#!/bin/bash
dnd=`ps faux | grep parsednd | grep -c -v grep`
if (($dnd < 1)) ; then
#		screen -S dnd -X quit
		screen -S dnd -m -d python3.5 /opt/DND/parsednd.py
	      	echo "parsednd.py restarted" >> /var/log/syslog.log
				fi

