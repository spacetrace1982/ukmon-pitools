# Copyright (C) Mark McIntyre
import time
import os
import sys
import glob
import boto3
import sendToLive as uoe
import datetime
import logging
from RMS.Logger import initLogging
import RMS.ConfigReader as cr
from stat import ST_INO
from uploadToArchive import readKeyFile


log = logging.getLogger("logger")

timetowait = 30 # seconds to wait for a new line before deciding the log is stale

# Images created more than this many seconds ago won't be uploaded. Prevents reuploads. 
MAXAGE=int(os.getenv('UKMMAXAGE', default='1800')) 

# frequency at which to check for fireball requests. Zero means dont check
FBINTERVAL = int(os.getenv('UKMFBINTERVAL', default='1800'))


def follow(fname, logf_ino):
    thefile = open(fname, 'r')
    t = 0
    while True:
        line = thefile.readline()
        if not os.path.isfile(fname):
            time.sleep(1)
        sres = os.stat(fname)
        if logf_ino != sres[ST_INO]:
            yield 'log rolled'

        if not line:
            time.sleep(0.1)
            t = t + 0.1
            if t > timetowait:
                t = 0
                yield 'log stale'
            else:
                continue
        else:
            t = 0
            yield line.strip()


def monitorLogFile(camloc, rmscfg):
    """ Monitor the latest RMS log file for meteor detections, convert the FF file
    to a jpg and upload it to ukmon-live. Requires the user to have been supplied
    with a ukmon-live security key and camera location identifier. 
    """
    cfg = cr.parse(os.path.expanduser(rmscfg))

    
    log = logging.getLogger("logger")
    while len(log.handlers) > 0:
        log.removeHandler(log.handlers[0])
        
    initLogging(cfg, 'ukmonlive_')
    log.info('--------------------------------')
    log.info('    ukmon-live feed started')
    log.info('--------------------------------')

    log.info('Camera location is {}'.format(camloc))
    log.info('RMS config file is {}'.format(rmscfg))

    myloc = os.path.split(os.path.abspath(__file__))[0]

    # get credentials
    if not os.path.isfile(os.path.join(myloc, 'live.key')):
        log.error('AWS key not present, aborting')
        exit(1)
    keys = readKeyFile(os.path.join(myloc, 'live.key'))
    awskey = keys['LIVE_ACCESS_KEY_ID']
    awssec = keys['LIVE_SECRET_ACCESS_KEY']
    awsreg = keys['LIVEREGION']
    archkey = keys['AWS_ACCESS_KEY_ID']
    archsec = keys['AWS_SECRET_ACCESS_KEY']
    archreg = keys['ARCHREGION']
    target = keys['LIVEBUCKET']

    conn = boto3.Session(aws_access_key_id=awskey, aws_secret_access_key=awssec, region_name=awsreg) 
    s3 = conn.resource('s3')
    archconn = boto3.Session(aws_access_key_id=archkey, aws_secret_access_key=archsec, region_name=archreg) 
    archs3 = archconn.resource('s3')

    datadir = cfg.data_dir
    logdir = os.path.expanduser(os.path.join(datadir, cfg.log_dir))
    keepon = True
    logf = ''
    capdir = ''
    starttime = datetime.datetime.utcnow()
    while keepon is True:
        try:
            logfs = glob.glob(os.path.join(logdir, 'log_{}*.log*').format(cfg.stationID))
            logfs.sort(key=lambda x: os.path.getmtime(x))
            newlogf = logfs[-1]
            if newlogf != logf:
                logf = newlogf
                log.info('Now monitoring {}'.format(logf))
            lis = open(logf,'r').readlines()
            dd = [li for li in lis if 'Data directory' in li]
            if len(dd) > 0:
                capdir = dd[0].split(' ')[5].strip()
                #log.info('Capture dir is {}'.format(capdir))

            # iterate over the generator
            logf_ino = os.stat(logf)[ST_INO]
            loglines = follow(logf, logf_ino)

            for line in loglines:
                nowtm = datetime.datetime.utcnow()
                if (FBINTERVAL > 0) and ((nowtm - starttime).seconds > FBINTERVAL):
                    try:
                        #log.info('checking for fireball flags')
                        uoe.checkFbUpload(cfg.stationID, datadir, archs3)
                    except Exception as e: 
                        log.warning('problem checking fireball flags')
                        log.info(e, exc_info=True)
                    starttime = nowtm
                if line == 'log stale' or line == 'log rolled':
                    #log.info(line)

                    logfs = glob.glob(os.path.join(logdir, 'log_{}*.log*').format(cfg.stationID))
                    logfs.sort(key=lambda x: os.path.getmtime(x))
                    logf = logfs[-1]
                    loglines.close()
                else:
                    if "Data directory" in line: 
                        newcapdir = line.split(' ')[5].strip()
                        if capdir != newcapdir:
                            capdir = newcapdir
                            log.info('Latest capture dir is {}'.format(capdir))

                    nowtm = datetime.datetime.utcnow()
                    if "detected meteors" in line and ": 0" not in line and "TOTAL" not in line:
                        if capdir != '':
                            ffname = line.split(' ')[3]
                            ftime = datetime.datetime.strptime(ffname[10:25], '%Y%m%d_%H%M%S')
                            if (nowtm - ftime).seconds < MAXAGE:
                                log.info('uploading {}'.format(ffname))
                                uoe.uploadOneEvent(capdir, ffname, cfg, s3, camloc, target)
                            else:
                                #log.info('skipping {} as too old'.format(ffname))
                                pass
            #log.info('no more lines, rereading {}'.format(logf))
        except StopIteration:
            log.info('restarting to read {}'.format(logf))
            pass
        except Exception as e:
            log.info('restarting due to crash:')
            log.info(e, exc_info=True)
            pass


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('LOCATION missing')
        exit(1)
    if len(sys.argv) < 3:
        rmscfg = '/home/pi/source/RMS/.config'
    else:
        rmscfg = sys.argv[2]
    camloc = sys.argv[1]
    monitorLogFile(camloc, rmscfg)
