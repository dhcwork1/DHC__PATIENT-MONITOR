void mulai_deflasi() {
  digitalWrite(POMPA, LOW);     // Matikan pompa
  digitalWrite(VALVE1, LOW);    // Buka valve1

  while (data_count < MAX_DATA) {
    float t = bacaTekanan();
    tekanan_mmHg[data_count] = t;

    if (data_count >= 2)
      osilasi[data_count] = abs(t - tekanan_mmHg[data_count - 1]);
    else
      osilasi[data_count] = 0;

    data_count++;
    delay(80);
  }

  hitung_dan_tampilkan_hasil();
}
