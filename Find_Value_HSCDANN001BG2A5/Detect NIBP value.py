import sys
import serial
import csv
import time
from datetime import datetime
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, 
    QLabel, QTextEdit, QFileDialog, QTabWidget, QGroupBox
)
from PyQt5.QtCore import QThread, pyqtSignal
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# --- Worker Thread untuk Serial ---
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

# --- Class untuk Analisis BP ---
class BPAnalyzer:
    def __init__(self):
        pass
    
    def moving_average(self, x, w=5):
        """Smoothing filter untuk mengurangi noise"""
        return np.convolve(x, np.ones(w)/w, mode='valid')
    
    def analyze_bp(self, pressure_data):
        """Analisis tekanan darah dari data deflasi"""
        try:
            # Cari puncak inflasi (mulai deflasi)
            peak_idx = np.argmax(pressure_data)
            deflation_data = pressure_data[peak_idx:]
            
            # Apply smoothing filter
            smoothed = self.moving_average(deflation_data, w=5)
            
            # Deteksi puncak osilasi
            peaks, _ = find_peaks(smoothed, distance=5)
            if len(peaks) == 0:
                return None, None, None, None, None, None
            
            peak_values = smoothed[peaks]
            
            # Hitung MAP (Maximum Amplitude Point)
            max_peak_index = peaks[np.argmax(peak_values)]
            MAP_value = smoothed[max_peak_index]
            
            # Filter puncak yang signifikan
            threshold = 0.3 * np.max(peak_values)
            valid_peaks = peaks[peak_values > threshold]
            
            if len(valid_peaks) < 20:
                return None, None, None, None, None, None
            
            # Estimasi Sistolik dan Diastolik
            systolic_value = smoothed[valid_peaks[1]] if len(valid_peaks) > 1 else MAP_value
            diastolic_value = smoothed[valid_peaks[-19]] if len(valid_peaks) >= 20 else MAP_value
            
            return smoothed, peaks, MAP_value, systolic_value, diastolic_value, valid_peaks
            
        except Exception as e:
            print(f"Error dalam analisis: {e}")
            return None, None, None, None, None, None

# --- GUI Utama ---
class NIBPGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Monitor NIBP dengan Analisis - Arduino")
        self.resize(1200, 800)
        
        # Inisialisasi analyzer
        self.bp_analyzer = BPAnalyzer()
        
        # Setup UI
        self.setup_ui()
        
        # Data penyimpanan
        self.times, self.raws, self.mmhgs = [], [], []
        self.current_csv_file = None
        self.log_file = None
        self.csv_file = None
        self.csv_writer = None

    def setup_ui(self):
        # Layout utama
        main_layout = QVBoxLayout()
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Tab 1: Real-time monitoring
        self.monitoring_tab = QWidget()
        self.setup_monitoring_tab()
        self.tabs.addTab(self.monitoring_tab, "Real-time Monitoring")
        
        # Tab 2: Data analysis
        self.analysis_tab = QWidget()
        self.setup_analysis_tab()
        self.tabs.addTab(self.analysis_tab, "Data Analysis")
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def setup_monitoring_tab(self):
        layout = QVBoxLayout()
        
        # Control buttons
        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("START Pengukuran")
        self.stop_btn = QPushButton("STOP Pengukuran")
        self.stop_btn.setEnabled(False)
        self.analyze_btn = QPushButton("Analisis Data Terakhir")
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(self.analyze_btn)
        layout.addLayout(control_layout)
        
        # Real-time plot
        self.canvas = FigureCanvas(plt.Figure(figsize=(10, 4)))
        self.ax = self.canvas.figure.subplots()
        self.line, = self.ax.plot([], [], label="Tekanan (mmHg)")
        self.ax.set_title("Grafik Tekanan Real-time")
        self.ax.set_xlabel("Sample")
        self.ax.set_ylabel("mmHg")
        self.ax.grid(True)
        self.ax.legend()
        
        layout.addWidget(self.canvas)
        
        # Output text
        layout.addWidget(QLabel("Log Output:"))
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMaximumHeight(200)
        layout.addWidget(self.output_text)
        
        self.monitoring_tab.setLayout(layout)
        
        # Connect signals
        self.start_btn.clicked.connect(self.start_serial)
        self.stop_btn.clicked.connect(self.stop_measurement)
        self.analyze_btn.clicked.connect(self.analyze_current_data)

    def setup_analysis_tab(self):
        layout = QVBoxLayout()
        
        # File selection
        file_layout = QHBoxLayout()
        self.load_btn = QPushButton("Load CSV File")
        self.file_label = QLabel("No file selected")
        file_layout.addWidget(self.load_btn)
        file_layout.addWidget(self.file_label)
        layout.addLayout(file_layout)
        
        # Analysis plot
        self.analysis_canvas = FigureCanvas(plt.Figure(figsize=(12, 6)))
        self.analysis_ax = self.analysis_canvas.figure.subplots()
        layout.addWidget(self.analysis_canvas)
        
        # Results display
        results_group = QGroupBox("Hasil Analisis")
        results_layout = QVBoxLayout()
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(150)
        results_layout.addWidget(self.results_text)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        self.analysis_tab.setLayout(layout)
        
        # Connect signals
        self.load_btn.clicked.connect(self.load_csv_file)

    def start_serial(self):
        # Setup file untuk saving
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_csv_file = f"nibp_data_{timestamp}.csv"
        
        self.log_file = open(f"log_{timestamp}.txt", "w")
        self.csv_file = open(self.current_csv_file, "w", newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(["Time", "RAW", "mmHg"])
        
        # Clear data dan UI
        self.output_text.clear()
        self.times.clear()
        self.raws.clear()
        self.mmhgs.clear()
        self.reset_plot()
        
        # Start serial reader
        self.reader = SerialReader()
        self.reader.data_received.connect(self.update_data)
        self.reader.done.connect(self.stop_serial)
        self.reader.start()
        
        # Update button states
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        self.output_text.append(f"📊 Mulai pengukuran... File: {self.current_csv_file}")

    def reset_plot(self):
        self.ax.clear()
        self.ax.set_title("Grafik Tekanan Real-time")
        self.ax.set_xlabel("Sample")
        self.ax.set_ylabel("mmHg")
        self.ax.grid(True)
        self.line, = self.ax.plot([], [], label="Tekanan (mmHg)")
        self.ax.legend()

    def stop_measurement(self):
        if hasattr(self, 'reader'):
            self.reader.stop()
            self.reader.quit()
            self.reader.wait()
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.output_text.append("⏹️ Pengukuran dihentikan secara manual")

    def update_data(self, time_str, raw, mmhg):
        self.times.append(time_str)
        self.raws.append(raw)
        self.mmhgs.append(mmhg)

        # Update grafik real-time
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
        
        if hasattr(self, 'log_file') and self.log_file:
            self.log_file.write("\n=== Selesai ===\n")
            self.log_file.flush()
            self.log_file.close()
        
        if hasattr(self, 'csv_file') and self.csv_file:
            self.csv_file.flush()
            self.csv_file.close()
        
        # Update button states
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        # Parse dan tampilkan hasil jika ada
        if "Sistolik" in message and "Diastolik" in message:
            try:
                parts = message.split(',')
                sistolik = parts[0].split('=')[1].strip().replace("mmHg", "")
                diastolik = parts[1].split('=')[1].strip().replace("mmHg", "")
                bpm = parts[2].split('=')[1].strip()

                self.output_text.append("\n💡 Hasil dari Arduino:")
                self.output_text.append(f"   🩺 Sistolik  : {sistolik} mmHg")
                self.output_text.append(f"   🫀 Diastolik : {diastolik} mmHg")
                self.output_text.append(f"   ❤️ BPM       : {bpm}")
            except:
                self.output_text.append("\n⚠️ Format hasil tidak dikenali:")
                self.output_text.append(message)
        else:
            self.output_text.append(message)

    def analyze_current_data(self):
        """Analisis data yang baru saja diambil"""
        if len(self.mmhgs) < 50:
            self.output_text.append("⚠️ Data terlalu sedikit untuk analisis (minimum 50 samples)")
            return
        
        self.output_text.append("\n🔍 Memulai analisis data...")
        
        # Lakukan analisis
        pressure_data = np.array(self.mmhgs)
        smoothed, peaks, MAP, systolic, diastolic, valid_peaks = self.bp_analyzer.analyze_bp(pressure_data)
        
        if smoothed is not None:
            self.display_analysis_results(smoothed, peaks, MAP, systolic, diastolic, valid_peaks, 
                                        "Analisis Data Real-time")
            
            self.output_text.append(f"📊 Hasil Analisis:")
            self.output_text.append(f"   🩺 Sistolik  : {systolic:.1f} mmHg")
            self.output_text.append(f"   🫀 Diastolik : {diastolic:.1f} mmHg")
            self.output_text.append(f"   💓 MAP       : {MAP:.1f} mmHg")
            
            # Switch ke tab analysis untuk melihat hasil
            self.tabs.setCurrentIndex(1)
        else:
            self.output_text.append("❌ Gagal menganalisis data")

    def load_csv_file(self):
        """Load file CSV untuk analisis"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Pilih file CSV", "", "CSV files (*.csv)"
        )
        
        if file_path:
            try:
                df = pd.read_csv(file_path)
                if 'mmHg' not in df.columns:
                    self.results_text.setText("❌ File CSV harus memiliki kolom 'mmHg'")
                    return
                
                self.file_label.setText(f"File: {file_path.split('/')[-1]}")
                pressure_data = df['mmHg'].values
                
                # Lakukan analisis
                smoothed, peaks, MAP, systolic, diastolic, valid_peaks = self.bp_analyzer.analyze_bp(pressure_data)
                
                if smoothed is not None:
                    self.display_analysis_results(smoothed, peaks, MAP, systolic, diastolic, valid_peaks,
                                                f"Analisis File: {file_path.split('/')[-1]}")
                    
                    results = f"""📊 Hasil Analisis File CSV:
🩺 Sistolik  : {systolic:.1f} mmHg
🫀 Diastolik : {diastolic:.1f} mmHg  
💓 MAP       : {MAP:.1f} mmHg

📈 Total samples: {len(pressure_data)}
🔍 Deflation samples: {len(smoothed)}
📍 Peaks detected: {len(peaks)}
✅ Valid peaks: {len(valid_peaks)}"""
                    
                    self.results_text.setText(results)
                else:
                    self.results_text.setText("❌ Gagal menganalisis data dari file CSV")
                    
            except Exception as e:
                self.results_text.setText(f"❌ Error membaca file: {str(e)}")

    def display_analysis_results(self, smoothed, peaks, MAP, systolic, diastolic, valid_peaks, title):
        """Tampilkan hasil analisis di plot"""
        self.analysis_ax.clear()
        
        # Plot data smoothed
        self.analysis_ax.plot(smoothed, label='Tekanan (smoothed)', color='blue', linewidth=1.5)
        
        # Plot semua peaks
        self.analysis_ax.plot(peaks, smoothed[peaks], "rx", label="Puncak Osilasi", markersize=6)
        
        # Plot garis referensi
        self.analysis_ax.axhline(y=MAP, color='green', linestyle='--', 
                               label=f'MAP ≈ {MAP:.1f} mmHg', linewidth=2)
        self.analysis_ax.axhline(y=systolic, color='red', linestyle='--', 
                               label=f'Sistolik ≈ {systolic:.1f} mmHg', linewidth=2)
        self.analysis_ax.axhline(y=diastolic, color='purple', linestyle='--', 
                               label=f'Diastolik ≈ {diastolic:.1f} mmHg', linewidth=2)
        
        # Highlight valid peaks
        if valid_peaks is not None and len(valid_peaks) > 0:
            self.analysis_ax.plot(valid_peaks, smoothed[valid_peaks], "go", 
                                label="Valid Peaks", markersize=4, alpha=0.7)
        
        self.analysis_ax.set_title(title)
        self.analysis_ax.set_xlabel("Sample Index (Deflation Phase)")
        self.analysis_ax.set_ylabel("Tekanan (mmHg)")
        self.analysis_ax.legend()
        self.analysis_ax.grid(True, alpha=0.3)
        
        self.analysis_canvas.draw()

    def closeEvent(self, event):
        # Cleanup saat aplikasi ditutup
        try:
            if hasattr(self, 'reader'):
                self.reader.stop()
                self.reader.wait()
        except:
            pass
        
        if hasattr(self, 'log_file') and self.log_file:
            self.log_file.close()
        if hasattr(self, 'csv_file') and self.csv_file:
            self.csv_file.close()
            
        event.accept()

# --- Jalankan Aplikasi ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = NIBPGUI()
    window.show()
    sys.exit(app.exec_())
