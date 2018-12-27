#!/usr/bin/python3.4
#coding: utf-8

#### ------------------------------ INFO ------------------------------ ####
#### Use python3.5 to run this script ###
#### For internal use only. Login and password are passed in clear mode ####

import os
import re
import time
import pymysql
pymysql.install_as_MySQLdb()
import gc
from asterisk.ami import AMIClient
from asterisk.ami import SimpleAction
import logging
from logging.handlers import WatchedFileHandler

#-- DB definions:
db_name = 'DB_NAME'
host = 'XXX.XXX.XXX.XXX'
user = 'USERNAME'
passwd = 'PASSWORD'
table = 'employee'

#-- AMI definions:
aster_server = 'XXX.XXX.XXX.XXX' (127.0.0.1 - for localhost)
ami_port = 'port_FROM_/etc/asterisk/manager.conf'
ami_user = 'USER_FROM_/etc/asterisk/manager.conf'
ami_pass = 'PASSWORD_FROM_/etc/asterisk/manager.conf'

# ----- logger settings:
logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# ---- syslog file settings:
fh = logging.handlers.WatchedFileHandler('/var/log/parsednd.log')
fh.setLevel(logging.INFO) # For log-file output use logging.INFO to write to log
fh.setFormatter(formatter)
# ---- terminal log output settings:
# --- How to use DEBUG mode:
# --- For terminal output use logging.debug.
# --- Uncomment this line for debug only! Don't forget to comment this line back: 
#logger.setLevel(logging.DEBUG)
# --- And comment this line:
logger.setLevel(logging.INFO)
# --- And don't forget to get it all back :)
# --- End of DEBUG mode block
ch = logging.StreamHandler()
ch.setFormatter(formatter)
# ------------------------------
logger.addHandler(fh)
logger.addHandler(ch)

db_name = 'employee'

def tail(f):
    f.seek(0,2)
    while True:
        line = f.readline()
        if not line: 
            time.sleep(0.1)
            continue
        yield line

# Log and regaxp for it:
#Aug 29 11:46:46 192.168.161.6 [0]Enable DND
#Aug 29 11:46:49 192.168.161.6 [0]Disable DND
#\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s\[0\]Enable\sDND

def initial():
    enable_dnd = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s\[0\]Enable\sDND'
    disable_dnd = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s\[0\]Disable\sDND'
    re_ip = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
    f = open('/var/log/DND.log', 'r')
    logStr = tail(f)
    
    for line in logStr:
        logging.debug("line from DND.log: %s " %line )
        
        if re.findall(enable_dnd,line):
            ip = re.findall(re_ip, line)
            ip = ''.join(ip) 
            peer = get_peer(ip)
            logging.info("Enter to enable. IP: %s peer: %s " %(ip, peer) )
            peer = ''.join(peer)
            ami_event(peer, 'enabled')
        
        elif re.findall(disable_dnd,line):
            ip = re.findall(re_ip, line)
            ip = ''.join(ip) 
            peer = get_peer(ip)
            if peer:
                peer = ''.join(peer)
                logging.info("Enter to disable. IP: %s peer: %s " %(ip, peer) )
                ami_event(peer, 'disabled')
            else:
                logging.info("ERROR! problems with peer %s " %(peer))
                logging.info("ERROR! problems with peer %s with ip %s" %(peer, ip))

def get_peer(ip):
    db = pymysql.connect(host=host, user=user, passwd=passwd, db=db_name, charset='utf8mb4')
    cursor = db.cursor()
    sql = """SELECT peer FROM `%(db_name)s` WHERE ip = '%(ip)s'""" %{"db_name":db_name, "ip":ip}
    cursor.execute(sql)
    peer = cursor.fetchone()
    db.close()
    gc.collect()
    return(peer)

def ami_event(peer, action):

# Part of dialplan to generate AMI UserEvent:    
# exten => 881,2,UserEvent(Channel: SIP, Peername: ${CALLERID(num)}, DND: enabled)
# exten => 882,2,UserEvent(Channel: SIP, Peername: ${CALLERID(num)}, DND: disabled)
    
    # channel - just a variable for MonAst
    channel = 'SIP/'+str(peer)

    # AMI connection. username and secret create in /etc/asterisk/manager.conf:
    client = AMIClient(address=aster_server, port=ami_port)
    client.login(username=ami_user, secret=ami_pass)
   
    if action == 'enabled':
        action = SimpleAction('UserEvent', UserEvent='UserEvent', peername=peer, dnd='enabled', channel=channel, status='DND enabled',)
    elif action == 'disabled':
        action = SimpleAction('UserEvent', UserEvent='UserEvent', peername=peer, dnd='disabled', channel=channel, status='DND disabled',)
    
    client.send_action(action)
    client.logoff()

if __name__ == '__main__':
    initial()

