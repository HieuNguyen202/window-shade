#include <Arduino.h>
#include <Ticker.h>
#include <WiFi.h>
#include "A4988.h"
#define MESSAGE_LENGTH 7  // including one byte checksum

#define MOTOR_STEPS 200
#define MOTOR_ENABLE_PIN 27
#define MOTOR_STEP_PIN 26
#define MOTOR_DIR_PIN 25
#define MOTOR_MS1 14
#define MOTOR_MS2 12
#define MOTOR_MS3 13

#define LIGHT_SENSOR_PIN A0

#define ENCODER_B_PIN 19
#define ENCODER_A_PIN 18
#define ENCODER_X_PIN 17

#define PULSE_TO_STEP_FACTOR 2
#define MICROSTEPS 1

#define DEFAULT_MIN_POS -100000
#define DEFAULT_MAX_POS 100000

#define DEFAULT_NUM_CAL_INTERVALS 20

#define DEFAULT_LIGHT_UPDATE_PERIOD_SECOND 0.5

#define POS_TOLERANCE 5

enum calibration_status {
  CAL_STATUS_SUCCESSFUL,
  CAL_STATUS_TIMEOUT,
  CAL_STATUS_LIMIT_NOT_SET,
  CAL_STATUS_IN_STAGE0,
  CAL_STATUS_IN_STAGE1,
  CAL_STATUS_IN_STAGE2,
  CAL_STATUS_IN_STAGE3,
};

enum State {
  STATE_IDLE,
  STATE_CAL_0,
  STATE_CAL_1,
  STATE_CAL_2,
  STATE_CAL_3,
  STATE_POS_PERSUIT,
  STATE_LIGHT_PERSUIT,
};

enum calibration_stage { STAGE0, STAGE1, STAGE2, STAGE3 };

struct Measurement {
  int pos, light;
};
typedef struct Measurement mea_t;

struct CalibrationProfile {
  int timeout;
  unsigned long timeoutMilis;
  char dataIn[2];
  int meaInterval;
  int midPos;
  mea_t mea;
  unsigned long startTime;
} cProfile;

A4988 stepper(MOTOR_STEPS, MOTOR_DIR_PIN, MOTOR_STEP_PIN, MOTOR_ENABLE_PIN,
              MOTOR_MS1, MOTOR_MS2, MOTOR_MS3);
bool doHoldPos = false;
portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;
volatile long counter = 0;

int count = 0;
int status;
const char *ssid = "Mars";
const char *password = "3941HIEU";
IPAddress serverip(192, 168, 0, 25);
WiFiClient client;
char dataIn[MESSAGE_LENGTH];
char dataOut[MESSAGE_LENGTH + 1];  // Nul char to terminate the string
volatile int currPos = 0;
int maxPos = DEFAULT_MAX_POS, minPos = DEFAULT_MIN_POS, targetPos = 0;

void incPos(int diff);
int setPos(int pos);
void setTargetPos(int pos);
void updatePos();
void updateLight();

int light = 0;

State currState = STATE_IDLE;
Ticker tickerMeasureLight;

// Handler for encoder counts
void IRAM_ATTR pinAHandler() {
  portENTER_CRITICAL_ISR(&mux);
  if (digitalRead(ENCODER_B_PIN) == LOW) {
    currPos++;
  } else {
    currPos--;
  }
  portEXIT_CRITICAL_ISR(&mux);
}

// Connect to the wireless router
void connectToWirelessRouter() {
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print("Connecting to ");
    Serial.println(ssid);
  }
  Serial.println("Connected to Mars!");
  Serial.print("Your local IP address is ");
  Serial.println(WiFi.localIP());
}
// Connect to the server. Also connect the the wireless router before that.
void setUpCommunication() {
  connectToWirelessRouter();
  if (client.connect(serverip, 1234)) {  // Connect to server
    Serial.println("Connected to server!");
  } else {
    Serial.println("Failed to connect to server!");
  }
}

// Calibration
// dataIn is used to get the message header to response
void calibrate() {
  if (currState == STATE_CAL_0) {  // setup
    Serial.printf(
        "tcpReceive: Begin calibration with timeout = %d seconds (STAGE0)\n",
        cProfile.timeout);
    client.printf("%c%c%05d", cProfile.dataIn[0], cProfile.dataIn[1],
                  CAL_STATUS_IN_STAGE0);
    if (cProfile.timeout <= 0) {  // Bad input, calibaration is not started.
      Serial.printf(
          "tcpReceive: Calibration failed because timeout (%d seconds) <= 0\n",
          cProfile.timeout);
      client.printf("%c%c%05d", cProfile.dataIn[0], cProfile.dataIn[1],
                    CAL_STATUS_TIMEOUT);  // timout input <= 0
      currState = STATE_IDLE;
      return;  // Abort
    }
    if (minPos == DEFAULT_MIN_POS ||
        maxPos == DEFAULT_MAX_POS) {  // Check if pos limits are set
      Serial.printf("tcpReceive: Calibration failed, limit not set.\n");
      client.printf("%c%c%05d", cProfile.dataIn[0], cProfile.dataIn[1],
                    CAL_STATUS_LIMIT_NOT_SET);
      currState = STATE_IDLE;
      return;  // Abort
    }
    cProfile.timeoutMilis = cProfile.timeout * 1000;
    cProfile.midPos = (minPos + maxPos) / 2;
    cProfile.meaInterval =
        (maxPos - minPos) /
        DEFAULT_NUM_CAL_INTERVALS;  // how often to take measuremnts

    // Increase light update frequency
    tickerMeasureLight.detach();
    tickerMeasureLight.attach(0.01, updateLight);  // 0.01 second period

    // Send a initial set of measurement
    cProfile.mea = {currPos, light};

    cProfile.startTime = millis();
    currState = STATE_CAL_1;
    Serial.printf("tcpReceive: Calibration entering STATE_CAL_1.\n");
    client.printf("%c%c%05d", 't', '0', STATE_CAL_1);
  } else {
    if (millis() - cProfile.startTime > cProfile.timeoutMilis) {
      // Timeout
      Serial.printf("tcpReceive: Calibration timed out.\n");
      client.printf("%c%c%05d", dataIn[0], dataIn[1],
                    CAL_STATUS_TIMEOUT);  // timed out
      currState = STATE_IDLE;
    } else {
      // STAGE0: setup
      // STAGE0: Calibration started, need to go to minPos
      // STAGE1: Arrived at minPos, need to go to maxPos
      // STAGE2: Arrived at maxPos, need to go to midPos
      // STAGE3: Calibration finished.

      // send measurements back to server
      if (abs(currPos - cProfile.mea.pos) >
          cProfile.meaInterval)  // The shade has gone far enough (>meaInterval)
      {
        // Send a new set of measuremnts
        cProfile.mea = {currPos, light};
        client.printf("%c%c%05d", dataIn[0], '1',
                      cProfile.mea.pos);  // send pos
        client.printf("%c%c%05d", dataIn[0], '2',
                      cProfile.mea.light);  // send light
      }

      // Check and update the stages
      if (currState == STATE_CAL_1) {
        if (abs(currPos - minPos) >
            POS_TOLERANCE) {     // Not arrived at minPos yet
          setTargetPos(minPos);  // Go to minPos
        } else {                 // Arrived at minPos
          currState = STATE_CAL_2;
          Serial.printf("tcpReceive: Calibration entering STATE_CAL_2.\n");
          client.printf("%c%c%05d", 't', '0', STATE_CAL_2);
        }
      } else if (currState == STATE_CAL_2) {
        if (abs(currPos - maxPos) > POS_TOLERANCE)  // Not arrived at maxPos yet
        {
          setTargetPos(maxPos);  // Go to maxPos
        } else {                 // Arrived at maxPos
          currState = STATE_CAL_3;
          Serial.printf("tcpReceive: Calibration entering STATE_CAL_3.\n");
          client.printf("%c%c%05d", 't', '0', STATE_CAL_3);
        }
      } else if (currState == STATE_CAL_3) {
        if (abs(currPos - cProfile.midPos) >
            POS_TOLERANCE)  // Not arrived at minPos yet
        {
          setTargetPos(cProfile.midPos);  // Go to midPos
        } else                            // Arrived at midPos
        {
          currState = STATE_IDLE;
          // Change light update period back to default values
          tickerMeasureLight.detach();
          tickerMeasureLight.attach(DEFAULT_LIGHT_UPDATE_PERIOD_SECOND,
                                    updateLight);
          Serial.printf("tcpReceive: Calibration entering STATE_CAL_3.\n");
          client.printf("%c%c%05d", 't', '0', STATE_IDLE);

          Serial.printf("tcpReceive: Calibration finished.\n");
          client.printf("%c%c%05d", dataIn[0], dataIn[1],
                        CAL_STATUS_SUCCESSFUL);  // succeeded
        }
      }
    }
  }
}

// Receive and execute a command from server
void tcpReceive() {
  if (client.connected()) {
    // Receive message
    int val, ret;
    while (client.available() >= MESSAGE_LENGTH) {
      client.readBytes(dataIn, MESSAGE_LENGTH);  // Read new message
      switch (dataIn[0]) {
        case 'g':
          switch (dataIn[1]) {
            case '0':
              Serial.printf("Need to implement %s\n", dataIn);
              break;
            case '1':
              Serial.printf("Need to implement %s\n", dataIn);
              break;
            case '2':
              Serial.printf("Need to implement %s\n", dataIn);
              break;
            case '3':
              Serial.printf("Need to implement %s\n", dataIn);
              break;
            case '4':
              Serial.printf("Need to implement %s\n", dataIn);
              break;
            case '5':
              Serial.printf("Need to implement %s\n", dataIn);
              break;
            case '6':
              Serial.printf("Need to implement %s\n", dataIn);
              break;
            case '7':
              Serial.printf("Need to implement %s\n", dataIn);
              break;
            case '8':
              Serial.printf("Need to implement %s\n", dataIn);
              break;
            default:
              Serial.printf("tcpReceive: Unknown command %s", dataIn);
              break;
          }
          break;
        case 'c':
          val = atoi(&dataIn[2]);
          switch (dataIn[1]) {
            case '0':  // calibrate(int timeout)
              cProfile.timeout = val;
              cProfile.dataIn[0] = dataIn[0];
              cProfile.dataIn[1] = dataIn[1];
              currState = STATE_CAL_0;
              break;
            case '1':
              Serial.printf("Need to implement %s\n", dataIn);
              break;
            case '2':
              Serial.printf("Need to implement %s\n", dataIn);
              break;
            case '3':
              Serial.printf("Need to implement %s\n", dataIn);
              break;
            case '4':
              Serial.printf("Need to implement %s\n", dataIn);
              break;
            case '5':
              Serial.printf("Need to implement %s\n", dataIn);
              break;
            case '6':
              Serial.printf("Need to implement %s\n", dataIn);
              break;
            case '7':
              Serial.printf("Need to implement %s\n", dataIn);
              break;
            case '8':
              Serial.printf("Need to implement %s\n", dataIn);
              break;
            default:
              Serial.printf("tcpReceive: Unknown command %s", dataIn);
              break;
          }
          break;
        case 's':
          val = atoi(&dataIn[2]);
          switch (dataIn[1]) {
            case '0':
              Serial.printf("Need to implement %s\n", dataIn);
              break;
            case '1':  // setPos(pos)
              setTargetPos(val);
              currState = STATE_POS_PERSUIT;
              Serial.printf("Target Pos: %d - Current Pos: %d\n", targetPos,
                            currPos);
              client.printf("%c%c%05d", dataIn[0], dataIn[1],
                            currPos);  // response with the same command header
                                       // and the actual steps.
              break;
            case '2':
              Serial.printf("Need to implement %s\n", dataIn);
              break;
            case '3':
              Serial.printf("Need to implement %s\n", dataIn);
              break;
            case '4':
              Serial.printf("Need to implement %s\n", dataIn);
              break;
            case '5':  // setMinPos()
              minPos = 0;
              currPos = 0;
              targetPos = 0;
              currState = STATE_POS_PERSUIT;
              client.printf("%c%c%05d", dataIn[0], dataIn[1],
                            minPos);  // response with the same command header
                                      // and the actual steps.
              Serial.printf("setMinPos(%d)\n", minPos);
              break;
            case '6':  // setMaxPos()
              maxPos = currPos;
              client.printf("%c%c%05d", dataIn[0], dataIn[1],
                            maxPos);  // response with the same command header
                                      // and the actual steps.
              Serial.printf("setMaxPos(%d)\n", maxPos);
              break;
            case '7':  // step(steps)
              // Serial.printf("Counter before: %d\n", currPos);
              incPos(val);
              currState = STATE_POS_PERSUIT;
              client.printf("%c%c%05d", dataIn[0], dataIn[1],
                            currPos);  // response with the same command header
                                       // and the actual steps.
              // Serial.printf("steps(%d)\n", val);
              // Serial.printf("Counter after: %d\n", currPos);
              break;
            case '8':
              Serial.printf("Need to implement %s\n", dataIn);
              break;
            default:
              Serial.printf("tcpReceive: Unknown command %s", dataIn);
              break;
          }
          break;
        default:
          Serial.printf("tcpReceive: Unknown command %s", dataIn);
          break;
      }
    }
  } else {  // Connection failed
    Serial.printf("Wifi connection failed with status %d.\n", WiFi.status());
  }
}

// Update the light value
void updateLight() { light = analogRead(LIGHT_SENSOR_PIN); }

// Go target pos if the currPos is not target pos.
void updatePos() {
  int diff = targetPos - currPos;
  unsigned wait_time =
      stepper.nextAction();  // Ignore the return value because the encoder can
                             // track the position
  if (doHoldPos) {
    if (abs(diff) > POS_TOLERANCE) {
      stepper.enable();
      if (stepper.getStepsRemaining() < abs(diff)) {
        stepper.startMove(diff * MOTOR_STEPS * MICROSTEPS);  // in microsteps
      }
    } else {
      stepper.stop();  // stop the previous move
      doHoldPos = false;
    }
  } else {
    stepper.stop();
    stepper.disable();
  }
}
// Set the target position of the shade. If pos is out of bound, target pos will
// be the respective bounds.
void setTargetPos(int pos) {
  if (pos > maxPos)
    targetPos = maxPos;
  else if (pos < minPos)
    targetPos = minPos;
  else
    targetPos = pos;
  doHoldPos = true;
}

// Change the pos incrementally. If diff is < 0, the change is in reverse
// direction. This fuction is mechanically safe (bound protected).
void incPos(int diff) { setTargetPos(currPos + diff); }

void setup() {
  Serial.begin(9600);
  // Setup wireless communication
  setUpCommunication();

  // Setup encoder
  pinMode(ENCODER_A_PIN, INPUT_PULLUP);
  pinMode(ENCODER_B_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENCODER_A_PIN), pinAHandler, FALLING);

  // Setup light sensor
  tickerMeasureLight.attach(DEFAULT_LIGHT_UPDATE_PERIOD_SECOND, updateLight);

  // Setup stepper
  stepper.begin(60, MICROSTEPS);
  stepper.setEnableActiveState(LOW);
}

void loop() {
  tcpReceive();

  if (currState == STATE_IDLE) {
    doHoldPos = false;
    // Do something
  } else if (currState >= STATE_CAL_0 && currState <= STATE_CAL_3) {
    calibrate();
  } else if (currState == STATE_POS_PERSUIT) {
    if (abs(targetPos - currPos) < POS_TOLERANCE)
      currState = STATE_IDLE;
    else
      doHoldPos = true;
  } else {
    printf("Unkown state %d\n", currState);
  }
  updatePos();
}
