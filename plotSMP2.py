import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path
from readSMP import plot_profiles, load_all_smp_profiles
from offset import get_offset, overlay_profiles
from plotSMP import bulid_pairs, plot_pairs

#new visualizations for comparison of profiles
target_dir = Path("output/visualizations_new")
smp_profiles = load_all_smp_profiles()

#means of eac 5 measurements of one velocity

#comparing 8 with 20