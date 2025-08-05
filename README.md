# SMP-SignalProcessing

This repository contains all scripts used for my master's thesis.
Folder `data` stores the measured data and converted files

## Code_automated_correlation

This folder contains free-standing code -a fully automated pipeline- to process, analyze, and average SnowMicroPen (SMP) profiles based on similarity. It allows for aligning, comparing, grouping, and averaging profiles using cosine similarity and cross-correlation methods.

### Data Structure

All data must be stored in the folder `raw_data`, which should contain one subfolder **per day**.  
Each subfolder contains the `.PNT` files (SMP profiles) for that specific measurement day.

**Example structure:**
raw_data/

├── 20250131/

│ ├── S45M0001.PNT

│ └── ...

├── 20250202/

│ ├── S45M0020.PNT

│ └── ...

The pipeline processes each subfolder sequentially, day by day.

### Run the Full Pipeline

You can execute the entire pipeline with the following command:

```bash
python -m code_automated_correlation.d_automated_mean
```

Each script can also be executed individually. Necessary previous steps (e.g. trimming, alignment) will be automatically performed within each script if needed.

a)Load and trim profiles, detect surface and ground, compute cross-correlation and align all profile pairs.-> `a_automated_processing.py`

b) The similarity of all profiles to each others is calculated and presented in a Similarity matrix. -> `b_automated_similarity.py`

c) To find matching profiles a threshold is applied and groups or pairs are build -> `c_automated_correlation.py`

d) The mean and std of groups/pairs is calculated and plotted -> `d_automated_mean.py`

### a_automated_processing

Load all smp profiles of subfolders with `load_profiles`
and cut them between surface (own method to find surface value and cut values before) and ground (detected by snowmicropyn). Save all profiles in a dict.

Alignment functions are save in this script: Used to align to profiles with crosscorrelation (finds lag(=displacement value) of two profiles to get the best correlation for them)
`get_offset` finds lag by correlate two profiles
`align_profiles` Shifts profiles by lag to get best alignment

Run script with command:

```bash
python -m code_automated_correlation.a_automated_processing
```

### b_automated_similarity.py

Cosine similarity matrix is calculated in `compute_aligned_similarity_matrix`. To get the highest possible similarity, profiles are aligned with crosscorrelation first! Alignment functions are part of `a_automated_processing.py`
After alignment cosine similarity as similarity value is calculated.

`cosine = np.dot(df1, df2) / (np.linalg.norm(df1) * np.linalg.norm(df2))`

Similarity Matrix of one day (=Subfolder) can be plotted.

Run script with command:

```bash
python -m code_automated_correlation.b_automated_similarity
```

### c_automated_grouping.py

This script analyzes structural similarity between SMP profiles based on cosine similarity. It includes three core methods:

`find_reference_profile`: Automatically selects the most representative profile in a group by optimizing for number of similar neighbors, their minimum similarity, and their mean similarity.

`find_highest_similarity_pairs`: Identifies unique pairs of profiles with the highest mutual similarity.

`find_all_threshold_groups` : Constructs groups of profiles in which all members exceed a specified similarity threshold to one another.

Run script with command:

```bash
python -m code_automated_correlation.c_automated_grouping
```

### d_automated_mean.py

Can use output of `c_automated_grouping.py` to compute and visualize mean of group-wise aligned profiles.
Run script with command:

```bash
python -m code_automated_correlation.d_automated_mean
```

## Code_density

...under construction...

## Surface_detection tuning + evaluation

### surfacedetection_tuning

Surface detetection method of `code_SMP.detect_surface.py` is tuned on testdata.

### surfacedetection_evaluate

Contains script and outputs for new surface detection method for all profiles of [WFJ Daily SMP Dataset](https://envidat.ch/#/metadata/wfj_dailysmp) with quality flag = 1 (2815 profiles). Error metrics are computed.

## Code_json

### profiles_parameters.py

contains listed labels for snow grain type and according colour sheme for plotting. Can be used to align an existing lawis snowprofiles to the correct snow grain tpe labels and colours.

### readjson.py

can be used to read an .json snowprofiles (for exampe exported from LAWIS). And extracts all the relevant information for later use.
Can plot the colour scheme and hardness profile of manual snowprofiles.

### alignSMPtoJson.py

can be used to align a SMP .pnt profile to the related json manual snow profile. Also takes into account the angle correction between the profiles and stores the snow types in the graphical output with the color according to the standard (Fierz et al. 2009) and gives the hardness of the layer as dashed hardness index.

## Code_SMP

### autocorrelation.py

Autocorrelation of single profiles

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
