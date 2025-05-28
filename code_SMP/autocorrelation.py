import numpy as np
import matplotlib.pyplot as plt
import pickle
from pathlib import Path
from code_SMP.readSMP import load_all_smp_profiles


def calc_autocorrelations(smp_profiles, normalize=True):
    autocorr_results = {}
    for name, df in smp_profiles.items():
        signal = df["force"].values
        # signal = signal - np.mean(signal) # Mittelwertzentrierung
        autocorr = np.correlate(signal, signal, mode='full')
        lags = np.arange(-len(signal) + 1, len(signal))
        if normalize == True:
            autocorr /= np.max(autocorr)
        autocorr_results[name] = (lags, autocorr)
    return autocorr_results


def plot_autocorrelation(lags, autocorr, title="Autocorrelation", save=False, filename=None, target_dir=Path("output/autocorrelation")):
    plt.figure(figsize=(8, 5))
    plt.plot(lags, autocorr)
    plt.title(title)
    plt.xlabel("Lag")
    plt.ylabel("Autocorrelation value")
    plt.grid()

    if save:
        target_dir.mkdir(parents=True, exist_ok=True)
        plt.savefig(target_dir / f"{filename}.png")
        plt.savefig(target_dir / f"{filename}.pdf", format="pdf", bbox_inches="tight")
    else:
        plt.show()
    plt.close()


if __name__ == "__main__":
    smp_profiles = load_all_smp_profiles()
    output_file = Path("output/autocorrelation/autocorr_results.pkl")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    #autocorr_dict = calc_autocorrelations(smp_profiles)

    # save dict for later to don't have to run def again (too long)
    #with open(output_file, "wb") as f:
    #    pickle.dump(autocorr_dict, f)

    # load dict again
    with output_file.open("rb") as f:
        autocorr_dict = pickle.load(f)

    #plots for autocorrelation
    for name, (lags, autocorr) in autocorr_dict.items():
        plot_autocorrelation(lags, autocorr, title=f"Autocorrelation: {name}", save=True, filename=f"autocorr_{name}")