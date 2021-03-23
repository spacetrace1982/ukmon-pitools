#!/bin/bash

# refresh UKmeteornetwork tools

here="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
source $here/ukmon.ini

cd $here

if [ -f  .firstrun ] ; then
    sftp -i ~/.ssh/ukmon -q $LOCATION@$UKMONHELPER << EOF
get ukmon.ini
get live.key
get archive.key
exit
EOF
    chmod 0600 live.key archive.key
fi 

echo "refreshing toolset"
git stash 
git pull
git stash apply

if [ ! -f  .firstrun ] ; then
    echo 1 > .firstrun
    echo "checking boto3 is installed for AWS connections"
    source ~/vRMS/bin/activate
    pip list | grep boto3
    if [ $? -eq 1 ] ; then 
        pip install boto3
    fi 
    echo "creating ukmon ssh key"
    ssh-keygen -t rsa -f ~/.ssh/ukmon -q -N ''
    echo "Copy this public key and email it to the ukmon team, then "
    echo "wait for confirmation its been installed and rerun this script"
    echo ""
    cat ~/.ssh/ukmon.pub
    echo ""
    read -p "Press any key to continue"
fi
crontab -l | egrep "refreshTools.sh" > /dev/null
if [ $? == 1 ] ; then 
    echo "enabling daily toolset refresh"
    crontab -l > /tmp/crontab.tmp 
    echo "@reboot sleep 60 && /home/pi/source/ukmon-pitools/refreshTools.sh > /home/pi/RMS_data/logs/refreshTools.log 2>&1" >> /tmp/crontab.tmp
    crontab /tmp/crontab.tmp
    rm /tmp/crontab.tmp
fi 
crontab -l | egrep "liveMonitor.sh" > /dev/null
if [ $? == 1 ] ; then 
    echo "enabling live monitoring"
    crontab -l > /tmp/crontab.tmp 
    echo "@reboot sleep 3600 && /home/pi/source/ukmon-pitools/liveMonitor.sh >> /home/pi/RMS_data/logs/ukmon-live-`date +%Y%m%d`.log 2>&1" >> /tmp/crontab.tmp
    crontab /tmp/crontab.tmp
    rm /tmp/crontab.tmp
fi 
echo "done"
