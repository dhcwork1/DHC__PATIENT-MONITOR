import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import datetime
import csv

# --- Konfigurasi Serial Arduino ---
port = 'COM10'        # Ganti sesuai port Arduino kamu
baudrate = 9600
ser = serial.Serial(port, baudrate, timeout=1)

# --- Data Penyimpanan ---
pressures = []             # Daftar nilai tekanan (instan)
smoothed = []              # Daftar nilai tekanan rata-rata
timestamps = []            # Waktu pembacaan

# --- File CSV Otomatis ---
filename = f"pressure_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
csv_file = open(filename, mode='w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(['Timestamp', 'Pressure_mmHg', 'Smoothed_mmHg'])

# --- Setup Grafik ---
fig, ax = plt.subplots()
line1, = ax.plot([], [], label='Pressure (mmHg)')
line2, = ax.plot([], [], label='Smoothed', linestyle='--')
ax.set_title('Grafik Tekanan (mmHg)')
ax.set_xlabel('Waktu')
ax.set_ylabel('Tekanan (mmHg)')
ax.legend()
ax.grid()

def update(frame):
    line = ser.readline().decode().strip()
    if "Pressure (mmHg):" in line:
        try:
            parts = line.split('|')
            raw_val = float(parts[0].split(':')[1].strip())
            smooth_val = float(parts[1].split(':')[1].strip())
            timestamp = datetime.now().strftime('%H:%M:%S')

            pressures.append(raw_val)
            smoothed.append(smooth_val)
            timestamps.append(timestamp)

            # Simpan ke CSV
            csv_writer.writerow([timestamp, raw_val, smooth_val])

            # Batasi 100 data terakhir untuk tampilan
            pressures_display = pressures[-100:]
            smoothed_display = smoothed[-100:]
            x_display = range(len(pressures_display))

            line1.set_data(x_display, pressures_display)
            line2.set_data(x_display, smoothed_display)
            ax.relim()
            ax.autoscale_view()

        except Exception as e:
            print(f"Error parsing: {e}")

    return line1, line2

ani = animation.FuncAnimation(fig, update, interval=200)
plt.tight_layout()
plt.show()

# Tutup file jika jendela ditutup
csv_file.close()
