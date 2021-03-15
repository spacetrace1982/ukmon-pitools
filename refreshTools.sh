#!/bin/bash

# refresh UKmeteornetwork tools

here="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
source $here/ukmon.ini

cd $here

sftp -i ~/.ssh/ukmon $LOCATION@$UKMONHELPER << EOF
get ukmon.ini
get live.key
get archive.key
exit
EOF
chmod 0600 live.key archive.key

echo "refreshing toolset"
git stash 
git pull
git stash apply

echo "checking boto3 is installed for AWS connections"
source ~/vRMS/bin/activate
pip list | grep boto3
if [ $? -eq 1 ] ; then 
    pip install boto3
fi 

#crontab -l | grep refreshTools
#if [ $? == 1 ] ; then 
#    crontab -l > /tmp/crontab.tmp 
#    echo "@reboot sleep 60 && /home/pi/source/ukmon-pitools/refreshTools.sh > /home/pi/RMS_data/logs/refreshTools.log 2>&1" >> /tmp/crontab.tmp
#    crontab /tmp/crontab.tmp
#    rm /tmp/crontab.tmp
#fi 
echo "done"
