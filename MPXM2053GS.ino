                                                        /*//////////////////////////////////////////////////////////
                                                         * MPXM2053GS DIBERI TEKANAN DENGAN BERBAGAI GAIN dan OFFSITE
                                                         *//////////////////////////////////////////////////////////







const int sensorPin = A0; // Pin analog tempat output AD620 terhubung

void setup() {
  Serial.begin(9600); // Inisialisasi komunikasi serial untuk debugging
}

void loop() {
  // Membaca nilai analog dari pin sensor
  int analogValue = analogRead(sensorPin);

  // Mengkonversi nilai analog ke tegangan (sesuai dengan referensi ADC mikrokontroler)
  // Misal, jika Arduino Uno (5V ref) dan 10-bit ADC (1024 nilai):
  float voltage = analogValue * (5.0 / 1023.0); // Atau 3.3 / 1023.0 jika 3.3V ref

  // --- Kalibrasi dan Konversi ke Tekanan ---
  // Di sini adalah bagian terpenting untuk mengkonversi tegangan ke tekanan.
  // Ini memerlukan kalibrasi. Anda perlu mencari tahu hubungan antara:
  // 1. Output sensor (mV) vs. Tekanan (kPa) - dari datasheet sensor
  // 2. Output AD620 (V) vs. Input AD620 (mV) - ini adalah gain yang Anda atur
  // 3. Output ADC (nilai) vs. Output AD620 (V) - ini adalah referensi ADC mikrokontroler

  // Contoh sederhana (Anda perlu melakukan kalibrasi aktual):
  // Misalkan Anda telah mengkalibrasi bahwa 0 kPa menghasilkan 0.5V dan 50 kPa menghasilkan 4.5V dari AD620.
  // float pressure = map(analogValue, analog_value_min_kPa0, analog_value_max_kPa50, 0, 50); // Jika menggunakan map untuk integer
  // Atau dengan rumus linier:
  // float pressure = ((voltage - offset_voltage) / sensitivity_V_per_kPa);

  // Untuk kalibrasi yang lebih akurat:
  // A. Tentukan gain aktual AD620 Anda:
  // Gain = (Output V AD620) / (Input V Sensor)
  // B. Tentukan Offset V Sensor pada 0 kPa.
  // C. Tentukan Sensitivitas Sensor (mV/kPa) dari datasheet (misal 0.8 mV/kPa untuk MPXM2053GS)

  // Contoh:
  // Jika gain AD620 = 100, maka setiap 1mV dari sensor akan menjadi 100mV di output AD620.
  // Sensitivitas sensor MPXM2053GS = 0.8 mV/kPa
  // Jadi, sensitivitas total setelah AD620 = 0.8 mV/kPa * Gain
  // Misal Gain = 100 -> Sensitivitas Total = 80 mV/kPa = 0.08 V/kPa
  // Tegangan offset sensor (misal 0 mV) akan menjadi 0 V di output AD620 (jika offset AD620 diatur 0).

  // Langkah kalibrasi yang lebih praktis:
  // 1. Letakkan sensor pada tekanan nol (atmosfer). Baca nilai analog (analogValue_min).
  // 2. Terapkan tekanan maksimum yang diketahui (misal 50 kPa). Baca nilai analog (analogValue_max).
  // 3. Gunakan rumus linier:
  //    float pressure = (float)(analogValue - analogValue_min) * (50.0 / (analogValue_max - analogValue_min));

  // Tampilkan hasil
  Serial.print("Nilai Analog: ");
  Serial.print(analogValue);
  Serial.print("\tTegangan Output AD620: ");
  Serial.print(voltage, 4); // Tampilkan 4 desimal
  // Serial.print("\tTekanan: ");
  // Serial.print(pressure, 2); // Tampilkan 2 desimal
  Serial.println(" kPa");

  delay(100); // Ambil bacaan setiap 100 ms
}
