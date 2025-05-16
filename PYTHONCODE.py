#ok untuk ekg dan menu awal
import sys
import numpy as np
import datetime
import psutil
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QDialog, QFormLayout
)
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg

class PatientMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Patient Monitor")
        self.resize(1800, 750)
        self.setStyleSheet("background-color: black;")

        self.buffer_size = 1000
        self.timer_interval = 10  # ms
        self.x = np.linspace(0, self.buffer_size * self.timer_interval / 1000.0, self.buffer_size)
        self.index = 0
        self.phase = 0.0
        self.fase_aktif = 1

        # Data arrays
        self.ecg_data = np.zeros(self.buffer_size)
        self.spo2_data = np.zeros(self.buffer_size)
        self.resp_data = np.zeros(self.buffer_size)

        main_layout = QHBoxLayout()
        graph_layout = QVBoxLayout()
        graph_layout.setSpacing(0)

        self.ecg_plot, self.ecg_curve, self.ecg_vline = self.create_realtime_plot("ECG", "lime", self.ecg_data, (-1.5, 1.5))
        self.spo2_plot, self.spo2_curve, self.spo2_vline = self.create_realtime_plot("SpO₂", "red", self.spo2_data, (-0.2, 1.2))
        self.resp_plot, self.resp_curve, self.resp_vline = self.create_realtime_plot("RESP", "yellow", self.resp_data, (-0.5, 1.5))

        graph_layout.addWidget(self.ecg_plot)
        graph_layout.addWidget(self.create_spacer())
        graph_layout.addWidget(self.spo2_plot)
        graph_layout.addWidget(self.create_spacer())
        graph_layout.addWidget(self.resp_plot)
        graph_layout.addStretch()

        # === Panel Info Kanan ===
        info_layout = self.create_info_panel()

        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setLineWidth(1)
        line.setStyleSheet("border: none; border-left: 2px dashed gray;")

        main_layout.addLayout(graph_layout, 4)
        main_layout.addWidget(line)
        main_layout.addLayout(info_layout, 1)

        self.setLayout(main_layout)

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_waveforms)
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(self.timer_interval)

    def create_realtime_plot(self, title, color, data_array, y_range):
        container = QFrame()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

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

    def create_spacer(self):
        spacer = QFrame()
        spacer.setFixedHeight(95)
        spacer.setStyleSheet("background-color: black; border-top: 1px dashed black;")
        return spacer

    def create_info_panel(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Top bar: datetime & battery
        top_layout = QHBoxLayout()
        top_layout.addStretch()
        self.label_datetime = QLabel("2025-05-16 12:00:00")
        self.label_datetime.setStyleSheet("color: gray; font-size: 12px;")
        self.label_battery = QLabel("Battery: 80%")
        self.label_battery.setStyleSheet("color: gray; font-size: 12px;")
        top_layout.addWidget(self.label_datetime)
        top_layout.addSpacing(10)
        top_layout.addWidget(self.label_battery)
        layout.addLayout(top_layout)

        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: gray;")
        layout.addSpacing(10)
        layout.addWidget(separator)

        layout.addWidget(self.create_data_row("HR", "75", "bpm", "lime", 80))
        layout.addWidget(self.create_data_row("SpO₂", "97%", "", "red", 50))
        layout.addWidget(self.create_data_row("RESP", "19", "rpm", "yellow", 70))
        layout.addWidget(self.create_data_row("TEMP", "36.8°C", "", "cyan", 50))
        layout.addWidget(self.create_data_row("NIBP", "118/78", "mmHg", "orange", 50))

        # Menu buttons
        menu_layout = QHBoxLayout()
        menu_layout.addStretch()

        menu_btn = QPushButton("Setting")
        menu_btn.setStyleSheet("background-color: #007bff; color: white; padding: 10px;")
        menu_btn.clicked.connect(self.show_menu)
        menu_layout.addWidget(menu_btn)

        settings_btn = QPushButton("Start NIBP")
        settings_btn.setStyleSheet("background-color: #28a745; color: white; padding: 10px;")
        #settings_btn.clicked.connect(self.show_settings)
        menu_layout.addWidget(settings_btn)

        layout.addLayout(menu_layout)
        return layout

    def create_data_row(self, title, value, unit, color, size):
        container = QFrame()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        row = QHBoxLayout()
        row.addWidget(QLabel(f"<span style='color:{color}; font-size:25px'>{title}</span>"))
        row.addStretch()
        row.addWidget(QLabel(f"<span style='color:{color}; font-size:19px'>{unit}</span>"))
        layout.addLayout(row)

        val = QLabel(value)
        val.setStyleSheet(f"color: {color}; font-size: {size}px; font-weight: bold;")
        val.setAlignment(Qt.AlignCenter)
        layout.addWidget(val)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: gray;")
        layout.addWidget(sep)

        container.setLayout(layout)
        return container

    def update_datetime(self):
        now = datetime.datetime.now()
        self.label_datetime.setText(now.strftime("%Y-%m-%d %H:%M:%S"))

    def show_menu(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Menu")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Menu Options"))
        dialog.setLayout(layout)
        dialog.exec_()

    def show_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        form = QFormLayout()
        form.addRow("Brightness", QLabel("Adjust brightness"))
        form.addRow("Volume", QLabel("Adjust volume"))
        dialog.setLayout(form)
        dialog.exec_()

    def update_waveforms(self):
        self.phase += self.timer_interval / 1000.0

        ecg_val = np.sin(2 * np.pi * 1 * self.phase) * np.exp(-5 * (self.phase % 1))
        spo2_val = 0.8 * np.exp(-((self.phase * 2) % 1 - 0.2) ** 2 / 0.01)
        resp_val = 1.0 * (np.sin(2 * np.pi * 0.2 * self.phase) > 0.5)

        self.ecg_data[self.index] = ecg_val
        self.spo2_data[self.index] = spo2_val
        self.resp_data[self.index] = resp_val

        self.ecg_curve.setData(self.x, self.ecg_data)
        self.spo2_curve.setData(self.x, self.spo2_data)
        self.resp_curve.setData(self.x, self.resp_data)

        vpos = self.x[self.index]
        self.ecg_vline.setPos(vpos)
        self.spo2_vline.setPos(vpos)
        self.resp_vline.setPos(vpos)

        self.index += 1
        if self.index >= self.buffer_size:
            self.index = 0
            self.fase_aktif = 2 if self.fase_aktif == 1 else 1

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PatientMonitor()
    window.show()
    sys.exit(app.exec_())
