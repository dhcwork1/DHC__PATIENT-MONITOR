
float bacaTekanan() {
  Wire.beginTransmission(SENSOR_ADDR);
  Wire.endTransmission();
  Wire.requestFrom(SENSOR_ADDR, 4);
  if (Wire.available() < 4) return 0;

  uint8_t b1 = Wire.read();
  uint8_t b2 = Wire.read();
  Wire.read(); Wire.read(); // suhu (tidak dipakai)

  uint16_t raw = ((b1 & 0x3F) << 8) | b2;
  raw_data[data_count] = raw;

  // Kalibrasi: 1648 = 0 mmHg, 6800 = 300 mmHg
  float mmHg = (raw - 1648) * 0.05825;
  if (mmHg < 0) mmHg = 0;
  return mmHg;
}
