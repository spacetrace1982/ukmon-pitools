#!/bin/bash

# this script can be used to restart the ukmon livefeed
# if it is killed. 
# just add this to your crontab:
# */10 * * * * /home/pi/source/ukmon-pitools/restartLiveMon.sh >/dev/null 2>&1
force=0
if [ $# -gt 0 ] 
then
    force=1
fi 
x=$(ps -ef | grep liveMon |wc -l)
if [[ $x -lt 2 || $force -eq 1 ]]
then 
    pids=$(ps -fn | grep liveMon | grep -v grep | awk '{print $1}')
    if [ "$pids" != "" ] 
    then 
        kill -9 $pids
    fi 
    echo "restarting liveMonitor"
    /home/pi/source/ukmon-pitools/liveMonitor.sh >> /home/pi/RMS_data/logs/ukmon-live.log 2>&1 &
fi