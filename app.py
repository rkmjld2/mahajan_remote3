#include <ESP8266WiFi.h>
#include <PubSubClient.h>

const char* ssid = "Airtel_56";
const char* password = "Raviuma5658";

const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;

// VERY IMPORTANT: These MUST match EXACTLY with app.py (copy-paste from app.py)
const char* topic_d1     = "ravi2025/home/d1/set";
const char* topic_d2     = "ravi2025/home/d2/set";
const char* topic_status = "ravi2025/home/status";

WiFiClient espClient;
PubSubClient client(espClient);

#define D1_PIN 5
#define D2_PIN 4

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("\n\n=== ESP8266 MQTT DEBUG START ===");

  pinMode(D1_PIN, OUTPUT);
  pinMode(D2_PIN, OUTPUT);
  digitalWrite(D1_PIN, LOW);
  digitalWrite(D2_PIN, LOW);

  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void setup_wifi() {
  Serial.print("Connecting to WiFi ");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  if (millis() - lastReconnectAttempt < 5000) return;
  lastReconnectAttempt = millis();

  Serial.print("MQTT reconnect attempt...");
  String clientId = "ESPClient-" + String(random(0xffff), HEX);
  if (client.connect(clientId.c_str())) {
    Serial.println("CONNECTED!");
    Serial.print("Subscribed to: ");
    Serial.println(topic_d1);
    Serial.print("Subscribed to: ");
    Serial.println(topic_d2);
    client.subscribe(topic_d1);
    client.subscribe(topic_d2);
    client.publish(topic_status, "ESP online - ready");
    Serial.println("Published: ESP online - ready");
  } else {
    Serial.print("FAILED rc=");
    Serial.println(client.state());
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Received on topic: ");
  Serial.println(topic);

  String message = "";
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  message.trim();
  Serial.print("Payload: '");
  Serial.print(message);
  Serial.println("'");

  String t = String(topic);

  if (t == topic_d1) {
    Serial.println("Topic matched D1");
    if (message == "ON") {
      digitalWrite(D1_PIN, HIGH);
      Serial.println("D1 → HIGH");
      bool pub_ok = client.publish(topic_status, "D1 ON");
      Serial.print("Published D1 ON → ");
      Serial.println(pub_ok ? "SUCCESS" : "FAILED");
    } else if (message == "OFF") {
      digitalWrite(D1_PIN, LOW);
      Serial.println("D1 → LOW");
      bool pub_ok = client.publish(topic_status, "D1 OFF");
      Serial.print("Published D1 OFF → ");
      Serial.println(pub_ok ? "SUCCESS" : "FAILED");
    }
  }
  else if (t == topic_d2) {
    Serial.println("Topic matched D2");
    if (message == "ON") {
      digitalWrite(D2_PIN, HIGH);
      Serial.println("D2 → HIGH");
      bool pub_ok = client.publish(topic_status, "D2 ON");
      Serial.print("Published D2 ON → ");
      Serial.println(pub_ok ? "SUCCESS" : "FAILED");
    } else if (message == "OFF") {
      digitalWrite(D2_PIN, LOW);
      Serial.println("D2 → LOW");
      bool pub_ok = client.publish(topic_status, "D2 OFF");
      Serial.print("Published D2 OFF → ");
      Serial.println(pub_ok ? "SUCCESS" : "FAILED");
    }
  }
  else {
    Serial.println("Topic did NOT match D1 or D2");
  }
}

unsigned long lastReconnectAttempt = 0;

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Periodic status publish every 30 seconds (for testing)
  static unsigned long lastPub = 0;
  if (millis() - lastPub > 30000) {
    lastPub = millis();
    String pins = "D1:" + String(digitalRead(D1_PIN) ? "ON" : "OFF") + ",D2:" + String(digitalRead(D2_PIN) ? "ON" : "OFF");
    client.publish(topic_status, pins.c_str());
    Serial.print("Periodic publish: ");
    Serial.println(pins);
  }
}
