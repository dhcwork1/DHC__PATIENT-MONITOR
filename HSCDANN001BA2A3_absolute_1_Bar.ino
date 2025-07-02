                                                        /*///////////////////////////////////////
                                                         * HSCDANN001BA2A3 DIBERI TEKANAN
                                                         *//////////////////////////////////////






#include <Wire.h>

const uint8_t SENSOR_ADDR = 0x28;  // I2C address of HSCDANN001BA2A3
uint8_t buffer[3];

// Kalibrasi dari datasheet (10%–90% rentang output)
const int OUTPUT_MIN = 1638;    // 10% dari 16383
const int OUTPUT_MAX = 14745;   // 90% dari 16383
const float PRESSURE_MIN = 0.0;     // Minimum pressure (kPa)
const float PRESSURE_MAX = 100.0;   // Maximum pressure (kPa)

const float KPA_TO_MMHG = 7.50062;  // Faktor konversi

void setup() {
  Serial.begin(115200);
  Wire.begin();
  delay(100);

  Serial.println("Honeywell HSCDANN001BA2A3 Sensor Reader");
  Serial.println("Raw | Pressure (kPa) | Pressure (mmHg)");
}

void loop() {
  Wire.requestFrom(SENSOR_ADDR, (uint8_t)3);

  if (Wire.available() == 3) {
    buffer[0] = Wire.read();
    buffer[1] = Wire.read();
    buffer[2] = Wire.read();  // CRC, abaikan

    // Ambil 14-bit dari dua byte
    int raw = ((buffer[0] & 0x3F) << 8) | buffer[1];

    // Hitung tekanan dalam kPa (dengan kalibrasi dari datasheet)
    float pressure_kPa = ((float)(raw - OUTPUT_MIN) * (PRESSURE_MAX - PRESSURE_MIN)) / (OUTPUT_MAX - OUTPUT_MIN) + PRESSURE_MIN;

    // Batasi agar tidak negatif
    if (pressure_kPa < 0) pressure_kPa = 0;

    // Konversi ke mmHg
    float pressure_mmHg = pressure_kPa * KPA_TO_MMHG;

    // Tampilkan hasil
    Serial.print("Raw: ");
    Serial.print(raw);
    Serial.print(" | kPa: ");
    Serial.print(pressure_kPa, 2);
    Serial.print(" | mmHg: ");
    Serial.println(pressure_mmHg, 2);
  }

  delay(200);
}
