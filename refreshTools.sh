#!/bin/bash

# refresh UKmeteornetwork tools

here=/home/$LOGNAME/source/ukmon-pitools
cd $here

if [ ! -f $here/ukmon.ini ] ; then
    echo  "# config data for this station" > $here/ukmon.ini
    echo  "export LOCATION=NOTCONFIGURED" >> $here/ukmon.ini
    echo  "export UKMONHELPER=3.8.65.98" >> $here/ukmon.ini
    echo  "export UKMONKEY=~/.ssh/ukmon" >> $here/ukmon.ini
    echo  "export RMSCFG=~/source/RMS/.config " >> $here/ukmon.ini
    echo "location not configured yet"
fi 
source $here/ukmon.ini
if [ "$RMSCFG" == "" ] ; then
    export RMSCFG=~/source/RMS/.config
fi 

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

if [ ! -f  ~/.ssh/ukmon ] ; then 
    echo "creating ukmon ssh key"
    ssh-keygen -t rsa -f ~/.ssh/ukmon -q -N ''
    echo "Copy this public key and email it to the ukmon team, then "
    echo "wait for confirmation its been installed and rerun this script"
    echo ""
    cat ~/.ssh/ukmon.pub
    echo ""
    read -p "Press any key to continue"
fi

if [[ "$LOCATION" != "NOTCONFIGURED"  && "$LOCATION" != "" ]] ; then
    if [ $(file $here/ukmon.ini | grep CRLF | wc -l) -ne 0 ] ; then
        echo 'fixing ukmon.ini'
        cp $here/ukmon.ini $here/tmp.ini
        # dos2unix not installed on the pi
        tr -d '\r' < $here/tmp.ini > $here/ukmon.ini
        rm -f $here/tmp.ini
    fi 
    sftp -i ~/.ssh/ukmon -q $LOCATION@$UKMONHELPER << EOF
get ukmon.ini
get live.key
get archive.key
exit
EOF
    chmod 0600 live.key archive.key
    echo "testing connections"
    source ~/vRMS/bin/activate
    python $here/sendToLive.py test test
    python $here/uploadToArchive.py test
    echo "if you didnt see two success messages contact us for advice" 
    read -p "Press any key to continue"
else
    echo "Location missing - please update UKMON Config File using the desktop icon"
    sleep 5
    read -p "Press any key to continue"
    exit 1
fi

if [ $(grep ukmonPost $RMSCFG | wc -l) -eq 0 ] ; then
    python -c "import ukmonPostProc as pp ; pp.installUkmonFeed('${RMSCFG}');"
fi 
if [ ! -f ~/Desktop/UKMON_config.txt ] ; then 
    ln -s $here/ukmon.ini ~/Desktop/UKMON_config.txt
fi 
if [ ! -f ~/Desktop/refresh_UKMON_Tools.sh ] ; then 
    ln -s $here/refreshTools.sh ~/Desktop/refresh_UKMON_Tools.sh
fi 

crontab -l | egrep "refreshTools.sh" > /dev/null
if [ $? == 1 ] ; then 
    echo "enabling daily toolset refresh"
    crontab -l > /tmp/crontab.tmp 
    echo "@reboot sleep 60 && $here/refreshTools.sh > /home/$LOGNAME/RMS_data/logs/refreshTools.log 2>&1" >> /tmp/crontab.tmp
    crontab /tmp/crontab.tmp
    rm /tmp/crontab.tmp
fi 

crontab -l | egrep "liveMonitor.sh" > /dev/null
if [ $? == 1 ] ; then 
    echo "enabling live monitoring"
    crontab -l > /tmp/crontab.tmp 
    echo "@reboot sleep 3600 && $here/liveMonitor.sh >> /home/$LOGNAME/RMS_data/logs/ukmon-live.log 2>&1" >> /tmp/crontab.tmp
    crontab /tmp/crontab.tmp
    rm /tmp/crontab.tmp
fi 
echo "done"
