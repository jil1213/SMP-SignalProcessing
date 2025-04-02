# Visualization of density field measurements
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path  # for OS-independent path handling

target_dir = Path("output/visualizations")

def load_csv(file_name):
    df = pd.read_excel(file_name)
    # Drop rows with NaN values in snowdepth or mean
    df = df[["snowdepth", "mean"]].dropna()
    # Ensure numeric conversion
    df["snowdepth"] = pd.to_numeric(df["snowdepth"], errors="coerce")
    df["mean"] = pd.to_numeric(df["mean"], errors="coerce")
    # Drop any remaining NaN after conversion
    df = df.dropna()
    snowdepth = df["snowdepth"]
    mean = df["mean"]
    return snowdepth, mean

def plot_density(snowdepth, mean, snowdepthslf, meanslf, cutter_name, slf_name):
    plt.figure(figsize=(8, 5))
    plt.scatter(snowdepth, mean, color='blue')
    plt.plot(snowdepth, mean, color='blue', label='Density Cutter')
    plt.scatter(snowdepthslf, meanslf, color='red')
    plt.plot(snowdepthslf, meanslf, color='red', label='Density SLF')
    plt.xlabel("Snowdepth (cm)")
    plt.ylabel("Density (kg/m^3)")

    title = f"Density over Snowdepth ({cutter_name} vs {slf_name})"
    plt.title(title)
    plt.legend()
    plt.grid()

    filename = f"density_{cutter_name}_vs_{slf_name}.png"
    plt.savefig(target_dir / filename)
    plt.close()

# Pair of files for each day
file_pairs = [
    ("data/01-31-densitycutter.xlsx", "data/01-31-densitySLF.xlsx"),
    ("data/03-21-densitycutter.xlsx", "data/03-21-densitySLF.xlsx"),]

for cutter_file, slf_file in file_pairs:
    snowdepth, mean = load_csv(cutter_file)
    snowdepthslf, meanslf = load_csv(slf_file)

    cutter_name = Path(cutter_file).stem # Extract file names without extensions and paths
    slf_name = Path(slf_file).stem

    plot_density(snowdepth, mean, snowdepthslf, meanslf, cutter_name, slf_name)
