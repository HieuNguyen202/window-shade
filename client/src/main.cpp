#include <Arduino.h>
#include <Ticker.h>
#include <WiFi.h>
#include "A4988.h"
#define MESSAGE_LENGTH 6  // including one byte checksum

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

#define DEFAULT_MIN_POS -32767
#define DEFAULT_MAX_POS 32767

#define DEFAULT_NUM_CAL_INTERVALS 20

#define DEFAULT_LIGHT_UPDATE_PERIOD_SECOND 0.5

#define POS_TOLERANCE 5

#define PULSES_PER_STEP 1

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
  STATE_CAL_3,
  STATE_CAL_2,
  STATE_CAL_1,
  STATE_CAL_0,
  STATE_POS_PERSUIT,
  STATE_LIGHT_PERSUIT,
};

enum Commands {
  CMD_GET_STATE,
  CMD_GET_POS,
  CMD_GET_LIGHT,
  CMD_GET_POS_AND_LIGHT,
  CMD_GET_MAX_POS,
  CMD_GET_MAX_LIGHT,
  CMD_GET_MIN_POS,
  CMD_GET_MIN_LIGHT,
  CMD_GET_LOWER_BOUND_POS_AND_LIGHT,
  CMD_GET_UPPER_BOUND_POS_AND_LIGHT,
  CMD_SET_POS,
  CMD_SET_LIGHT,
  CMD_SET_MIN_POS,
  CMD_SET_MAX_POS,
  CMD_SET_STEP_INCREMENT,
  CMD_CALIBRATE,
  CMD_GET_LIVE_POS_AND_LIGHT,
  CMD_RESET,
  CMD_SCHEDULER,
  CMD_STOP
};

struct Measurement {
  int pos, light;
};

typedef struct Measurement mea_t;

struct Message {
  uint16_t commmand;
  int16_t value1;
  int16_t value2;
};

struct Message oMsg;
struct Message iMsg;

struct CalibrationProfile {
  int timeout;
  unsigned long timeoutMilis;
  int numInterval;
  int meaInterval;
  int midPos;
  mea_t mea;
  unsigned long startTime;
} cProfile;

A4988 stepper(MOTOR_STEPS, MOTOR_DIR_PIN, MOTOR_STEP_PIN, MOTOR_ENABLE_PIN,
              MOTOR_MS1, MOTOR_MS2, MOTOR_MS3);
bool doHoldPos = false;
bool isLive = false;
portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;
volatile long counter = 0;

int count = 0;
int status;

struct WifiCredentials{
  const char *ssid;
  const char *password;
};

#define NUMBER_OF_CREDENTIALS 3

struct WifiCredentials credentials[] = {{"HieuToGo", "3941HIEU"}, {"Mars", "3941HIEU"}, {"NETGEAR34", "newplum360"}};
int rIdx = 0;
const char *ssid = "Mars";
const char *password = "3941HIEU";
IPAddress serverip(192, 168, 0, 25);

int port = 2345;
WiFiClient client;
char dataIn[MESSAGE_LENGTH];
char dataOut[MESSAGE_LENGTH + 1];  // Nul char to terminate the string
volatile int currPos = 0;
int maxPos = DEFAULT_MAX_POS, minPos = DEFAULT_MIN_POS, targetPos = 0;

void incPos(int16_t diff);
int setPos(int pos);
void setTargetPos(int pos);
void updatePos();
void updateLight();
void writeToServer();

int light = 0;

State currState = STATE_IDLE;
Ticker tickerMeasureLight;
Ticker tickerLivePosAndLight;

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
  int numNetworks = WiFi.scanNetworks();
  for(size_t ii = 0; ii < NUMBER_OF_CREDENTIALS; ii++){
    Serial.printf("Trying %s\n", credentials[ii].ssid);
    for(size_t i = 0; i < numNetworks; i++)
    {
      Serial.println(WiFi.SSID(i));
      if(WiFi.SSID(i).equals(credentials[ii].ssid)){
        WiFi.begin(credentials[ii].ssid, credentials[ii].password);
        while (WiFi.status() != WL_CONNECTED) {
          Serial.printf("Connecting to %s\n", credentials[ii].ssid);
          delay(500);
        }
        Serial.printf("Connected to %s\n", credentials[ii]);
        Serial.printf("Your local IP address is ");
        Serial.println(WiFi.localIP());
        //Get server's ip address (always 25)
        Serial.printf("Your server IP address is ");
        serverip = WiFi.gatewayIP();
        serverip[3] = 25;
        Serial.println(serverip);
        return;
      }
    }
  }
}

int connectToServer(){
  if (client.connect(serverip, port)) {  // Connect to server
    Serial.println("Connected to server!");
    return 1;
  } else {
    Serial.println("Failed to connect to server!");
    return 0;
  }
}

// Connect to the server. Also connect the the wireless router before that.
void setUpCommunication() {
  connectToWirelessRouter();
  while(!(connectToServer())){
    delay(500);
    //Spin
  }
}

void sendCalibrationStatus(calibration_status s) {
  oMsg.commmand = CMD_CALIBRATE;
  oMsg.value1 = s;
  oMsg.value2 = 0;
  writeToServer();
}
void changeState(State s) {
  currState = s;
  oMsg.commmand = CMD_GET_STATE;
  oMsg.value1 = s;
  oMsg.value2 = 0;
  writeToServer();
}
void sendPosAndLight(mea_t mea) {
  oMsg.commmand = CMD_GET_POS_AND_LIGHT;
  oMsg.value1 = mea.pos;
  oMsg.value2 = mea.light;
  writeToServer();
}

void sendLivePosAndLight() {
  oMsg.commmand = CMD_GET_LIVE_POS_AND_LIGHT;
  oMsg.value1 = currPos;
  oMsg.value2 = light;
  writeToServer();
}

void sendPos(int pos) {
  oMsg.commmand = CMD_GET_POS_AND_LIGHT;
  oMsg.value1 = pos;
  oMsg.value2 = 0;
  writeToServer();
}
void send(uint16_t command, int16_t value1, int16_t value2) {
  oMsg.commmand = command;
  oMsg.value1 = value1;
  oMsg.value2 = value2;
  writeToServer();
}

// Calibration
// dataIn is used to get the message header to response
void calibrate() {
  if (currState == STATE_CAL_0) {  // setup
    Serial.printf(
        "tcpReceive: Begin calibration with timeout = %d seconds (STAGE0)\n",
        cProfile.timeout);
    sendCalibrationStatus(CAL_STATUS_IN_STAGE0);
    if (cProfile.timeout <= 0) {  // Bad input, calibaration is not started.
      Serial.printf(
          "tcpReceive: Calibration failed because timeout (%d seconds) <= 0\n",
          cProfile.timeout);
      sendCalibrationStatus(CAL_STATUS_TIMEOUT);
      changeState(STATE_IDLE);
      return;  // Abort
    }
    if (minPos == DEFAULT_MIN_POS ||
        maxPos == DEFAULT_MAX_POS) {  // Check if pos limits are set
      Serial.printf("tcpReceive: Calibration failed, limit not set.\n");
      sendCalibrationStatus(CAL_STATUS_LIMIT_NOT_SET);
      changeState(STATE_IDLE);
      return;  // Abort
    }
    cProfile.timeoutMilis = cProfile.timeout * 1000;
    cProfile.midPos = (minPos + maxPos) / 2;
    cProfile.meaInterval =
        (maxPos - minPos) /
        cProfile.numInterval;  // how often to take measuremnts

    // Increase light update frequency
    tickerMeasureLight.detach();
    tickerMeasureLight.attach(0.01, updateLight);  // 0.01 second period

    // Send a initial set of measurement
    cProfile.mea = {currPos, light};
    cProfile.startTime = millis();
    Serial.printf("tcpReceive: Calibration entering STATE_CAL_1.\n");
    changeState(STATE_CAL_1);
  } else {
    if (millis() - cProfile.startTime > cProfile.timeoutMilis) {
      // Timeout
      Serial.printf("tcpReceive: Calibration timed out.\n");
      sendCalibrationStatus(CAL_STATUS_TIMEOUT);
      changeState(STATE_IDLE);
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
        sendPosAndLight(cProfile.mea);
      }
      // Check and update the stages
      if (currState == STATE_CAL_1) {
        if (abs(currPos - minPos) >
            POS_TOLERANCE) {     // Not arrived at minPos yet
          setTargetPos(minPos);  // Go to minPos
        } else {                 // Arrived at minPos
          changeState(STATE_CAL_2);
          Serial.printf("tcpReceive: Calibration entering STATE_CAL_2.\n");
        }
      } else if (currState == STATE_CAL_2) {
        if (abs(currPos - maxPos) > POS_TOLERANCE)  // Not arrived at maxPos yet
        {
          setTargetPos(maxPos);  // Go to maxPos
        } else {                 // Arrived at maxPos
          changeState(STATE_CAL_3);
          Serial.printf("tcpReceive: Calibration entering STATE_CAL_3.\n");
        }
      } else if (currState == STATE_CAL_3) {
        if (abs(currPos - cProfile.midPos) >
            POS_TOLERANCE)  // Not arrived at minPos yet
        {
          setTargetPos(cProfile.midPos);  // Go to midPos
        } else                            // Arrived at midPos
        {
          changeState(STATE_IDLE);
          // Change light update period back to default values
          tickerMeasureLight.detach();
          tickerMeasureLight.attach(DEFAULT_LIGHT_UPDATE_PERIOD_SECOND,
                                    updateLight);
          Serial.printf("tcpReceive: Calibration finished.\n");
          sendCalibrationStatus(CAL_STATUS_SUCCESSFUL);
        }
      }
    }
  }
}

// Receive and execute a command from server
void tcpReceive() {
  while (!client.connected()) {  // Connection failed
      Serial.printf("Wifi connection failed with status %d.\n", WiFi.status());
      delay(500);
      connectToServer();
  }
  while (client.available() >= sizeof(iMsg)) {
    client.readBytes((byte *)&iMsg, sizeof(iMsg));  // Read new message
    switch (iMsg.commmand) {
      case CMD_GET_STATE:
        send(CMD_GET_STATE, currState, 0);
        break;
      case CMD_GET_POS:
        send(CMD_GET_POS, currPos, 0);
        break;
      case CMD_GET_LIGHT:
        send(CMD_GET_LIGHT, light, 0);
        break;
      case CMD_GET_POS_AND_LIGHT:
        send(CMD_GET_POS_AND_LIGHT, currPos, light);
        break;
      case CMD_GET_MAX_POS:
        send(CMD_GET_MAX_POS, maxPos, 0);
        break;
      case CMD_GET_MAX_LIGHT: //not implemented
        break;
      case CMD_GET_MIN_POS:
        send(CMD_GET_MIN_POS, minPos, 0);
        break;
      case CMD_GET_MIN_LIGHT: //not implemented
        break;
      case CMD_GET_LOWER_BOUND_POS_AND_LIGHT: //not implemented
        break;
      case CMD_GET_UPPER_BOUND_POS_AND_LIGHT: //not implemented
        break;
      case CMD_SET_POS:
        setTargetPos(iMsg.value1);
        changeState(STATE_POS_PERSUIT);
        Serial.printf("Target Pos: %d - Current Pos: %d\n", targetPos,
                      currPos);
        send(CMD_SET_POS, targetPos, 0);
        break;
      case CMD_SET_LIGHT: //not implemented
        break;
      case CMD_SET_MIN_POS:
        minPos = 0;
        currPos = 0;
        targetPos = 0;
        currState = STATE_POS_PERSUIT;
        send(CMD_SET_MIN_POS, minPos, 0);
        Serial.printf("setMinPos(%d)\n", minPos);
        break;
      case CMD_SET_MAX_POS:
        maxPos = currPos;
        send(CMD_SET_MAX_POS, maxPos, 0);
        Serial.printf("setMaxPos(%d)\n", maxPos);
        break;
      case CMD_SET_STEP_INCREMENT:  // or negative means decrement
        incPos(iMsg.value1);
        changeState(STATE_POS_PERSUIT);
        Serial.printf("CMD_SET_STEP_INCREMENT(%d)\n", currPos);
        send(CMD_SET_STEP_INCREMENT, targetPos, 0);
        break;
      case CMD_CALIBRATE:
        cProfile.timeout = iMsg.value1;
        cProfile.numInterval = iMsg.value2;
        changeState(STATE_CAL_0);
        break;
      case CMD_GET_LIVE_POS_AND_LIGHT:
        if(iMsg.value1){
          tickerMeasureLight.detach();
          tickerMeasureLight.attach((float)iMsg.value2/1000, updateLight);
          tickerLivePosAndLight.detach();
          tickerLivePosAndLight.attach((float)iMsg.value2/1000, sendLivePosAndLight);
        } else {
          tickerLivePosAndLight.detach();
          tickerMeasureLight.detach();
          tickerMeasureLight.attach(DEFAULT_LIGHT_UPDATE_PERIOD_SECOND, updateLight);
        }
        break;
      case CMD_RESET:
        maxPos = DEFAULT_MAX_POS;
        minPos = DEFAULT_MIN_POS;
        targetPos = 0;
        currPos = 0;
        send(CMD_GET_MIN_POS, minPos, 0);
        send(CMD_GET_MAX_POS, maxPos, 0);
        changeState(STATE_IDLE);
        break;
      case CMD_SCHEDULER: //not implemented
          break;
      case CMD_STOP:
          changeState(STATE_IDLE);
          break;
      default:
        Serial.printf("tcpReceive: Unknown command\n");
        break;
    }
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
      if (stepper.getStepsRemaining() < abs(diff) || stepper.getDirection() * diff < 0) { //if opposite direction or remaining step hasn't been set
        stepper.startMove(diff * MICROSTEPS * PULSES_PER_STEP);  // in microsteps
      }
    } else {
      Serial.printf("In CMD_SET_STEP_INCREMENT(%d)\n", currPos);
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
void incPos(int16_t diff) { setTargetPos(currPos + diff); }

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
  stepper.begin(120, MICROSTEPS);
  stepper.setEnableActiveState(LOW);
}

// Write the content of message m to server
void writeToServer() { client.write((byte *)&oMsg, sizeof(oMsg)); }

void loop() {
  tcpReceive();
  if (currState == STATE_IDLE) {
    doHoldPos = false;
    // Do something
  } else if (currState >= STATE_CAL_3 && currState <= STATE_CAL_0) {
    calibrate();
  } else if (currState == STATE_POS_PERSUIT) {
    if (abs(targetPos - currPos) < POS_TOLERANCE)
      changeState(STATE_IDLE);
    else
      doHoldPos = true;
  } else {
    printf("Unkown state %d\n", currState);
  }
  updatePos();
}