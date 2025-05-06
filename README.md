# SMP-SignalProcessing

This repository contains all scripts used for my master's thesis.
Folder `data` stores the measured data and converted files

## visualizationsdensity

can be used to import and visualize density measuremnts stored in csv files

## readSMP

can be used to read .pnt SMP files. They can be converted into a csv file without any reduction of datapoints
SMP files can also be stored in dataframes and are used in further steps for visualization and signal processing

## plotSMP

can be used to visualize smp profiles. Outputs are stored in folder `output/visualizations`

## offset

functions to calculate offset of two different profiles with crosscorrelation. Outputs are stored in folder `output/cross_correlations`
