void hitung_dan_tampilkan_hasil() {
  float max_osc = 0;
  int idx_map = 0;
  for (int i = 10; i < data_count - 10; i++) {
    if (osilasi[i] > max_osc) {
      max_osc = osilasi[i];
      idx_map = i;
    }
  }

  float map_pressure = tekanan_mmHg[idx_map];

  float systolic = 0;
  float threshold_sys = max_osc * 0.55;
  for (int i = idx_map; i > 0; i--) {
    if (osilasi[i] < threshold_sys) {
      systolic = tekanan_mmHg[i];
      break;
    }
  }

  float diastolic = 0;
  float threshold_dia = max_osc * 0.85;
  for (int i = idx_map; i < data_count; i++) {
    if (osilasi[i] < threshold_dia) {
      diastolic = tekanan_mmHg[i];
      break;
    }
  }

  digitalWrite(VALVE2, LOW);  // Buka buang udara
  delay(2000);
  digitalWrite(VALVE1, LOW);
  digitalWrite(VALVE2, LOW);

  Serial.println("\n=== HASIL NIBP ===");
  Serial.print("Sistolik  : "); Serial.print(systolic, 1); Serial.println(" mmHg");
  Serial.print("Diastolik : "); Serial.print(diastolic, 1); Serial.println(" mmHg");
  Serial.print("MAP       : "); Serial.print(map_pressure, 1); Serial.println(" mmHg");
  Serial.println("===================================");
  Serial.println("Ketik START lagi untuk pengukuran baru.");
}
