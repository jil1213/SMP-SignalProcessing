import numpy as np
import matplotlib.pyplot as plt

from pathlib import Path
from readSMP import load_all_smp_profiles

# calculate Fast Fourier Transform
def calculate_fourier_transform(smp_profiles, sampling_rate):
    fft_results = {}
    for name, df in smp_profiles.items():
        signal = df["force"].values
        n = len(signal)
        fft_result = np.fft.fft(signal)
        frequencies = np.fft.fftfreq(n, d=1/sampling_rate)
        half_n = n // 2
        fft_results[name] = (frequencies[:half_n], np.abs(fft_result[:half_n]) / n)
    return fft_results


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
    fft_dict = calculate_fourier_transform(smp_profiles, sampling_rate)

    for name, (freqs, mags) in fft_dict.items():
        plot_fft(freqs, mags, title=f"FFT von {name}", save=True, filename=f"fft_{name}")