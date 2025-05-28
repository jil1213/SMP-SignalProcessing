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

    # Standardabweichung berechnen
    df["std"] = df[["density1", "density2", "density3", "density4"]].std(axis=1)

    # Fehlerbalken: symmetrisch mit Standardabweichung
    df["err"] = df["std"]

    return df


def plot_density(df_cutter, df_slf, cutter_name, slf_name):
    plt.figure(figsize=(8, 5))

    # Cutter
    plt.errorbar(df_cutter["snowdepth"], df_cutter["mean"],
                yerr=df_cutter["err"],
                fmt='o-', color='blue', capsize=4, label='Density Cutter with std')

    # SLF
    plt.errorbar(df_slf["snowdepth"], df_slf["mean"],
                yerr=df_slf["err"],
                fmt='o-', color='red', capsize=4, label='Density SLF with std')


    plt.xlabel("Snowdepth (cm)")
    plt.ylabel("Density (kg/m^3)")
    title = f"Density over Snowdepth ({cutter_name} vs {slf_name})"
    plt.title(title)
    plt.legend()
    plt.grid()

    filename = f"density_{cutter_name}_vs_{slf_name}.png"
    plt.savefig(target_dir / filename)
    plt.close()
    return

# Pair of files for each day
file_pairs = [
    ("data/01-31-densitycutter.xlsx", "data/01-31-densitySLF.xlsx"),
    ("data/03-21-densitycutter.xlsx", "data/03-21-densitySLF.xlsx"),]

for cutter_file, slf_file in file_pairs:
    df_cutter = load_csv(cutter_file)
    df_slf = load_csv(slf_file)

    cutter_name = Path(cutter_file).stem # Extract file names without extensions and paths
    slf_name = Path(slf_file).stem

    plot_density(df_cutter, df_slf, cutter_name, slf_name)
