#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
from ATATools import ata_control, logger_defaults
import atexit
from SNAPobs import snap_dada, snap_if
import numpy as np
import sys
import time

import argparse
import logging

import os

def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)
    
    ant_list = ["1c", "1e", "1g", "1h", "2a", "2b", "2c",
                "2e", "2h", "2j", "2k", "2l", "2m", "3c", "3d",
                "3l", "4j", "5b", "4g"] # whats going on with 1k? 2k points somewhere else
    
    ant_2k = ['2k']

    lo = 'B'
    antlo_list = [ant+lo for ant in ant_list]

    pams = {ant+pol:27 for ant in ant_list for pol in ["x","y"]}
    ifs  = {antlo+pol:20 for antlo in antlo_list for pol in ["x","y"]}

    ata_control.set_pams(pams)
    snap_if.setatten(ifs)
    freq = 1600

    #snap_dada.set_freq_auto([freq]*len(ant_list), ant_list)
    ata_control.set_freq([freq]*len(ant_list), ant_list, lo='b')

    obs_time = 60
    

    az = 203.323 #121.96
    el = 40.119 #23.63
    #step = 2

    #az_list = np.arange(goes_az - 10, goes_az + 10, step)
    #el_list = np.arange(goes_el - 10, goes_el + 10, step)

    #for az in az_list:
    #    for el in el_list

    print("az: %.2f, el: %.2f" %(az, el))
    os.system("killall ata_udpdb")
    ata_control.set_az_el(ant_2k, az, el)

    utc = snap_dada.start_recording(antlo_list, obs_time, acclen=120*16,
                    disable_rfi=True)
    time.sleep(10)

if __name__ == "__main__":
    main()
