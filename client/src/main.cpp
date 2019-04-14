#include <Arduino.h>
#include <WiFi.h>
#include <Ticker.h>
#include "A4988.h"
#define MESSAGE_LENGTH 7  //including one byte checksum

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

A4988 stepper(MOTOR_STEPS, MOTOR_DIR_PIN, MOTOR_STEP_PIN, MOTOR_ENABLE_PIN, MOTOR_MS1, MOTOR_MS2, MOTOR_MS3);

portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;
volatile long counter = 0;

int count  = 0;
int status;
const char* ssid = "Mars";
const char* password = "3941HIEU";
IPAddress serverip(192,168,0,25);
WiFiClient client;
char dataIn[MESSAGE_LENGTH];
char dataOut[MESSAGE_LENGTH + 1];       //Nul char to terminate the string
volatile int currPos = 0;
int maxPos = 10000, minPos = -10000, targetPos = 0;

void incPos(int diff);
int setPos(int pos);
void setTargetPos(int pos);

int light = 0;

Ticker tickerMeasureLight;

//Handler for encoder counts
void IRAM_ATTR pinAHandler(){
  portENTER_CRITICAL_ISR(&mux);
  if (digitalRead(ENCODER_B_PIN) == LOW) {
    currPos++;
  } else {
    currPos--;
  }
  portEXIT_CRITICAL_ISR(&mux);
}

//Connect to the wireless router
void connectToWirelessRouter(){
    WiFi.begin(ssid, password);
  while(WiFi.status()!=WL_CONNECTED){
    delay(500);
    Serial.print("Connecting to ");
    Serial.println(ssid);
  }
  Serial.println("Connected to Mars!");
  Serial.print("Your local IP address is ");
  Serial.println(WiFi.localIP());
}
//Connect to the server. Also connect the the wireless router before that.
void setUpCommunication(){
  connectToWirelessRouter();
  if(client.connect(serverip,1234)){    //Connect to server
    Serial.println("Connected to server!");
  } else {
    Serial.println("Failed to connect to server!");
  }
}
//Receive and execute a command from server
void tcpReceive(){
  if(client.connected()){
    //Receive message
    int val, ret;
    while(client.available()>=MESSAGE_LENGTH){
      client.readBytes(dataIn, MESSAGE_LENGTH);     //Read new message
        switch (dataIn[0])
        {
          case 'g':
            switch (dataIn[1]){
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
            switch (dataIn[1]){
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
          case 's':
            val = atoi(&dataIn[2]);
            switch (dataIn[1])
            {
              case '0':
                Serial.printf("Need to implement %s\n", dataIn);
                break;
              case '1': //setPos(pos)
                setTargetPos(val);
                client.printf("%c%c%05d", dataIn[0], dataIn[1], currPos); //response with the same command header and the actual steps.
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
              case '5': //setMinPos()
                minPos = 0;
                currPos = 0;
                targetPos = 0;
                client.printf("%c%c%05d", dataIn[0], dataIn[1], minPos); //response with the same command header and the actual steps.
                Serial.printf("setMinPos(%d)\n", minPos);
                break;
              case '6': //setMaxPos()
                maxPos = currPos;
                client.printf("%c%c%05d", dataIn[0], dataIn[1], maxPos); //response with the same command header and the actual steps.
                Serial.printf("setMaxPos(%d)\n", maxPos);
                break;
              case '7': //step(steps)
                Serial.printf("Counter before: %d\n", currPos);
                incPos(val);
                client.printf("%c%c%05d", dataIn[0], dataIn[1], currPos); //response with the same command header and the actual steps.
                Serial.printf("steps(%d)\n", val);
                Serial.printf("Counter after: %d\n", currPos);
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
  } else{                                           //Connection failed
    Serial.printf("Wifi connection failed with status %d.\n", WiFi.status());
  }
}

//Update the light value
void updateLight(){
   light = analogRead(LIGHT_SENSOR_PIN);
}

//Go target pos if the currPos is not target pos.
void updatePos(){
  int diff = targetPos - currPos;
  unsigned wait_time = stepper.nextAction();                //Ignore the return value because the encoder can track the position
  if(abs(diff) > 10){
    stepper.enable();
    stepper.startMove(diff * MOTOR_STEPS * MICROSTEPS);     // in microsteps
  } else{
    stepper.stop();
    stepper.disable();
  }
}
//Set the target position of the shade. If pos is out of bound, target pos will be the respective bounds.
void setTargetPos(int pos){
  if(pos > maxPos)
    targetPos = maxPos;
  else if (pos < minPos)
    targetPos = minPos;
  else{
    targetPos = pos;
  }
}

//Change the pos incrementally. If diff is < 0, the change is in reverse direction. This fuction is mechanically safe (bound protected).
void incPos(int diff){
  setTargetPos(currPos + diff);
}

void setup() {
  Serial.begin(9600);
  //Setup wireless communication
  setUpCommunication();

  //Setup encoder
  pinMode(ENCODER_A_PIN, INPUT_PULLUP);
  pinMode(ENCODER_B_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENCODER_A_PIN), pinAHandler, FALLING);

  //Setup light sensor
  tickerMeasureLight.attach(0.5, updateLight);

  //Setup stepper
  stepper.begin(30, MICROSTEPS);
  stepper.setEnableActiveState(LOW);
}
void loop() {
  tcpReceive();
  updatePos();
}


