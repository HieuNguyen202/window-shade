#include <Arduino.h>
#include <WiFi.h>
#define MESSAGE_LENGTH 7  //including one byte checksum
#define MOTOR_ENABLE_PIN 27
#define MOTOR_STEP_PIN 26
#define MOTOR_DIR_PIN 25

#define LIGHT_SENSOR_PIN A0

#define ENCODER_B_PIN 19
#define ENCODER_A_PIN 18
#define ENCODER_X_PIN 17

#define PULSE_TO_STEP_FACTOR 2



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
volatile int currPos;
int maxPos, minPos;

int incPos(int diff);
int setPos(int pos);


void IRAM_ATTR pinAHandler(){
  portENTER_CRITICAL_ISR(&mux);
  if (digitalRead(ENCODER_B_PIN) == HIGH) {
    currPos++;
  } else {
    currPos--;
  }
  portEXIT_CRITICAL_ISR(&mux);
}

//TODO: deleted this, not nedded
//l: len is including the check sum byte
void checksum(char* raw, int l){
  unsigned char sum = 0, i;
  l--;
  for(i = 0; i < l; i++){
    sum += raw[i];
  }
  raw[i] = (256 - sum);
}

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

char sum(char* arr, char len){
  char _sum = 0;
  for(char i = 0; i < len; i++){               //Verify checksum
      _sum += arr[i];
  }
  return _sum;
}

void setUpCommunication(){
  connectToWirelessRouter();
  if(client.connect(serverip,1234)){    //Connect to server
    Serial.println("Connected to server!");
  } else {
    Serial.println("Failed to connect to server!");
  }
}
void setupMotor(){
  pinMode(MOTOR_DIR_PIN, OUTPUT);
  pinMode(MOTOR_STEP_PIN, OUTPUT);
  pinMode(MOTOR_ENABLE_PIN, OUTPUT);
  currPos = 0;
  minPos = -10000;
  maxPos = 10000;
}
void tcpReceive(){
  if(client.connected()){
    //Receive message
    int val;
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
                setPos(val);
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
int getLight(){
   return analogRead(A0); //pin ADC7
}
void motorTest(){
  digitalWrite(MOTOR_ENABLE_PIN, LOW); // Set Enable low
  digitalWrite(MOTOR_DIR_PIN, HIGH); // Set Dir high
  Serial.println("Loop 200 steps (1 rev)");
  for(int x = 0; x < 200; x++) // Loop 200 times
  {
    digitalWrite(MOTOR_STEP_PIN, HIGH); // Output high
    delay(1); // Wait
    digitalWrite(MOTOR_STEP_PIN,LOW); // Output low
    delay(1); // Wait
    }
  Serial.println("Pause");                                                     
  delay(1000); // pause one second
}
//Turn the motor with a diff of increment. If diff < 0, direction is reversed. This function is not bound protected.
void turn(int diff){
  digitalWrite(MOTOR_ENABLE_PIN, LOW); //Enable the motor
  digitalWrite(MOTOR_DIR_PIN, diff >= 0 ? LOW : HIGH); // Set direction
  int steps = abs(diff) / PULSE_TO_STEP_FACTOR;
  for(size_t _ = 0; _ < steps; _++)
  {
    digitalWrite(MOTOR_STEP_PIN, HIGH);
    delay(1);
    digitalWrite(MOTOR_STEP_PIN,LOW);
    delay(1);
  }
  digitalWrite(MOTOR_ENABLE_PIN, HIGH); //Disable the motor
}
//Turn the motor to a given pos. If the pos if out of bound, adjust to to at bound. Update the global currPos. Return the number of steps it actually turned.
int setPos(int pos){
  int diff;
  if(pos > maxPos)
    pos = maxPos;
  if (pos < minPos)
    pos = minPos;
  diff = pos - currPos;
  turn(diff);       //Turn the motor
  return diff;
}
//Change the pos incrementally. If diff is < 0, the change is in reverse direction. This fuction is mechanically safe (bound protected).
int incPos(int diff){
  int pos = currPos + diff;
  return setPos(pos);
}
void setPosTest(){
  currPos = 90;
  minPos = 0;
  maxPos = 180;
  int pos[] = {0, 90, -90, 90, 180, 90, 270, 90};
  Serial.println("Starting setPosTest()");
  for(size_t i = 0; i < 8; i++)
  {
      Serial.printf("Set pos: %d - diff: %d - currPos: %d\n", pos[i], setPos(pos[i]), currPos);
      delay(1000);
  }
  Serial.println("SetPosTest(0 finished");
}
void incPosTest(){
  currPos = 0;
  minPos = 0;
  maxPos = 180;
  int inc = 30, prevPos, realInc;
  Serial.println("Starting incPosTest()");
  for(size_t _ = 0; _ < maxPos; _+=inc)
  {
    prevPos = currPos;
    realInc = incPos(inc);
    Serial.printf("From pos: %d - increment: %d - to: %d\n", prevPos, realInc, currPos);
    delay(1000);
  }
    for(size_t _ = 0; _ < maxPos; _+=inc)
  {
    prevPos = currPos;
    realInc = incPos(-inc);
    Serial.printf("From pos: %d - increment: %d - to: %d\n", prevPos, realInc, currPos);
    delay(1000);
  }
  Serial.println("incPosTest(0 finished");
}
void setup() {
  Serial.begin(9600);
  setUpCommunication();
  setupMotor();
  pinMode(ENCODER_A_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENCODER_A_PIN), pinAHandler, FALLING);
  // incPosTest();
}

void loop() {
  tcpReceive();
  //New message structure [A single command char][an four digit number decoded in ASCII]
  // int val = getLight();
  // Serial.printf("g2%04d\n", val);
  // client.printf("g2%04d", val);
  // delay(100);
}