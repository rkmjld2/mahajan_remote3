#include <ESP8266WiFi.h>
#include <PubSubClient.h>

const char* ssid     = "Airtel_56";
const char* password = "Raviuma5658";

const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;

const char* topic_status = "ravi2025/home/status";

const char* topic_d0 = "ravi2025/home/d0/set";
const char* topic_d1 = "ravi2025/home/d1/set";
const char* topic_d2 = "ravi2025/home/d2/set";
const char* topic_d3 = "ravi2025/home/d3/set";
const char* topic_d4 = "ravi2025/home/d4/set";
const char* topic_d5 = "ravi2025/home/d5/set";
const char* topic_d6 = "ravi2025/home/d6/set";
const char* topic_d7 = "ravi2025/home/d7/set";

#define PIN_D0 D0
#define PIN_D1 D1
#define PIN_D2 D2
#define PIN_D3 D3
#define PIN_D4 D4
#define PIN_D5 D5
#define PIN_D6 D6
#define PIN_D7 D7

WiFiClient espClient;
PubSubClient client(espClient);

bool state[8] = {0,0,0,0,0,0,0,0};

void publishStatus() {

  char msg[120];

  sprintf(msg,
  "D0=%s D1=%s D2=%s D3=%s D4=%s D5=%s D6=%s D7=%s",
  state[0]?"ON":"OFF",
  state[1]?"ON":"OFF",
  state[2]?"ON":"OFF",
  state[3]?"ON":"OFF",
  state[4]?"ON":"OFF",
  state[5]?"ON":"OFF",
  state[6]?"ON":"OFF",
  state[7]?"ON":"OFF"
  );

  client.publish(topic_status,msg,true);
}

void setPin(int index,bool value){

  int pins[8]={PIN_D0,PIN_D1,PIN_D2,PIN_D3,PIN_D4,PIN_D5,PIN_D6,PIN_D7};

  state[index]=value;

  digitalWrite(pins[index],value?HIGH:LOW);

  publishStatus();
}

void callback(char* topic, byte* payload, unsigned int length) {

  String msg;

  for(int i=0;i<length;i++)
    msg+=(char)payload[i];

  bool val=false;

  if(msg=="ON") val=true;
  else if(msg=="OFF") val=false;
  else return;

  String t=String(topic);

  if(t==topic_d0) setPin(0,val);
  if(t==topic_d1) setPin(1,val);
  if(t==topic_d2) setPin(2,val);
  if(t==topic_d3) setPin(3,val);
  if(t==topic_d4) setPin(4,val);
  if(t==topic_d5) setPin(5,val);
  if(t==topic_d6) setPin(6,val);
  if(t==topic_d7) setPin(7,val);
}

void reconnect(){

  while(!client.connected()){

    String clientId="ESP8266-Ravi-"+String(random(0xffff),HEX);

    if(client.connect(clientId.c_str())){

      client.subscribe(topic_d0);
      client.subscribe(topic_d1);
      client.subscribe(topic_d2);
      client.subscribe(topic_d3);
      client.subscribe(topic_d4);
      client.subscribe(topic_d5);
      client.subscribe(topic_d6);
      client.subscribe(topic_d7);

      client.publish(topic_status,"ESP connected",true);

      publishStatus();
    }
    else
    {
      delay(5000);
    }
  }
}

void setup(){

  Serial.begin(115200);

  pinMode(PIN_D0,OUTPUT);
  pinMode(PIN_D1,OUTPUT);
  pinMode(PIN_D2,OUTPUT);
  pinMode(PIN_D3,OUTPUT);
  pinMode(PIN_D4,OUTPUT);
  pinMode(PIN_D5,OUTPUT);
  pinMode(PIN_D6,OUTPUT);
  pinMode(PIN_D7,OUTPUT);

  WiFi.begin(ssid,password);

  while(WiFi.status()!=WL_CONNECTED){
    delay(500);
  }

  client.setServer(mqtt_server,mqtt_port);
  client.setCallback(callback);
}

void loop(){

  if(!client.connected())
    reconnect();

  client.loop();
}
