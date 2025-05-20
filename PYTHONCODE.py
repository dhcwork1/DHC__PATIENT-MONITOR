import sys
import numpy as np
import datetime
import serial
import threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QPushButton, QDialog
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
import pyqtgraph as pg

# ----------- Komunikasi Data Serial ----------
class SerialData(QObject):
    data_received = pyqtSignal(float, float, float)  # ECG, SpO₂, RESP

# ----------- Kelas Utama ----------
class PatientMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Patient Monitor")
        self.resize(1820, 960)
        self.setStyleSheet("background-color: black;")

        # Signal serial
        self.serial_data = SerialData()
        self.serial_data.data_received.connect(self.receive_serial_data)

        # Buffer data sinyal
        self.buffer_size = 1000
        self.timer_interval = 10  # ms
        self.x = np.linspace(0, self.buffer_size * self.timer_interval / 1000.0, self.buffer_size)
        self.index = 0
        self.ecg_data = np.zeros(self.buffer_size)
        self.spo2_data = np.zeros(self.buffer_size)
        self.resp_data = np.zeros(self.buffer_size)

        # Layout utama
        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        graph_layout = QVBoxLayout()

        # Grafik sinyal
        self.ecg_plot, self.ecg_curve, self.ecg_vline = self.create_plot("ECG", "lime", self.ecg_data, (-1.5, 1.5))
        self.spo2_plot, self.spo2_curve, self.spo2_vline = self.create_plot("SpO₂", "red", self.spo2_data, (-0.2, 1.2))
        self.resp_plot, self.resp_curve, self.resp_vline = self.create_plot("RESP", "yellow", self.resp_data, (-0.5, 1.5))

        graph_layout.addWidget(self.ecg_plot)
        graph_layout.addWidget(self.spacer())
        graph_layout.addWidget(self.spo2_plot)
        graph_layout.addWidget(self.spacer())
        graph_layout.addWidget(self.resp_plot)
        graph_layout.addStretch()

        # Panel data vital
        info_panel = QVBoxLayout()
        info_panel.setSpacing(10)
        info_panel.addLayout(self.create_info_panel())

        # Tombol Setting dan Start NIBP
        button_layout = QHBoxLayout()
        setting_btn = QPushButton("Setting")
        setting_btn.setStyleSheet("background-color: #007bff; color: white; padding: 12px; font-size: 16px;")
        setting_btn.clicked.connect(self.show_menu)

        nibp_btn = QPushButton("Start NIBP")
        nibp_btn.setStyleSheet("background-color: #28a745; color: white; padding: 12px; font-size: 16px;")

        button_layout.addWidget(setting_btn)
        button_layout.addWidget(nibp_btn)
        info_panel.addLayout(button_layout)

        # Garis pemisah vertikal
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setStyleSheet("border-left: 2px dashed gray;")

        top_layout.addLayout(graph_layout, 4)
        top_layout.addWidget(line)
        top_layout.addLayout(info_panel, 1)

        main_layout.addLayout(top_layout)
        self.setLayout(main_layout)

        # Timer untuk update GUI
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_waveform_display)
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(self.timer_interval)

        # Jalankan thread serial
        self.start_serial_thread()

    def create_plot(self, title, color, data_array, y_range):
        container = QFrame()
        layout = QVBoxLayout()
        label = QLabel(title)
        label.setStyleSheet(f"color: {color}; font-size: 14px;")
        label.setAlignment(Qt.AlignHCenter)
        layout.addWidget(label)

        plot = pg.PlotWidget()
        plot.setBackground('black')
        plot.setYRange(*y_range)
        plot.getPlotItem().hideAxis('bottom')
        plot.getPlotItem().hideAxis('left')
        curve = plot.plot(self.x, data_array, pen=pg.mkPen(color, width=2))
        vline = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen('black', width=9))
        plot.addItem(vline)

        layout.addWidget(plot)
        container.setLayout(layout)
        return container, curve, vline

    def spacer(self):
        s = QFrame()
        s.setFixedHeight(95)
        s.setStyleSheet("background-color: black;")
        return s

    def create_info_panel(self):
        layout = QVBoxLayout()
        top_row = QHBoxLayout()
        top_row.addStretch()
        self.label_datetime = QLabel("2025-05-16 12:00:00")
        self.label_datetime.setStyleSheet("color: gray; font-size: 12px;")
        self.label_battery = QLabel("Battery: 80%")
        self.label_battery.setStyleSheet("color: gray; font-size: 12px;")
        top_row.addWidget(self.label_datetime)
        top_row.addSpacing(10)
        top_row.addWidget(self.label_battery)
        layout.addLayout(top_row)

        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: gray;")
        layout.addSpacing(10)
        layout.addWidget(separator)

        # Label numerik
        self.label_hr = self.create_data("HR", "--", "bpm", "lime", 80)
        self.label_spo2 = self.create_data("SpO₂", "--%", "", "red", 50)
        self.label_resp = self.create_data("RESP", "--", "rpm", "yellow", 70)
        self.label_temp = self.create_data("TEMP", "36.8°C", "", "cyan", 50)
        self.label_nibp = self.create_data("NIBP", "118/78", "mmHg", "orange", 50)

        layout.addWidget(self.label_hr)
        layout.addWidget(self.label_spo2)
        layout.addWidget(self.label_resp)
        layout.addWidget(self.label_temp)
        layout.addWidget(self.label_nibp)
        return layout

    def create_data(self, title, value, unit, color, size):
        container = QFrame()
        layout = QVBoxLayout()
        row = QHBoxLayout()
        row.addWidget(QLabel(f"<span style='color:{color}; font-size:25px'>{title}</span>"))
        row.addStretch()
        row.addWidget(QLabel(f"<span style='color:{color}; font-size:19px'>{unit}</span>"))
        layout.addLayout(row)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"color: {color}; font-size: {size}px; font-weight: bold;")
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: gray;")
        layout.addWidget(sep)

        container.setLayout(layout)
        container.value_label = self.value_label
        return container

    def show_menu(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Settings Menu")
        dialog.setStyleSheet("background-color: #222; color: white;")
        layout = QVBoxLayout()
        for item in [
            "Patient Info", "Trend Menu", "Alarm Settings", "Monitor Setup",
            "Parameter Setup", "Record / Screenshot", "Network / Connectivity", "System Settings"
        ]:
            btn = QPushButton(item)
            btn.setStyleSheet("background-color: #444; color: white; padding: 8px; font-size: 14px;")
            btn.clicked.connect(lambda _, name=item: self.show_submenu(name))
            layout.addWidget(btn)

        dialog.setLayout(layout)
        dialog.resize(400, 400)
        dialog.exec_()

    def show_submenu(self, name):
        dlg = QDialog(self)
        dlg.setWindowTitle(name)
        dlg.setStyleSheet("background-color: #333; color: white;")
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"{name} configuration goes here..."))
        dlg.setLayout(layout)
        dlg.exec_()

    def update_datetime(self):
        now = datetime.datetime.now()
        self.label_datetime.setText(now.strftime("%Y-%m-%d %H:%M:%S"))

    def update_waveform_display(self):
        self.ecg_curve.setData(self.x, self.ecg_data)
        self.spo2_curve.setData(self.x, self.spo2_data)
        self.resp_curve.setData(self.x, self.resp_data)

        vpos = self.x[self.index]
        self.ecg_vline.setPos(vpos)
        self.spo2_vline.setPos(vpos)
        self.resp_vline.setPos(vpos)
        self.index = (self.index + 1) % self.buffer_size

    def receive_serial_data(self, ecg, spo2, resp):
        self.ecg_data[self.index] = ecg
        self.spo2_data[self.index] = spo2
        self.resp_data[self.index] = resp

        self.label_hr.value_label.setText(str(int(60 + ecg * 10)))
        self.label_spo2.value_label.setText(f"{int(spo2 * 100)}%")
        self.label_resp.value_label.setText(str(int(resp * 20)))

    def start_serial_thread(self):
        def read_serial():
            try:
                # Ganti COM port jika perlu (Windows: "COM3", Linux: "/dev/ttyUSB0")
                ser = serial.Serial("/dev/ttyACM0", 9600, timeout=1)
                while True:
                    line = ser.readline().decode(errors="ignore").strip()
                    if line.startswith("ECG:"):
                        try:
                            parts = line.split(',')
                            ecg = float(parts[0].split(':')[1])
                            spo2 = float(parts[1].split(':')[1])
                            resp = float(parts[2].split(':')[1])
                            self.serial_data.data_received.emit(ecg, spo2, resp)
                        except:
                            continue
            except serial.SerialException:
                print("Gagal membuka port serial.")

        thread = threading.Thread(target=read_serial, daemon=True)
        thread.start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PatientMonitor()
    window.show()
    sys.exit(app.exec_())
