# SMP-SignalProcessing

This repository contains all scripts used for my master's thesis.
Folder `data` stores the measured data and converted files

## Code_density

...under construction...

## Code_json

### profiles_parameters.py

contains listed labels for snow grain type and according colour sheme for plotting. Can be aesiliy used to align an existing lawis snowprofiles to the correct snow grain tpe labels and colours.

### readjson.py

can be used to read an .json snowprofiles (for exampe exported from LAWIS). And extracts all the relevant information for later use.
Can plot the colour scheme and hardness profile of manual snowprofiles.

### alignSMPtoJson.py

can be used to align a SMP .pnt profile to the related json manual snow profile. Also takes into account the angle correction between the profiles and stores the snow types in the graphical output with the color according to the standard (Fierz et al 2009) and gives the hardness of the layer as dashed hardness index.

## Code_SMP

### autocorrelation.py

Autocorrelation of single profiles

### automated_correlation.py

This script analyzes structural similarity between SMP profiles based on cosine similarity. It includes three core methods:

    `find_reference_profile`: Automatically selects the most representative profile in a group by optimizing for number of similar neighbors, their minimum similarity, and their mean similarity.

    `find_highest_similarity_pairs`: Identifies unique pairs of profiles with the highest mutual similarity.

    `find_all_threshold_groups` : Constructs groups of profiles in which all members exceed a specified similarity threshold to one another.

### automated_mean.py

Can use output of `automated_correlation.py` to compute and visualize mean of group-wise aligned profiles.

### detect_ground.py

Ground detection for csv smp profiles with same method as used in snowmicropyn preprocessing (5Sigma rule)

### detect_surface.py

Surface detection of smp profiles with logarithmic force gradient. Currently under construction

### detrending.py

This script compares two methods for removing trends from SMP force profiles:
(1) interpolation-based drift subtraction using minima, and
(2) linear detrending following the method by Proksch et al. (2015). (not sure if implemented right)
The results are visualized to evaluate differences between the detrending techniques.
It is not used further yet...

### offset.py

functions to calculate offset of two different profiles with crosscorrelation. Outputs are stored in folder `output/cross_correlations`
Alignment of two or more profiles can be done and aligned profiles can be stored as csv.
! Attention: Lag wich is used to align two profiules, is always understood from smaller profile name to higher profile name (e.g S45M1058 to S45M1060)! That's important for right direction of alignment with lag!

### pairs.py

Stores predefined profile pairing, used for similarity scores.

### readSMP.py

can be used to read .pnt SMP files. They can be converted into a csv file without any reduction of datapoints
SMP files can also be stored in dataframes and are used in further steps for visualization and signal processing

New: also possible to read csv SMP files (e.g already aligned profiles)

### similarity_mean.py

Can compare means of profiles with similiarity code. Has been overtaken by automatic procedure in `automated_mean.py`

### similarity.py

This script evaluates the similarity between SMP profiles using cosine similarity.
It supports various predefined profile pairings (e.g. fixed pairs, adjacent profiles, increasing spacing) and computes pairwise similarity scores after alignment via cross-correlation.
The results include:

    Similarity plots (bar charts and regression plots)

    Correlation matrices for full days and velocities

    Offset caching to avoid redundant computations

All results are saved to `output/similarity_scores`.

### temperaturetrends.py

Minima Interpolation of two velocities can be compared and extracted to get information about temperature trend scale of diffent velocities

## code_visualizations

### FFT.py

Fourier Transformation computed with the Fast Fourier Transformation and PSD (Leistungsdichtespektrum) can be plotted.

### plot_interpolate.py

Interploation of Minimas with a low pass filtered spline. This result can be used to investigate temperature trends

### plot_logarithm.py

Logratihm scale for single output plots.

### plot_mean.py

Mean of 5 profiles of one velocitiy can be plotted with standard deviation. Comparing means is also possible

### plotSMP.py

can be used to visualize simple smp profiles. Outputs are stored in folder `output/visualizations`

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
