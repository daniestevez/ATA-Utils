#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
from ATATools import ata_control, logger_defaults
from SNAPobs import snap_dada, snap_if
import time
import atexit
import numpy as np
import sys

import argparse
import logging

import os,sys
import glob

from SNAPobs import snap_config

CFG = snap_config.get_ata_cfg()

def mv_utc_antlo_to_ant(utc):
    obsdir = CFG['OBSDIR']
    g = glob.glob(os.path.join(obsdir, utc, "*"))
    for eachDir in g:
        bname = os.path.basename(eachDir)
        t = bname[0]
        e = bname[-1]
        if (t.isnumeric()) and (e.lower() in ["a","b","c","d"]):
            os.rename(eachDir, eachDir[:-1]) #remove LO
    return

def main():
    logger = logger_defaults.getProgramLogger("observe", 
            loglevel=logging.INFO)

    # moon observation
    az_offset = -20.
    el_offset = 0.

    #ant_list = ["1a", "1f", "1c", "2a", "2b", "3d",
    #        "4g", "1k", "5c", "1h", "4j", "2h"]
    ant_list = ["1a", "1f", "1c", "2a", "4j", "2h",
            "3d", "4g", "1k", "5c", "1h", "2b"]

    antlo_list = ["1aA", "1fA", "2aA", "2hA", "3dA", "4gA", "1kA", "5cA", "1hA", "2bA",
            "1cB", "1eB", "1gB", #rfsoc1
            "2cB", #rfsoc2
#            "2eB", "2jB", #"2kB", #rfsoc3
            "2mB", "3cB", #rfsoc4
            "3lB", "5bB", "4jB"  #rfsoc5
            ]

    antlo_list = [
		"1cB", "1eB", "1gB", "1hB",
		"1kB", "2aB", "2cB",
		"2eB", "2hB", "2jB",
		"2mB", "3cB", "3dB",
		"3lB", "4jB", "5bB", "4gB"]

    ant_list = [antlo[:-1] for antlo in antlo_list]

    ata_control.reserve_antennas(ant_list)
    atexit.register(ata_control.release_antennas,ant_list, False)

    obs_time = 30
    n_on_off = 1

    source = "moon"
    ata_control.create_ephems2(source, az_offset, el_offset)

    ata_control.point_ants2(source, "off", ant_list)
    ata_control.autotune(ant_list)

    #freqs = np.arange(2250, 11200, 550)

    freqs = np.arange(2250, 6100, 550)
    #freqs = np.arange(6100, 9950, 550)
    #freqs = np.arange(9950, 11200, 550)

    #snap_dada.set_freq_auto([freqs[0]]*len(ant_list), ant_list)
    ata_control.set_freq([freqs[0]]*len(ant_list), ant_list, lo='a')
    ata_control.set_freq([freqs[0]]*len(ant_list), ant_list, lo='b')

    snap_if.tune_if_antslo(antlo_list)
    time.sleep(30)

    utcs_all = []
    for ifreq, freq in enumerate(freqs):
        utcs_this_freq = []
        if ifreq != 0:
            ata_control.set_freq([freq]*len(ant_list), ant_list, lo='a')
            time.sleep(20)
            ata_control.set_freq([freq]*len(ant_list), ant_list, lo='b')
            snap_if.tune_if_antslo(antlo_list)

        for i in range(n_on_off):
            # record on
            ata_control.point_ants2(source, "on", ant_list)

            ntries = 0
            while True:
                try:
                    utc = snap_dada.start_recording(antlo_list, obs_time, 
                            npolout=2, acclen=120*16, disable_rfi=True)
                    break
                except Exception as e:
                    print("Got exception")
                    print(e)
                    ntries += 1
                    if ntries > 3:
                        raise e
                    time.sleep(0.5)

            utcs_this_freq.append(utc)
            mv_utc_antlo_to_ant(utc)
            os.system("killall ata_udpdb")

            #record off
            ata_control.point_ants2(source, "off", ant_list)

            ntries = 0
            while True:
                try:
                    utc = snap_dada.start_recording(antlo_list, obs_time, 
                            npolout=2, acclen=120*16, disable_rfi=True)
                    break
                except Exception as e:
                    print("Got Exception")
                    print(e)
                    ntries += 1
                    if ntries > 3:
                        raise e
                    time.sleep(0.5)

            utcs_this_freq.append(utc)
            mv_utc_antlo_to_ant(utc)
            os.system("killall ata_udpdb")

        utcs_all.append(utcs_this_freq)

    initial_utc = utcs_all[0][0]
    sys.exit(0)


    os.system("mkdir /mnt/datax-netStorage-40G/calibration/"+initial_utc)
    for freq, utcs in zip(freqs, utcs_all):
        os.system("mkdir /mnt/datax-netStorage-40G/calibration/%s/freq_%i"
                %(initial_utc, freq))
        for utc in utcs:
            os.system("mv /mnt/buf0/obs/%s /mnt/datax-netStorage-40G/calibration/%s/freq_%i"
                    %(utc, initial_utc, freq))

    os.system("/home/obsuser/scripts/fil2csv.py /mnt/datax-netStorage-40G/calibration/%s/*/*/*/*.fil" %(initial_utc))

    """
    os.system("mkdir /mnt/datax-netStorage-40G/calibration/"+initial_utc)
    for freq, utcs in zip(freqs, utcs_all):
        for utc in utcs:
            os.system("mv /mnt/buf0/obs/%s /mnt/datax-netStorage-40G/calibration/%s"
                    %(utc, initial_utc))
    """

    o = open("/mnt/datax-netStorage-40G/calibration/obs.dat", "a")
    o.write("%s %s %i\n" %(initial_utc, source, n_on_off))
    o.close()


if __name__ == "__main__":
    main()
