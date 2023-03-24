# Processing ATA TRAPPIST-1 Multibeam observation data
NOTE: Data directory tree structure is important for processing files with bash script: 
base_project_directory -> observations -> integrations -> nodes -> filterbank files
However, the cross correlation script is agnostic to the directory structure.
It will recursively scan all subfolders of the input directories for the requisite dat and fil files.

1. Use tset_bash.sh with hardcoded observation directory to run fscrunch and turboSETI.
    - h5 or fil files --> dat and log files.

2.  Two methods available for correlating hits across multiple beams:
    - OLD METHOD: 2beam_spatial_filter.py does the spatial filtering with a given target beam as input
        - dats and logs --> csv
        - filters on overlapping frequencies of hits in each dat file (isolating only those with no obvious pair)
        - limited to 2 beams (because it hasn't been fixed for N-beam yet)
        - faster than new method because it only looks at dat text files
    - NEW METHOD: CCFnbeam.py uses cross-correlation to identify the same signals in both beams
        - dats and logs --> csv
        - correlates frequency ranges of hits in target beam with other beams
        - should work with any number of beams
        - slower than old method because it draws blimpy waterfall data slice for each hit in all beams

3. target_beam_stats.py conducts statistical analysis on the correlated hits of the target vs off-target beams.
    - csv --> histograms & csv
    - input arguments allow for filtering of csv
    - OPTIONAL

4. plot_target_hits.py uses plot_target_utils.py to plot the hits in the input csv.
    - csv --> waterfall plots
    - input arguments allow for filtering of csv
