import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from tkinter import Tk
from tkinter.filedialog import askopenfilename

# === 1. Dialog Pilih File ===
Tk().withdraw()
filename = askopenfilename(initialdir=r"C:\Users\user\Downloads", 
                           filetypes=[("  ", "*.csv")])


# === 2. Baca CSV ===
df = pd.read_csv(filename)
pressure = df['mmHg'].values

# === 3. Cari puncak inflasi (mulai deflasi) ===
peak_idx = np.argmax(pressure)
deflation_data = pressure[peak_idx:]

# === 4. Moving Average (filter noise) ===
def moving_average(x, w=5):
    return np.convolve(x, np.ones(w)/w, mode='valid')

smoothed = moving_average(deflation_data, w=5)

# === 5. Deteksi puncak osilasi ===
peaks, _ = find_peaks(smoothed, distance=5)
peak_values = smoothed[peaks]

# === 6. Hitung MAP, Sistolik, Diastolik ===
max_peak_index = peaks[np.argmax(peak_values)]
MAP_value = smoothed[max_peak_index]
threshold = 0.3 * np.max(peak_values)
valid_peaks = peaks[peak_values > threshold]

systolic_value = smoothed[valid_peaks[1]]
diastolic_value = smoothed[valid_peaks[-19]]

# === 7. Plot Grafik ===
plt.figure(figsize=(12,6))
plt.plot(smoothed, label='Tekanan (smoothed)', color='blue')
plt.plot(peaks, smoothed[peaks], "rx", label="Puncak Osilasi")
plt.axhline(y=MAP_value, color='green', linestyle='--', label=f'MAP ~ {MAP_value:.1f} mmHg')
plt.axhline(y=systolic_value, color='red', linestyle='--', label=f'Sistolik ~ {systolic_value:.1f} mmHg')
plt.axhline(y=diastolic_value, color='purple', linestyle='--', label=f'Diastolik ~ {diastolic_value:.1f} mmHg')
plt.title("Analisis Tekanan Darah (Deflasi)")
plt.xlabel("Sample Index")
plt.ylabel("Tekanan (mmHg)")
plt.legend()
plt.grid(True)
plt.show()

# === 8. Print Hasil ===
print(f"Sistolik  : {systolic_value:.1f} mmHg")
print(f"Diastolik : {diastolic_value:.1f} mmHg")
print(f"MAP       : {MAP_value:.1f} mmHg")
