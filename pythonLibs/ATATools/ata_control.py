#!/usr/bin/python

"""
Python wrappers for various command line
tools at the ATA.
"""

import re
from subprocess import Popen, PIPE
import ast
from threading import Thread
import ata_remote
import ata_constants
import snap_array_helpers
from plumbum import local
import logger_defaults

def get_snap_dictionary(array_list):
    """
    returns the dictionary for snap0-3 antennas

    Raises KeyError if antenna is not in list
    """
    s0 = []
    s1 = []
    s2 = []
    for ant in array_list:
        if ant in ata_constants.snap0ants:
            s0.append(ant)
        elif ant in ata_constants.snap1ants:
            s1.append(ant)
        elif ant in ata_constants.snap2ants:
            s2.append(ant)
        else:
            raise KeyError("antenna unknown")

    retval = {}
    if s0:
        retval['snap0'] = s0
    if s1:
        retval['snap1'] = s1
    if s2:
        retval['snap2'] = s2

    return retval
    

def autotune(ant_string):
    logger = logger_defaults.getModuleLogger(__name__)

    logger.warning("autotune not implemented! fix it")
    return

    logger.info("autotuning: {}".format(ant_str))
    str_out,str_err = ata_remote.callObs(['ataautotune',antstr])
    #searching for warnings or errors
    rwarn = str_out.find("warning")
    if rwarn != -1:
        logger.warning(str_out)
    rerr = str_out.find("error")
    if rerr != -1:
        logger.error(str_out)
        raise RuntimeError("Autotune execution error")

def get_sky_freq():
    """
    Return the sky frequency (in MHz) currently
    tuned to the center of the ATA band
    """
    proc = Popen(["atagetskyfreq", "a"], stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    return float(stdout.strip())

def get_ascii_status():
    """
    Return an ascii table of lots of ATA
    status information.
    """
    proc = Popen("ataasciistatus", stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    return stdout

def point(source, freq, az_offset=0.0, el_offset=0.0, ants=['dummy'], writetodb=True):
    """
    Point the ATA at `source`, with an offset
    from the source's position of `az_offset` degrees
    in azimuth and `el_offset` degrees in elevation.
    Tune to a center sky frequency of `freq` MHz
    """

    proc = Popen(["pointshift", source, "%f" % freq, "%f" % az_offset, "%f" % el_offset])
    proc.wait()

#def set_rf_switch(switch, sel):
def set_rf_switch(ant_list):
    """
    Set RF switch `switch` (0..1) to connect the COM port
    to port `sel` (1..8)
    """
    logger = logger_defaults.getModuleLogger(__name__)

    ant_list_stripped = str(ant_list).replace("'","").replace("[","").replace("]","").replace(" ","")

    if socket.gethostname() == RF_SWITCH_HOST:
        proc = Popen(["rfswitch", "%s" % ant_list_stripped], stdout=PIPE, stderr=PIPE)
    else:
        proc = Popen(["ssh", "sonata@%s" % RF_SWITCH_HOST, "rfswitch", "%s" % ant_list_stripped], stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    for line in stdout.splitlines():
        logger.info("Set rfswitch for ants %s result: %s" % (ant_list_stripped, line))
    if stderr.startswith("OK"):
        logger.info("Set rfswitch for ants %s result: SUCCESS" % ant_list_stripped)
        return
    else:
        logger.info("Set switch 'rfswitch %s' failed!" % ant_list_stripped)
        raise RuntimeError("Set switch 'rfswitch %s' failed!" % (ant_list_stripped))

def rf_switch_thread(ant_list, wait):

    logger = logger_defaults.getModuleLogger(__name__)

    t = Thread(target=set_rf_switch, args=(ant_list,))
    t.start()

    if(wait == True):
        t.join();
        return None

    return t


def set_atten_thread(antpol_list, db_list, wait):
    """
    start a thread to set attenuator value
    """

    logger = logger_defaults.getModuleLogger(__name__)

    if(len(antpol_list) != len(db_list)):
        logger.error("set_atten_thread, antenna list length != db_list length.")
        raise RuntimeError("set_atten_thread, antenna list length != db_list length.")

    t = Thread(target=set_atten, args=(antpol_list, db_list,))
    t.start()

    if(wait == True):
        t.join();
        return None

    return t
    
def wait_for_threads(tlist):
    """
    wait for all threads in the list to finish
    """
    for t in tlist:
        t.join()

def set_atten(antpol_list, db_list):
    """
    Set attenuation of antenna or ant-pol `ant`
    to `db` dB.
    Allowable values are 0.0 to 31.75
    """

    antpol_str = ",".join(antpol_list)
    db_str = ",".join(map(str,db_list))
    #ant_list_stripped = str(ant_list).replace("'","").replace("[","").replace("]","").replace(" ","")
    #db_list_stripped = str(db_list).replace("'","").replace("[","").replace("]","").replace(" ","")

    logger = logger_defaults.getModuleLogger(__name__)
    logger.info("setting rfswitch attenuators %s %s" % (db_str, antpol_str))

#    if socket.gethostname() == ATTEN_HOST:
#    proc = Popen(["atten", "%s" % db_list_stripped, "%s" % ant_list_stripped],  stdout=PIPE, stderr=PIPE)
#    else:
    #proc = Popen(["ssh", "sonata@%s" % ATTEN_HOST, "sudo", "atten", "%s" % db_list_stripped, "%s" % ant_list_stripped],  stdout=PIPE, stderr=PIPE)
    #stdout, stderr = proc.communicate()
    stdout, stderr = ata_remote.callSwitch(["atten",db_str,antpol_str])

    output = ""
    # Log the result
    for line in stdout.splitlines():
        output += "%s\n" % line
        logger.info("Set atten for ant %s to %s db result: %s" % (antpol_str, db_str, line))

    if stderr.startswith("OK"):
        logger.info("Set atten for ant %s to %s db result: SUCCESS" % (antpol_str, db_str))
        return output
    else:
        logger.error("Set attenuation 'atten %s %s' failed! (STDERR=%s)" % (db_str, antpol_str,stderr))
        raise RuntimeError("ERROR: set_atten %s %s returned: %s" % (db_str, antpol_str, stderr))

#def set_pam_atten_old(ant, pol, val):
#    """
#    Set the attenuation of antenna `ant`, polarization `pol` to `val` dB
#    """
#    logger = logging.getLogger(snap_onoffs_contants.LOGGING_NAME)
#    logger.info("setting pam attenuator %s%s to %.1fdb" % (ant, pol, val))
#    if(pol == ""):
#        proc = Popen(["ssh", "obs@tumulus", "atasetpams", ant, "%f"%val, "%f"%val], stdout=PIPE)
#    else:
#        proc = Popen(["ssh", "obs@tumulus", "atasetpams", ant, "-%s"%pol, "%f"%val], stdout=PIPE)
#    stdout, stderr = proc.communicate()
#    proc.wait()
#    # Log  returned result, but strip off the newline character
#    logger.info(stdout.rstrip())

#def set_pam_attens_old(ant, valx, valy):
#    """
#    Set the attenuation of antenna `ant`, both pols, to valx and valy dB
#    """
#    logger = logging.getLogger(snap_onoffs_contants.LOGGING_NAME)
#    logger.info("setting pam attenuator %s to %.1f,%.1f db" % (ant, valx, valy))
#    proc = Popen(["ssh", "obs@tumulus", "atasetpams", ant, "%f"%valx, "%f"%valy], stdout=PIPE)
#    stdout, stderr = proc.communicate()
#    proc.wait()
#    # Log  returned result, but strip off the newline character
#    logger.info(stdout.rstrip())

#def get_pam_status(ant):
#    """
#    Get the PAM attenuation settings and power detector readings for antenna `ant`
#    """
#    logger = logging.getLogger(snap_onoffs_contants.LOGGING_NAME)
#    logger.info("getting pam attenuator %s" % ant )
#    proc = Popen(["getdetpams", ant],  stdout=PIPE, stderr=PIPE)
#    stdout, stderr = proc.communicate()
#    logger.info("getting pam attenuator stdout: %s" % stdout)
#    x = stdout.split(',')
#    return {'ant':x[0], 'atten_xf':float(x[1]), 'atten_xb':float(x[2]), 'atten_yf':float(x[3]), 'atten_yb':float(x[4]), 'det_x':float(x[5]), 'det_y':float(x[6])}

def get_pams(antlist):

    logger = logger_defaults.getModuleLogger(__name__)
    antstr = ",".join(antlist)
    logger.info("getting pams: {}".format(antstr))
    str_out,str_err = ata_remote.callObs(['atagetpams','-q',antstr])

    retdict = {}
    lines = str_out.splitlines()
    for line in lines:
        regroups = re.search('ant(?P<ant>..)\s*on\s*(?P<x>[\d.]+)\s*on\s*(?P<y>[\d.]+)',line);
        ant = regroups.group('ant')
        xval = float(regroups.group('x'))
        yval = float(regroups.group('y'))
        retdict[ant + 'x'] = xval
        retdict[ant + 'y'] = yval

    return retdict

def move_ant_group(ants, from_group, to_group):

    logger = logger_defaults.getModuleLogger(__name__)
    logger.info("Reserving \"%s\" from %s to %s" % (snap_array_helpers.array_to_string(ants), from_group, to_group))

    proc = Popen(["antreserve", from_group, to_group] + ants, stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    lines = stdout.split('\n')
    for line in lines:
        cols = line.split()
        if (len(cols) > 0) and (cols[0]  == to_group):
            bfa = cols[1:]
    for ant in ants:
        if ant not in bfa:
            #print nonegroup
            #print(ants)
            logger.error("Failed to move antenna %s from %s to %s" % (ant, from_group, to_group))
            raise RuntimeError("Failed to move antenna %s from %s to %s" % (ant, from_group, to_group))

def reserve_antennas(ants):

    move_ant_group(ants, "none", "bfa")

def release_antennas(ants, should_park):

    move_ant_group(ants, "bfa", "none")

    if(should_park):
        logger = logger_defaults.getModuleLogger(__name__)
        logger.info("Parking ants");
        #proc = Popen(["ssh", "obs@tumulus", "park.csh"], stdout=PIPE, stderr=PIPE)
        #stdout, stderr = proc.communicate()
        #proc.wait()
        stdout, stderr = ata_remote.callObs(["park.csh", ','.join(ants)])
        logger.info(stdout.rstrip())
        logger.info(stderr.rstrip())
        logger.info("Parked");

def get_ra_dec(source, deg=True):
    """
    Get the J2000 RA / DEC of `source`. Return in decimal degrees (DEC) and hours (RA)
    by default, unless `deg`=False, in which case return in sexagesimal.
    """
    proc = Popen(["atacheck", source], stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    for line in stdout.split("\n"):
        if "Found %s" % source in line:
            cols = line.split()
            ra  = float(cols[-1].split(',')[-2])
            dec = float(cols[-1].split(',')[-1])
    if deg:
        return ra, dec
    else:
        ram = (ra % 1) * 60
        ras = (ram % 1) * 60
        ra_sg = "%d:%d:%.4f" % (int(ra), int(ram), ras)
        decm = (dec % 1) * 60
        decs = (decm % 1) * 60
        dec_sg = "%+d:%d:%.4f" % (int(dec), int(decm), decs)
        return ra_sg, dec_sg

def create_ephems(source, az_offset, el_offset):

    ssh = local["ssh"]
    cmd = ssh[("obs@tumulus", "cd /home/obs/NSG;./create_ephems.rb %s %.2f %.2f" % (source, az_offset, el_offset))]
    result = cmd()
    return ast.literal_eval(result)


def point_ants(on_or_off, ant_list):

    ssh = local["ssh"]
    cmd = ssh[("obs@tumulus", "cd /home/obs/NSG;./point_ants_onoff.rb %s %s" % (on_or_off, ant_list))]
    result = cmd()
    return ast.literal_eval(result)

def set_freq(freq, ants):

    ssh = local["ssh"]
    cmd = ssh[("obs@tumulus", "atasetskyfreq a %.2f" % freq)]
    result = cmd()
    cmd = ssh[("obs@tumulus", "atasetfocus %s %.2f" % (ants, freq))]
    result = cmd()
    return result

if __name__== "__main__":

    #print get_pam_status("2a")

    #send_email("Test subject", "Test message")
    #logger = logging.getLogger(snap_onoffs_contants.LOGGING_NAME)
    #logger.setLevel(logging.INFO)
    #sh = logging.StreamHandler(sys.stdout)
    #fmt = logging.Formatter('[%(asctime)-15s] %(message)s')
    #sh.setFormatter(fmt)
    #logger.addHandler(sh)

    #print set_freq(2000.0, "2a,2b")
    #print set_atten("2jx,2jy", "10.0,10.0")
    #print create_ephems("casa", 10.0, 5.0)
    #print point_ants("on", "1a,1b")
    #print point_ants("off", "1a,1b")
    print('foo')
