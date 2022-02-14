#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
import atexit
from ATATools import ata_control, logger_defaults
from SNAPobs import snap_dada, snap_if
import numpy as np
import os,sys
import time

import argparse
import logging

import os

def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)

    # Define antennas
    ant_list = ["1c", "1g", "1h", "1k", "1e", "2a", "2b", "2c",
                "2e", "2h", "2j", "2k", "2l", "2m", "3c", "3d",
                "3l", "4j", "5b", "4g"]

    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas, ant_list, False)

    obs_time = 300

    antlo_list = [ant+lo.upper() for ant in ant_list for lo in ['b','c']]

    freqs   = [2200]*len(ant_list)
    freqs_c = [3000]*len(ant_list)

    ata_control.set_freq(freqs, ant_list, lo='b', nofocus=True)
    ata_control.set_freq(freqs_c, ant_list, lo='c')
    time.sleep(30)

    source = "3c295"
    ata_control.make_and_track_ephems(source, ant_list)
    ata_control.autotune(ant_list)

    snap_if.tune_if_antslo(antlo_list)

    obs_time = 650

    print("="*79)
    print("start_record_in_x.py -H 1 2 3 4 5 6 7 8 -i 15 -n %i" %obs_time)
    os.system("start_record_in_x.py -H 1 2 3 4 5 6 7 8 -i 15 -n %i" %obs_time)

    print("Recording for %i seconds..." %obs_time)
    time.sleep(obs_time+20)


    for i in range(10):
        source = "3c345"
        ata_control.make_and_track_ephems(source, ant_list)
        time.sleep(20) #make sure delay engine is updated
        print("="*79)
        print("start_record_in_x.py -H 1 2 3 4 5 6 7 8 -i 15 -n %i" %obs_time)
        os.system("start_record_in_x.py -H 1 2 3 4 5 6 7 8 -i 15 -n %i" %obs_time)

        print("Recording for %i seconds..." %obs_time)
        time.sleep(obs_time+20)


        source = "3c295"
        ata_control.make_and_track_ephems(source, ant_list)
        time.sleep(20) #make sure delay engine is updated
        print("="*79)
        print("start_record_in_x.py -H 1 2 3 4 5 6 7 8 -i 15 -n %i" %obs_time)
        os.system("start_record_in_x.py -H 1 2 3 4 5 6 7 8 -i 15 -n %i" %obs_time)

        print("Recording for %i seconds..." %obs_time)
        time.sleep(obs_time+20)



if __name__ == "__main__":
    main()
