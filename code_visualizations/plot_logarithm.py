import matplotlib.pyplot as plt

from pathlib import Path
from code_SMP.readSMP import load_all_smp_profiles

def logarithm(smp_profiles, save=False, target_dir=Path("output/logarithm")):
    target_dir.mkdir(parents=True, exist_ok=True)

    for name, df in smp_profiles.items():
        distance = df["distance"].values
        force = df["force"].values

        # logarithmic force plot
        plt.figure(figsize=(8, 5))
        plt.plot(distance, force)
        plt.yscale('log')
        plt.xlabel("Distance (mm)")
        plt.ylabel("Force (log N)")
        plt.title(f"Logarithmic Force Plot: {name}")
        plt.grid(True, which="both", ls="--")
        if save:
            plt.savefig((target_dir / f"{name}_logY").with_suffix(".png"))
        else:
            plt.show()
        plt.close()

        # Double logarithmic plot
        # filter out negative values 
        mask = (distance > 0) & (force > 0)
        plt.figure(figsize=(8, 5))
        plt.plot(distance[mask], force[mask])
        plt.xscale('log')
        plt.yscale('log')
        plt.xlabel("Distance (log mm)")
        plt.ylabel("Force (log N)")
        plt.title(f"Double Logarithmic Plot: {name}")
        plt.grid(True, which="both", ls="--")
        if save:
            plt.savefig((target_dir / f"{name}_loglog").with_suffix(".png"))
        else:
            plt.show()
        plt.close()

if __name__ == "__main__":
    smp_profiles = load_all_smp_profiles()
    logarithm(smp_profiles, save=True)
