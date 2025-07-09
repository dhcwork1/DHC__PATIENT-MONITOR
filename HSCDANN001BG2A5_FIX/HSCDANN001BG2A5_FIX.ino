#include <Wire.h>

// Pin definisi untuk Arduino Mega
#define POMPA   5
#define VALVE1  4
#define VALVE2  6

#define MAX_DATA 200
uint16_t raw_data[MAX_DATA];
float tekanan_mmHg[MAX_DATA];
float osilasi[MAX_DATA];
int data_count = 0;

const byte SENSOR_ADDR = 0x28;
bool mulai = false;

void setup() {
  Serial.begin(115200);
  Wire.begin(); // SDA = 20, SCL = 21 untuk Mega

  pinMode(POMPA, OUTPUT);
  pinMode(VALVE1, OUTPUT);
  pinMode(VALVE2, OUTPUT);

  digitalWrite(POMPA, LOW);
  digitalWrite(VALVE1, HIGH); // tertutup
  digitalWrite(VALVE2, HIGH); // tertutup

  Serial.println("=== SISTEM NIBP - ARDUINO MEGA AKTIF ===");
  Serial.println("Ketik START di Serial Monitor untuk memulai.");
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd.equalsIgnoreCase("START")) {
      mulai = true;
      data_count = 0;
      Serial.println("\n> Mulai pengukuran NIBP...");
      inflasi();
    }
  }
}
