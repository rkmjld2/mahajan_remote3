#include <ESP8266WiFi.h>
#include <PubSubClient.h>

const char* ssid = "Airtel_56";
const char* password = "Raviuma5658";

const char* mqtt_server = "broker.hivemq.com";
const int   mqtt_port   = 1883;

const char* topic_d1     = "ravi2025/home/d1/set";
const char* topic_d2     = "ravi2025/home/d2/set";
const char* topic_status = "ravi2025/home/status";

WiFiClient espClient;
PubSubClient client(espClient);

#define D1_PIN 5
#define D2_PIN 4

unsigned long lastReconnectAttempt = 0;

void setup() {
  Serial.begin(115200);
  delay(100);
  Serial.println("\n\n=== ESP8266 MQTT Debug Start ===");

  pinMode(D1_PIN, OUTPUT);
  pinMode(D2_PIN, OUTPUT);
  digitalWrite(D1_PIN, LOW);
  digitalWrite(D2_PIN, LOW);

  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void setup_wifi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Signal strength (RSSI): ");
    Serial.println(WiFi.RSSI());
  } else {
    Serial.println("\nWiFi connection FAILED after 15 seconds!");
  }
}

void reconnect() {
  if (millis() - lastReconnectAttempt < 5000) {
    return;  # Don't spam reconnect
  }
  lastReconnectAttempt = millis();

  Serial.print("Attempting MQTT connection to ");
  Serial.print(mqtt_server);
  Serial.print(":");
  Serial.print(mqtt_port);
  Serial.print(" ... ");

  String clientId = "ESP8266Client-" + String(random(0xffff), HEX);
  if (client.connect(clientId.c_str())) {
    Serial.println("CONNECTED!");
    client.subscribe(topic_d1);
    client.subscribe(topic_d2);
    client.publish(topic_status, "ESP online - MQTT connected");
    Serial.println("Published: ESP online - MQTT connected");
  } else {
    Serial.print("FAILED, rc=");
    Serial.print(client.state());
    Serial.println(" → will retry in 5 seconds");
    // Common rc values:
    // -2 = network error
    // -4 = timeout
    // 5 = unauthorized (not for public broker)
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  message.trim();

  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  Serial.println(message);

  String t = String(topic);

  if (t == topic_d1) {
    if (message == "ON") {
      digitalWrite(D1_PIN, HIGH);
      client.publish(topic_status, "D1 ON");
      Serial.println("D1 turned ON");
    } else if (message == "OFF") {
      digitalWrite(D1_PIN, LOW);
      client.publish(topic_status, "D1 OFF");
      Serial.println("D1 turned OFF");
    }
  }
  else if (t == topic_d2) {
    if (message == "ON") {
      digitalWrite(D2_PIN, HIGH);
      client.publish(topic_status, "D2 ON");
      Serial.println("D2 turned ON");
    } else if (message == "OFF") {
      digitalWrite(D2_PIN, LOW);
      client.publish(topic_status, "D2 OFF");
      Serial.println("D2 turned OFF");
    }
  }
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}

