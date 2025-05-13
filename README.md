# SMP-SignalProcessing

This repository contains all scripts used for my master's thesis.
Folder `data` stores the measured data and converted files

## visualizationsdensity

can be used to import and visualize density measuremnts stored in csv files

## readSMP

can be used to read .pnt SMP files. They can be converted into a csv file without any reduction of datapoints
SMP files can also be stored in dataframes and are used in further steps for visualization and signal processing

New: also possible to read csv SMP files (e.g already aligned profiles)

## plotSMP

can be used to visualize simple smp profiles. Outputs are stored in folder `output/visualizations`

## offset

functions to calculate offset of two different profiles with crosscorrelation. Outputs are stored in folder `output/cross_correlations`
Alignment of two or more profiles can be done and aligned profiles can be stored as csv.

## plot_interpolate

Interploation of Minimas with a low pass filtered spline. This result can be used to investigate temperature trends

## temperaturetrends

Minima Interpolation of two velocities can be compared and extracted to get information about temperature trend scale of diffent velocities

## plot_mean

Mean of 5 profiles of one velocitiy can be plotted with standard deviation. Comparing means is also possible

## plot_logarithm

Logratihm scale for single output plots.

## autocorrelation

Autocorrelation of single profiles

## FFT

Fourier Transformation computed with the Fast Fourier Transformation and PSD (Leistungsdichtespektrum) can be plotted.
