import numpy as np
import matplotlib.pyplot as plt

from scipy.signal import welch
from pathlib import Path
from code_SMP.readSMP import load_all_smp_profiles

# calculate Fast Fourier Transform
def calc_fourier_transform(smp_profiles, sampling_rate):
    fft_results = {}
    for name, df in smp_profiles.items():
        signal = df["force"].values
        n = len(signal)
        fft_result = np.fft.fft(signal)
        frequencies = np.fft.fftfreq(n, d=1/sampling_rate)
        half_n = n // 2
        fft_results[name] = (frequencies[:half_n], np.abs(fft_result[:half_n]) / n)
    return fft_results

#Leistungsspektrumdichte (PSD) berechnen
def calc_psd(smp_profiles, sampling_rate):

    psd_results = {}
    for name, df in smp_profiles.items():
        signal = df["force"].values
        n = len(signal)

        fft = np.fft.fft(signal)
        psd = (np.abs(fft) ** 2) / (n * sampling_rate)
        freqs = np.fft.fftfreq(n, d=1/sampling_rate)

        freqs, psd = welch(signal, fs=sampling_rate, nperseg=1024) #Segmentlänge für Welch-Methode
        psd_results[name] = (freqs[:n // 2], psd[:n // 2])
    return psd_results

# Welch method
def calc_welch(smp_profiles, sampling_rate):

    welch_results = {}
    for name, df in smp_profiles.items():
        signal = df["force"].values
        freqs, welch_values = welch(signal, fs=sampling_rate, nperseg=1024) #Segmentlänge für Welch-Methode
        welch_results[name] = (freqs, welch_values)
    return welch_results

def plot_fft(frequencies, magnitudes, title="FFT", save=False, filename=None, target_dir=Path("output/fft")):

    plt.figure(figsize=(8, 5))
    plt.plot(frequencies, magnitudes)
    plt.title(title)
    plt.xlabel("Frequenz (Hz)")
    plt.ylabel("Magnitude")
    plt.grid()
    if save==True:
        target_dir.mkdir(parents=True, exist_ok=True)
        plt.savefig(target_dir / f"{filename}.png")
        #plt.savefig(target_dir / f"{filename}.pdf", format="pdf", bbox_inches="tight")
    else:
        plt.show()
    plt.close()


if __name__ == "__main__":
    smp_profiles = load_all_smp_profiles()
    #convert spatial resolution into sampling rate
    res = next(iter(smp_profiles.values())).attrs["spatial_resolution"]
    sampling_rate = 1 / res  # spatial resolution is in mm, convert to Hz
    fft_dict = calc_fourier_transform(smp_profiles, sampling_rate)
    psd_dict = calc_psd(smp_profiles, sampling_rate)
    welch_dict = calc_welch(smp_profiles, sampling_rate)

    for name, (freqs, mags) in fft_dict.items():
        plot_fft(freqs, mags, title=f"FFT of {name}", save=True, filename=f"fft_{name}")
    for name, (freqs, psd) in psd_dict.items():
        #plot psd
        plot_fft(freqs, psd, title=f"PSD of {name}", save=True, filename=f"psd_{name}")

    for name, (freqs, welch) in welch_dict.items():
        plot_fft(freqs, welch, title=f"PSD (Welch) of {name}", save=True, filename=f"welch_{name}")