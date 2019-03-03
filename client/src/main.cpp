#include <Arduino.h>
#include <WiFi.h>
int count  = 0;
const char* ssid = "Mars";
const char* password = "3941HIEU";
IPAddress server(192,168,0,19);
WiFiClient client;

void setupWiFi(){
  WiFi.begin(ssid, password);
  while(WiFi.status()!=WL_CONNECTED){
    delay(500);
    Serial.print("Connecting to ");
    Serial.println(ssid);
  }
  Serial.println("Connected to Mars!");
  Serial.print("Your local IP address is ");
  Serial.println(WiFi.localIP());

  if(client.connect(server,1234)){
    Serial.println("Connected to server!");
    client.println("GET /search?q=arduino HTTP/1.0");
    client.println();
  } else {
    Serial.println("Failed to connect to server!");
  }
}

void setup() {
  Serial.begin(9600);
}

void loop() {
  Serial.println(analogRead(ADC_0db)); //pin ADC7
  delay(100);

  // Serial.println(count);
  // count++;
  // put your main code here, to run repeatedly:
}