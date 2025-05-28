# SMP-SignalProcessing

This repository contains all scripts used for my master's thesis.
Folder `data` stores the measured data and converted files

## Code_json

### profiles_parameters.py

contains listed labels for snow grain type and according colour sheme for plotting. Can be aesiliy used to align an existing lawis snowprofiles to the correct snow grain tpe labels and colours.

### readjson.py

can be used to read an .json snowprofiles (for exampe exported from LAWIS). And extracts all the relevant information for later use.
Can plot the colour scheme and hardness profile of manual snowprofiles.

## Code_SMP

### autocorrelation.py

Autocorrelation of single profiles

### detect_ground.py

Ground detection for csv smp profiles with same method as used in snowmicropyn preprocessing (5Sigma rule)

### detect_surface.py

Surface detection of smp profiles with logarithmic force gradient. Currently under construction

### offset.py

functions to calculate offset of two different profiles with crosscorrelation. Outputs are stored in folder `output/cross_correlations`
Alignment of two or more profiles can be done and aligned profiles can be stored as csv.

### readSMP.py

can be used to read .pnt SMP files. They can be converted into a csv file without any reduction of datapoints
SMP files can also be stored in dataframes and are used in further steps for visualization and signal processing

New: also possible to read csv SMP files (e.g already aligned profiles)

### temperaturetrends.py

Minima Interpolation of two velocities can be compared and extracted to get information about temperature trend scale of diffent velocities

## code_visualizations

### plotSMP.py

can be used to visualize simple smp profiles. Outputs are stored in folder `output/visualizations`

### plot_interpolate.py

Interploation of Minimas with a low pass filtered spline. This result can be used to investigate temperature trends

### plot_mean.py

Mean of 5 profiles of one velocitiy can be plotted with standard deviation. Comparing means is also possible

### plot_logarithm.py

Logratihm scale for single output plots.

### FFT.py

Fourier Transformation computed with the Fast Fourier Transformation and PSD (Leistungsdichtespektrum) can be plotted.

### visualizationsdensity.py

can be used to import and visualize density measuremnts stored in csv files

## data

Contains input data

### aligned_first

Contains SMP profiles as csv aligned with crosscorrelation to `the first profile of the day`. Can be used as input data for later calculations without calculate crosscorr again (very time consuming!)

### aligned_pairs

Contains SMP profiles as csv aligned with crosscorrelation `velocity pairs`. Can be used as input data for later calculations without calculate crosscorr again (very time consuming!)

### smp_profiles

.pnt profiles original SMP Profiles

### smp_profiles_csv

csv files converted from .pnt
