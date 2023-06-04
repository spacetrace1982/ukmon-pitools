# 
# python script thats called when the nightly run completes to generate jpgs 
# and upload data to the ukmeteornetwork
# Copyright (C) 2018-2023 Mark McIntyre
#
# Notes: 
# - to enable MP4 creation of each detection, create a file 'domp4s' in the same folder as this script
# - to enable creation of an all-night timelapse, create a file 'dotimelapse'
# - to trigger another python script after this one, create a file 'extrascript' containing the full path 
#   to the extra script. The script will be passed the same arguments as this one (cap_dir, arc_dir, config)

import os
import sys

# import Utils.StackFFs as sff
import Utils.BatchFFtoImage as bff2i
import Utils.GenerateMP4s as gmp4
import RMS.ConfigReader as cr
from importlib import import_module as impmod
import logging
from RMS.Logger import initLogging

import uploadToArchive 

log = logging.getLogger("logger")


def rmsExternal(cap_dir, arch_dir, config):
    """ Called from RMS to trigger the UKMON specific code  

    Arguments:  
    cap_dir: [str] full path to the night's CapturedFiles folder  
    arch_dir: [str] full path to the night's ArchivedFiles folder  
    config: [object] an RMS config object.  

    """
    # clear existing log handlers
    log = logging.getLogger("logger")
    while len(log.handlers) > 0:
        log.removeHandler(log.handlers[0])
        
    initLogging(config, 'ukmon_')
    log.info('ukmon external script started')
    
    rebootlockfile = os.path.join(config.data_dir, config.reboot_lock_file)
    with open(rebootlockfile, 'w') as f:
        f.write('1')

    # create jpgs from the potential detections
    log.info('creating JPGs')
    try:
        bff2i.batchFFtoImage(arch_dir, 'jpg', True)
    except Exception:
        bff2i.batchFFtoImage(arch_dir, 'jpg')

    myloc = os.path.split(os.path.abspath(__file__))[0]
    log.info('app home is {}'.format(myloc))
    if os.path.isfile(os.path.join(myloc, 'domp4s')):
        # generate MP4s of detections
        log.info('generating MP4s')
        ftpdate=''
        if os.path.split(arch_dir)[1] == '':
            ftpdate=os.path.split(os.path.split(arch_dir)[0])[1]
        else:
            ftpdate=os.path.split(arch_dir)[1]
        ftpfile_name="FTPdetectinfo_"+ftpdate+'.txt'
        gmp4.generateMP4s(arch_dir, ftpfile_name)
    else:
        log.info('mp4 creation not enabled')
    
    log.info('uploading to archive')
    uploadToArchive.uploadToArchive(arch_dir)

    # do not remote reboot lock file if running another script
    # os.remove(rebootlockfile)
    extrascrfn = os.path.join(myloc, 'extrascript')
    if os.path.isfile(extrascrfn):
        extrascript = open(extrascrfn,'r').readline().strip()
        log.info('running additional script {:s}'.format(extrascript))
        sloc, sname = os.path.split(extrascript)
        sys.path.append(sloc)
        scrname, _ = os.path.splitext(sname)
        nextscr=impmod(scrname)
        nextscr.rmsExternal(cap_dir, arch_dir, config)
    else:
        log.info('additional script not called')
        try:
            os.remove(rebootlockfile)
        except Exception:
            log.info('unable to remove reboot lock file, pi will not reboot')
            pass

    # clear log handlers again
    while len(log.handlers) > 0:
        log.removeHandler(log.handlers[0])  
    return True


def manualRerun(dated_dir, rmscfg = '~/source/RMS/.config'):
    """This function is used to manually rerun the Ukmon post processing script.  
    To invoke this function, open a Terminal window and run the following:  

    *python ../ukmon-pitools/ukmonPostProc.py dated_dir rmscfg*  

    Args:
        dated_dir (str): This is the name of the folder to upload eg UK000F_20210512_202826_913898  
        rmscfg (str): optional. full path to the RMS config file to be used. Required for multi-station linux builds  
    """
    config = cr.parse(os.path.expanduser(rmscfg))
    cap_dir = os.path.join(config.data_dir, 'CapturedFiles', dated_dir)
    if not os.path.isdir(cap_dir):
        print(cap_dir)
        return False
    arch_dir = os.path.join(config.data_dir, 'ArchivedFiles', dated_dir)
    if not os.path.isdir(arch_dir):
        return False
    return rmsExternal(cap_dir, arch_dir, config)


def main(args):
    if len(args) < 2:
        print('usage: python ukmonPostProc.py arc_dir_name rmscfg')
        print('rmscfg is optional')
        print('eg python ukmonPostProc.py UK0006_20210312_183741_206154')
        print('eg python ukmonPostProc.py UK0006_20210312_183741_206154 ~/source/RMS/')
        print('\n nb: script must be run from RMS source folder')
        return False
    arch_dir = args[1]
    try:
        if 'ConfirmedFiles' in arch_dir or 'ArchivedFiles' in arch_dir or 'CapturedFiles' in arch_dir:
            _, arch_dir = os.path.split(arch_dir)
        if len(args) > 2:
            ret = manualRerun(arch_dir, args[2])
        else:
            ret = manualRerun(arch_dir)
        return ret
    except Exception:
        print('unable to call manualRerun')
        return False


if __name__ == '__main__':
    main(sys.argv)
