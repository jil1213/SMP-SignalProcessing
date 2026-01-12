# SMP-SignalProcessing

This repository contains all scripts used for my master's thesis.

## Code_automated_correlation

This folder contains free-standing code -a fully automated pipeline- to process, analyze, and average SnowMicroPen (SMP) profiles based on similarity. It enables aligning, comparing, grouping, and averaging profiles using cosine similarity and cross-correlation methods.

### Data Structure

All data must be stored in the folder `raw_data`, which should contain one subfolder **per day** (or measurement set).
Each subfolder contains the `.PNT` files (SMP profiles) for that specific measurement day (or spcific measurement set).

**Example structure:**

```text
raw_data/
├── 20250131/
│ ├── S45M0001.PNT
│ └── ...
├── 20250202/
│ ├── S45M0020.PNT
│ └── ...
```

The pipeline processes each subfolder sequentially, day by day.
Other data (e.g., .xlsx, .xml files) are optional and not required for the pipeline. Only when used in combination with the density code.

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

`analyze_day`: To use the pipeline (processing similarity, groups and pair finding) for one day. It loads the profiles, computes the similarity matrix, identifies the best reference profile,
generates similarity-based profile pairs, and extracts groups of profiles that exceed a defined similarity threshold.
Returns a structured dictionary containing:

```text
- day (str)
- smp_profiles (dict)
- similarity_matrix (np.ndarray)
- labels (list)
- threshold (float)
- reference_result (tuple): (ref_name, remaining, mean_score)
- pairs (list): [(a, b, score)]
- groups (list): list of group dicts {'labels': [...], 'matrix': ...}
```

This function ensures consistent data processing across multiple modules (e.g., grouping, mean calculation, density analysis).

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

### new_surface_detection.py

This script contains the surface detection method newly developed in this work. Please note: This is the same function as in code_SMP/surface_detection, which has simply been copied so that the code_automated_correlation subfolder can be used as standalone code.

## Code_density

This module computes snow density profiles from a SMP mean profile using the **Löwe et al. (2012)** shot-noise model together with the **Calonne & Richter (2020)** density parameterization, implemented in the snowmicropyn python package.
It makes use of the previously developed _automated averaging pipeline_ located in `code_automated_correlation` to compute the SMP mean profile used as input for density calculation.

**`calculate_density_profile`**
Computes a density profile from SMP force data using Löwe2012 + CalonneRichter2020.

**`plot_density`**
Plots individual, paired, or averaged density profiles and saves them as `.svg`.

**`load_manual_density`**
Imports manual density data from CAAML-XML, SnowPro sensor (`.xlsx`), and density cutter measurements, including slope-angle correction. For comparison between smp computed density and traditional methods

**Daily processing (`__main__`)**
Runs the automated averaging pipeline for each day to generate mean profiles,
Computes density for reference profiles, individual profiles, and group means,
Generates comparison plots

All outputs are saved in:
`output/density/<day>/`
