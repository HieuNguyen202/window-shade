#include <Arduino.h>
#include <WiFi.h>
#define MESSAGE_LENGTH 5  //including one byte checksum
int count  = 0;
int status;
const char* ssid = "Mars";
const char* password = "3941HIEU";
IPAddress serverip(192,168,0,19);
WiFiClient client;
char dataIn[MESSAGE_LENGTH];
char dataOut[MESSAGE_LENGTH + 1];       //Nul char to terminate the string
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

void setup() {
  Serial.begin(9600);
  connectToWirelessRouter();
  if(client.connect(serverip,1234)){    //Connect to server
    Serial.println("Connected to server!");

  } else {
    Serial.println("Failed to connect to server!");
  }
}

void loop() {
  if(client.connected()){
    //Receive message
    while(client.available()>MESSAGE_LENGTH){
      client.readBytes(dataIn, MESSAGE_LENGTH);     //Read new message
      if(sum(dataIn, MESSAGE_LENGTH)==0){           //Checksum verified
        Serial.printf("New message received: [%d, %d, %d, %d]!", dataIn[0], dataIn[1], dataIn[2], dataIn[3], dataIn[4]);
      }
    }
    //Send message
    dataOut[0] = 2;
    dataOut[1] = 1;
    dataOut[2] = 2;
    dataOut[3] = 3;
    dataOut[MESSAGE_LENGTH] = 0;

    checksum(dataOut, MESSAGE_LENGTH);
    client.write(dataOut);
  } else{                                           //Connection failed
    Serial.printf("Wifi connection failed with status %d.\n", WiFi.status());
  }
  // Serial.println("Looping...");
  delay(100);
  // Serial.println(analogRead(ADC_0db)); //pin ADC7
  // delay(100);

  // Serial.println(count);
  // count++;
  // put your main code here, to run repeatedly:
}