import sys
import serial
import csv
import time
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QTextEdit
)
from PyQt5.QtCore import QThread, pyqtSignal
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# --- Worker Thread ---
class SerialReader(QThread):
    data_received = pyqtSignal(str, int, float)  # time_str, raw, mmHg
    done = pyqtSignal(str)

    def __init__(self, port='COM14', baud=115200):
        super().__init__()
        self.port = port
        self.baud = baud
        self.running = False

    def run(self):
        try:
            with serial.Serial(self.port, self.baud, timeout=1) as ser:
                time.sleep(2)  # tunggu koneksi serial
                ser.write(b'START\n')
                self.running = True
                while self.running:
                    line = ser.readline().decode().strip()
                    if "Tekanan:" in line:
                        try:
                            mmhg_str = line.replace("Tekanan:", "").replace("mmHg", "").strip()
                            mmhg = float(mmhg_str)
                            raw = int((mmhg / 0.05825) + 1648)
                            now = datetime.now().strftime('%H:%M:%S')
                            self.data_received.emit(now, raw, mmhg)
                        except:
                            continue
                    elif "HASIL" in line:
                        self.done.emit(line)
                        break
        except Exception as e:
            self.done.emit(f"Gagal konek: {e}")

    def stop(self):
        self.running = False

# --- GUI Utama ---
class NIBPGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Monitor NIBP - Arduino")
        self.resize(800, 600)

        # Layout
        self.layout = QVBoxLayout()
        self.start_btn = QPushButton("START Pengukuran")
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)

        self.canvas = FigureCanvas(plt.Figure())
        self.ax = self.canvas.figure.subplots()
        self.line, = self.ax.plot([], [], label="Tekanan (mmHg)")
        self.ax.set_title("Grafik Tekanan")
        self.ax.set_xlabel("Sample")
        self.ax.set_ylabel("mmHg")
        self.ax.grid(True)

        self.layout.addWidget(self.start_btn)
        self.layout.addWidget(self.canvas)
        self.layout.addWidget(QLabel("Log Output:"))
        self.layout.addWidget(self.output_text)
        self.setLayout(self.layout)
        self.start_btn.clicked.connect(self.start_serial)

        # Data penyimpanan
        self.times, self.raws, self.mmhgs = [], [], []
        self.log_file = open("log.txt", "w")
        self.csv_file = open("nibp_data_gui.csv", "w", newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(["Time", "RAW", "mmHg"])

    def start_serial(self):
        self.output_text.clear()
        self.times.clear()
        self.raws.clear()
        self.mmhgs.clear()
        self.ax.cla()
        self.ax.set_title("Grafik Tekanan")
        self.ax.set_xlabel("Sample")
        self.ax.set_ylabel("mmHg")
        self.ax.grid(True)
        self.line, = self.ax.plot([], [], label="Tekanan (mmHg)")

        self.reader = SerialReader()
        self.reader.data_received.connect(self.update_data)
        self.reader.done.connect(self.stop_serial)
        self.reader.start()

    def update_data(self, time_str, raw, mmhg):
        self.times.append(time_str)
        self.raws.append(raw)
        self.mmhgs.append(mmhg)

        # Update grafik
        self.line.set_xdata(range(len(self.mmhgs)))
        self.line.set_ydata(self.mmhgs)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

        # Tampilkan dan simpan
        log_line = f"{time_str} | RAW: {raw} | mmHg: {mmhg:.2f}"
        self.output_text.append(log_line)
        self.log_file.write(log_line + "\n")
        self.csv_writer.writerow([time_str, raw, mmhg])

    def stop_serial(self, message):
        self.output_text.append("\n✅ Pengukuran selesai.")
        self.log_file.write("\n=== Selesai ===\n")
        self.log_file.flush()
        self.csv_file.flush()
        self.reader.quit()
        self.reader.wait()

        # Tampilkan hasil jika ada
        if "Sistolik" in message and "Diastolik" in message:
            try:
                parts = message.split(',')
                sistolik = parts[0].split('=')[1].strip().replace("mmHg", "")
                diastolik = parts[1].split('=')[1].strip().replace("mmHg", "")
                bpm = parts[2].split('=')[1].strip()

                self.output_text.append("\n💡 Hasil Pengukuran:")
                self.output_text.append(f"   🩺 Sistolik  : {sistolik} mmHg")
                self.output_text.append(f"   🫀 Diastolik : {diastolik} mmHg")
                self.output_text.append(f"   ❤️ BPM       : {bpm}")
            except:
                self.output_text.append("\n⚠️ Format hasil tidak dikenali:")
                self.output_text.append(message)
        else:
            self.output_text.append(message)

    def closeEvent(self, event):
        try:
            self.reader.stop()
            self.reader.wait()
        except:
            pass
        self.log_file.close()
        self.csv_file.close()
        event.accept()

# --- Jalankan ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = NIBPGUI()
    window.show()
    sys.exit(app.exec_())
