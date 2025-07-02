                                                                      /*////////////////////////////////////////////////////////
                                                                      
                                                                                  CEK VALVE MENGGUNAKAN PWM MODULE 
                                                                                    ALTERNATIVE VALVE PORPOTIONAL
                                                                                               PWM 50
        
                                                                      ////////////////////////////////////////////////////////*/





const int P=9;
const int P1=10;
const int V=5;
const int V1=6;
// Pin definisi HX710B
const int dataPin = 2;   // Pin DOUT dari modul HX710B
const int clockPin = 3;  // Pin SCK dari modul HX710B

// Kalibrasi tekanan: nilai ADC pada 0 mmHg dan 300 mmHg
const long raw_0mmHg = 504000;     // Sesuaikan hasil saat tekanan 0 mmHg
const long raw_300mmHg = 8388607;  // Nilai maksimum saat tekanan penuh

// Moving average buffer
const int bufferSize = 10;         // Ukuran buffer rata-rata
long buffer[bufferSize];           // Array untuk menyimpan nilai
int bufferIndex = 0;               // Indeks array
bool bufferFilled = false;         // Apakah buffer sudah penuh?

void setup() {
  pinMode(dataPin, INPUT);         // DOUT sebagai input
  pinMode(clockPin, OUTPUT);       // SCK sebagai output
  pinMode(P,OUTPUT);
  pinMode(P1,OUTPUT);
  pinMode(V,OUTPUT);
  pinMode(V1,OUTPUT);
  Serial.begin(9600);              // Mulai komunikasi serial
  digitalWrite(V,HIGH);
  digitalWrite(V1,LOW);
}

// Fungsi membaca data dari HX710B, hasilnya signed 24-bit
long readHX710B() {
  long result = 0;

  // Tunggu hingga sensor siap (DOUT = LOW)
  while (digitalRead(dataPin) == HIGH);

  // Baca 24 bit data dari HX710B
  for (int i = 0; i < 24; i++) {
    digitalWrite(clockPin, HIGH);
    result = (result << 1) | digitalRead(dataPin);  // Geser bit dan ambil data
    digitalWrite(clockPin, LOW);
  }

  // Berikan 1 extra clock pulse (channel selection atau reset internal HX710B)
  digitalWrite(clockPin, HIGH);
  delayMicroseconds(1);
  digitalWrite(clockPin, LOW);

  // Jika bit tertinggi (MSB) adalah 1, artinya nilai negatif → sign extend
  if (result & 0x800000) {
    result |= 0xFF000000; // Extend ke 32-bit signed integer
  }

  return result;  // Nilai raw signed dari ADC
}

// Fungsi konversi nilai raw ADC ke tekanan dalam mmHg
float convertToMMHg(long rawValue) {
  float mmHg = (rawValue - raw_0mmHg) * 300.0 / (raw_300mmHg - raw_0mmHg);
  if (mmHg < 0) mmHg = 0; // Jangan tampilkan negatif
  return mmHg;
}

// Fungsi moving average dari 10 pembacaan terakhir
float getMovingAverage(float newValue) {
  buffer[bufferIndex] = newValue;          // Simpan nilai baru ke buffer
  bufferIndex = (bufferIndex + 1) % bufferSize;  // Geser indeks

  // Cek apakah buffer sudah terisi penuh
  if (bufferIndex == 0) bufferFilled = true;

  // Hitung rata-rata
  int count = bufferFilled ? bufferSize : bufferIndex;
  float sum = 0;
  for (int i = 0; i < count; i++) {
    sum += buffer[i];
  }

  return sum / count;
}

void loop() {
   analogWrite(V,50);
   digitalWrite(V1,LOW);
   analogWrite(P,HIGH);
  digitalWrite(P1,LOW);
  long rawValue = readHX710B();                  // Baca raw data dari sensor
  float pressure = convertToMMHg(rawValue);      // Konversi ke mmHg
  float averagePressure = getMovingAverage(pressure);  // Hitung rata-rata

  // Tampilkan hasil ke Serial Monitor
  Serial.print("Pressure (mmHg): ");
  Serial.print(pressure, 2);            // Hasil instan
  Serial.print(" | Smoothed: ");
  Serial.println(averagePressure, 2);   // Hasil perataan

  delay(200);  // Delay antar pembacaan
}
