
#### My comment:
I had an issue to make monast project know about DND state at the phones and faced with a problem 
that not all phones have possibilitie to make a call to Asterisk while changing it's state to 'DND'.

I mean I didn't find the possibility to make Linksys phones activate DND and make a call to Asterisk 
at the same time (making a call for generating AMI "UserEvent" for monast) and deactivate DND state
by one PSK ( programmable soft key). That's why Linksys phones send a debug-log to rsyslog on VoIP-server, 
then python script parsednd.py parse in real time /var/log/DND.log (that was created by rsyslog) and 
generates AMI Action "UserEvent" for monast. Look at the syslog-ng config at the end of this comment.

Initially, I didn't have a database, but then I had to add it because of a problem with DND on Linksys phones,
that's why this DND feature is so weird ;)

See structural scheme below to make it clearer
##### All scripts, rsyslog and logrotate settings, Asterisk extensions.conf in /DND folder in this branch (DND)
![dnd diagram_pub](https://user-images.githubusercontent.com/37866374/50450475-013ae900-0937-11e9-81e5-805ab701b10e.png)
##### Explanation to structural scheme:
Grandstream, Yealink, Cisco phones send a call to number 881 when you turn on DND mode and a call to 882 
when you turn it off. Asterisk generates AMI "UserEvent" with arguments:
- DND - enabled or disabled
- peername 

Then this AMI "UserEvent" catches monast, writes (DND - enabled) or removes (DND - disabled) peer to(from) /opt/monast/dnd_list and changes peer status to 'DND' (I added 'DND' state to /pymon/monast.py script at line 741)

Linksys phones write debug-log to syslog-server on VoIP-server -> rsyslog pars it and, when finding a line with 
the word "DND", forms the log file DND.log -> script parsednd.py in the real-time pars this log, accesses the 
database (DB called 'monast' and has a table 'employee' -`employee`(`id`, `peer`, `description`, `callerid`, `phone`, `ip`, `incoming`))
and in the employee table (filled with the script peerlist.py) looks for the correspondence of the 
IP-address (current IP-phone ip-address) and peer, then generates AMI "UserEvent". 
This AMI "UserEvent" catches monast, writes (DND - enabled) or removes (DND - disabled) peer to(from)
/opt/monast/dnd_list and changes the peer status at he Web-page.

Scripts (in my server they are at /opt/DND folder):
- dnd_watch.sh - bash script to check if parsednd.py is running in the screen
- dnd_restart.sh - restart script parsednd.py
- parsednd.py - python script for Monast (use python3.5)
- peerlist.py - python script, fills monast database, employee table (use python3.5)

Asterisk:

I use Asterisk 14.7.7, so I changed some AMI Events in monast.py to correspond to this Asterisk version.
You can find extensions.conf in /DND folder - extensions.conf

Logs:
- /var/log/parsednd.log
- /var/log/peerlist.log
- /var/log/DND.log - from this log rsyslog writes the DND status and ip-address of the phone 
(the line that Linksys sends to syslog)

Logrotate:

- logrotate is configured to rotate logs weekly. You can find logrotate conf files in /DND/logrotate folder, 
move them to /etc/logrotate.d folder
- /var/log/DND.log - creates by logrotate, other logs are created by scripts, if there is no log, it means 
nothing has happened to write to the log.

If the peer DND status is displayed incorrectly, delete or add the peername on the monast server to the 
/opt/monast/dnd_list file and restart monast - /etc/init.d/monast restart.

#### IP-phone settings:
- CISCO phones: here is the link how to congfigure DND PSK for sending a call to Asterisk - http://www.funkynerd.com/the-definitive-guide-to-asterisk-dnd-with-the-cisco-spa5xx-sip-phone
- Grandstream phones: go to Accounts -> Call Settings, find there "DND Call Feature On" and "DND Call Feature Off",
write there a number and phone will dial that number when the DND mode is activated/deactivated
- Yealink phones: the same as Grandstream
- Linksys phones: go to System -> Optional Network Configuration, find there "Debug Server" and write your server 
(with configured rsyslog) there.

#### syslog-ng settings (for Linksys phones):
Don't forget to add:

@include "/etc/syslog-ng/conf.d/*.conf"

to the end of the /etc/syslog-ng/syslog-ng.conf, then put ipphone.conf from the /DND/rsyslog folder to the 
/etc/syslog-ng/conf.d/ folder in your server



#### Original README comment:
Before playing with Monast you must install a couple of things in
your system (with administrator privileges). Make sure to have both
PHP5 and Python2.4+ installed.

Copy the sample file named monast.conf.sample from the pymon/
directory to /etc/monast.conf and edit it properly as documented
inside of this file. Do some tests with your Asterisk Manager
Interface user before trying it out, maybe it's your fault and not
Monast's. You can then execute the monast.py script located in the
pymon/ directory as well. You should see a bunch of log messages
confirming the AMI login and start receiving events.

Monast has been successfully tested under many Linux distributions
(like Slackware, CentOS and Mandriva) and also on MacOS X.
* Requires Twisted Python (http://twistedmatrix.com)
  Starpy (http://www.vrplumber.com/programming/starpy/)
See INSTALL file.

Monast webpage is located at <https://dagmoller.github.io/monast/> and it's licenced
under BSD. It has been created by Diego Aguirre (DagMoller).
