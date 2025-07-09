void inflasi() {
  digitalWrite(POMPA, HIGH);
  digitalWrite(VALVE1, HIGH);
  digitalWrite(VALVE2, HIGH);

  while (true) {
    float tekanan = bacaTekanan();
    Serial.print("Tekanan: ");
    Serial.print(tekanan);
    Serial.println(" mmHg");

    if (tekanan >= 160.0) {
      Serial.println("> Tekanan target tercapai. Mulai deflasi...");
      break;
    }
    delay(50);
  }

  mulai_deflasi();
}
