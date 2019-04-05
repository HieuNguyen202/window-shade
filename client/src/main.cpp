#include <Arduino.h>
#include <WiFi.h>
#define MESSAGE_LENGTH 6  //including one byte checksum

#define STEP_PIN 26
#define DIR_PIN 27
#define ENABLE_PIN 14
#define LIGHT_SENSOR_PIN A0

int count  = 0;
int status;
const char* ssid = "Mars";
const char* password = "3941HIEU";
IPAddress serverip(192,168,0,25);
WiFiClient client;
char dataIn[MESSAGE_LENGTH];
char dataOut[MESSAGE_LENGTH + 1];       //Nul char to terminate the string

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
  pinMode(DIR_PIN, OUTPUT);
  pinMode(STEP_PIN, OUTPUT);
  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN,LOW); // Set Enable low
}

void tcpReceive(){
  if(client.connected()){
    //Receive message
    while(client.available()>MESSAGE_LENGTH){
      client.readBytes(dataIn, MESSAGE_LENGTH);     //Read new message
        Serial.printf("New message received: %s\n", dataIn);
        client.print(dataIn);
    }
  } else{                                           //Connection failed
    Serial.printf("Wifi connection failed with status %d.\n", WiFi.status());
  }
}

int getLight(){
   return analogRead(A0); //pin ADC7
}

void motorTest(){
  digitalWrite(ENABLE_PIN, LOW); // Set Enable low
  digitalWrite(DIR_PIN, HIGH); // Set Dir high
  Serial.println("Loop 200 steps (1 rev)");
  for(int x = 0; x < 200; x++) // Loop 200 times
  {
    digitalWrite(STEP_PIN, HIGH); // Output high
    delay(1); // Wait
    digitalWrite(STEP_PIN,LOW); // Output low
    delay(1); // Wait
    }
  Serial.println("Pause");                                                     
  delay(1000); // pause one second
}

void setup() {
  Serial.begin(9600);
  setUpCommunication();
}
void loop() {
  //tcpReceive();
  //New message structure [A single command char][an four digit number decoded in ASCII]
  int val = getLight();
  Serial.printf("g2%04d\n", val);
  client.printf("g2%04d", val);
  delay(1);
}