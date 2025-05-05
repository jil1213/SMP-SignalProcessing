# Visualization of density field measurements
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path  # for OS-independent path handling

target_dir = Path("output/visualizations")

def load_csv(file_name):
    df = pd.read_excel(file_name)
    # take only relevant rows
    df = df[["snowdepth", "density1","density2","density3","density4"]]
    # Ensure numeric conversion
    df["snowdepth"] = pd.to_numeric(df["snowdepth"], errors="coerce")
    df["density1"] = pd.to_numeric(df["density1"], errors="coerce")
    df["density2"] = pd.to_numeric(df["density2"], errors="coerce")
    df["density3"] = pd.to_numeric(df["density3"], errors="coerce")
    df["density4"] = pd.to_numeric(df["density4"], errors="coerce")

    #Means
    df["mean"] = df[["density1", "density2", "density3", "density4"]].mean(axis=1)
    #delete rows were man has a NaN value
    df = df.dropna(subset=["mean"])

    #Min and max values for density
    df["min"] = df[["density1", "density2", "density3", "density4"]].min(axis=1)
    df["max"] = df[["density1", "density2", "density3", "density4"]].max(axis=1)

    mean = df["mean"]
    snowdepth = df["snowdepth"]
    return snowdepth, mean

def plot_density(snowdepth, mean, snowdepthslf, meanslf, cutter_name, slf_name):
    plt.figure(figsize=(8, 5))

    #plot density cutter
    plt.scatter(snowdepth, mean, color='blue')
    plt.plot(snowdepth, mean, color='blue', label='Density Cutter')

    #plot density SLF - mostly we have only one value, so only few error bars
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
