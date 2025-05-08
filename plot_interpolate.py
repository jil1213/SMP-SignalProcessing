import matplotlib.pyplot as plt
import numpy as np

from pathlib import Path
from readSMP import load_all_smp_profiles
from offset import align_profiles


#mins interpolate to find trend 
#also for temperature measurements (89)
