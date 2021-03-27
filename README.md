ukmeteornetwork toolset for RMS pi meteor cameras
=================================================
These tools manage uploads of RMS data to the UK Meteor Network Archive and Live-stream.

INSTALLATION
------------
* Login to your pi using VNC or AnyDesk or TeamViewer, open a Terminal window from the Accessories menu, then type the following
> cd /home/pi/source  
> git clone https://github.com/markmac99/ukmon-pitools.git  
> cd ukmon-pitools  
> ./refreshTools.sh  

* When prompted, copy the SSH public key. 

* Email the key to markmcintyre99@googlemail.com along with your location (eg the name of your town or village) and the rough direction your camera points in eg SW, S, NE. The location should be no more than 16 characters. We will also need your camera ID, latitude, longitude and elevation if possible, so that your data can be included in the Orbit and Trajectory solving routines. 

* We will add your key to our server and send you a small config file.  Copy this file into */home/pi/source/ukmon-pitools* 
* Once you've installed the ini file, re-run the *refreshTools.sh* script to download your security keys and bring the tools up to date. 

* Finally to enable daily uploads to the UKMON archive, double-click the *RMS_Config.txt* icon on the Pi desktop, find and update the following values
> external_script_run: true  
> auto_reprocess_external_script_run: true  
> auto_reprocess: true  
> external_script_path: /home/pi/source/ukmon-pitools/ukmonPostProc.py  

Note: if external_script_run was already true please follow these additional steps  
> Using a text editor, create a new file */home/pi/source/ukmon-pitools/extrascript*  
> copy the current value of external_script_path and paste it into this file  (nb just the part after the colon)   
> set external_script_path to /home/pi/source/ukmon-pitools/ukmonPostProc.py  
> save both files.   

RMS will now run ukmonPostProc.py and then run the script mentioned in "extrascript"


HOW THE TOOLS WORK
==================
ukmonPostProc.py
================
This uses the RMS post-processing hook to creates JPGs and other data, then upload to the UK Meteor Network archive. The script has three optional capabilities: 


MP4s and Timelapse
------------------
The script can  create MP4s of each detection and a timelapse of the  whole night. 
To enable these, create files named "domp4s" or "dotimelapse" in the same folder as the script:  
> echo "1" > /home/pi/source/ukmon-pitools/domp4s  
> echo "1" > /home/pi/source/ukmon-pitools/dotimelapse  

Running an Additional Script
----------------------------
If you want to run an additional Python script after this one finishes, create a file named "extrascript" 
in the same folder, containing a single line with the full path to the script, eg
> echo "/home/pi/myfolder/myscript.py" > /home/pi/source/ukmon-pitools/extrascript  

This script will be passed the capture_dir, archive_dir and RMS config object in the same way as RMS
passes these to any external script. 

uploadToArchive.py
==================
This does the actual  uploading to the UK meteor network archive. Can be called standalone if you want to reupload data:
eg  
> python uploadToArchive.py UK0006_20210312_183741_206154  

this will upload from /home/pi/RMS_data/ArchivedFiles/UK0006_20210312_183741_206154

liveMonitor.sh
==============
This script monitors in realtime for detections, then uploads them to ukmon-live. The script calls a 
python script liveMonitor.py. 

sendToLive.py
-------------
Part of liveMonitor, this python script does the actual uploading. You can use it manually as follows:  
> python sendToLive.py capture-dir ff-file-name 

refreshTools.sh
===============
Updates the UKMON RMS Toolset to the latest version. After first run, this will run automatically
every time your Pi reboots. You can also run it manually. 

refreshTools reads from a configuration file that is specific to your camera. We will send
you this file when you onboard to the network. The file contains your location ID and the
details of our sftp server used to distribute security keys. 

Questions
=========
Any questions, concerns or suggestions to me via markmcintyre99@googlemail.com  