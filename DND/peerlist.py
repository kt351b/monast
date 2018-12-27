#!/usr/bin/python3.5
# coding: utf-8

#### ------------------------------ INFO ------------------------------ ####
#### Use python3.5 to run this script ###
#### For internal use only. Login and password are passed in clear mode ####

import time
import pymysql
pymysql.install_as_MySQLdb()
import gc
import os
import subprocess
import re
import logging
from logging.handlers import WatchedFileHandler

##### DB definions:
db_name = 'DB_NAME'
host = 'XXX.XXX.XXX.XXX'
user = 'USERNAME'
passwd = 'PASSWORD'
table = 'employee'

# Definions for get_incom() func
# Get from what external number to what internal peer dials
# Incoming phone number for internall number (peer)
# Put your path to extensions.conf here:
exten = '/etc/asterisk/office/dialplan/private.conf'
# EXAMPLE OF EXTENSIONS
#exten => 1234567,201,Dial(SIP/937&SIP/916&SIP/929&SIP/926,60,to)
#exten => XXXXXXX,101,Dial(SIP/974,30,kto)
#exten => XXXXXXX,n(BUSY)-admin,Dial(SIP/937&SIP/915,60,to)
# shablon - extension to parse
#shablon = r'exten\s?\=\>\s\d{7}\,\d{1,3}?\,Dial\(SIP\/\d{3}.*'
shablon = r'exten(?:\s\=|\=)\>(\s|)\d{7}\,(\s|).+?\,(\s|)Dial\(SIP\/\d{3}.*'
# peer_shablon - peer to parse from shablon line
peer_shablon = r'\/\d{3}'
# number_shablon - number to parse from shablon line
number_shablon = r'\d{7}'
peer = []
peernumber = {}

# Create list of peers (peer_list):
peer_list = []

# ----- logger settings:
logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# ---- syslog file settings:
# fh = logging.FileHandler('/var/log/peerlist.log')
fh = logging.handlers.WatchedFileHandler('/var/log/peerlist.log')
fh.setLevel(logging.INFO)  # For log-file output use logging.info to write to log
fh.setFormatter(formatter)
# ---- terminal log output settings:
ch = logging.StreamHandler()
ch.setFormatter(formatter)
# --- How to use DEBUG mode:
# --- For terminal output use logging.debug.
# --- Uncomment this line for debug only! Don't forget to comment this line back:
# logger.setLevel(logging.DEBUG)
# --- And comment this line:
logger.setLevel(logging.INFO)
# --- And don't forget to get it all back :)
# --- End of DEBUG mode block
logger.addHandler(fh)
logger.addHandler(ch)


def db_connect():
    try:
        db = pymysql.connect(host=host, user=user, passwd=passwd, db=db_name, charset='utf8mb4')
        cursor = db.cursor()
        return cursor, db
    except pymysql.err.OperationalError:
        i = 1
        while i < 3:
            try:
                db = pymysql.connect(host=host, user=user, passwd=passwd, db=db_name, charset='utf8mb4')
                cursor = db.cursor()
                return cursor, db
            except (pymysql.err.OperationalError, pymysql.InterfaceError):
                logging.debug("Maybe no connection to DB while db_connect func. Reconnection. Attempt - {}".format(i))
                logging.info("Maybe no connection to DB while db_connect func. Reconnection. Attempt - {}".format(i))
                i+=1
                time.sleep(2)
                continue
        logging.debug("No connection to DB while db_connect func. Check DB definitions. Exiting!")
        logging.info("No connection to DB while db_connect func. Check DB definitions. Exiting!")
        raise SystemExit(1)

# get peer, callerid, description, phone and ip ( mac-address also)
# and insert these data to DB
def get_info():

    data = subprocess.run(['asterisk', '-x sip show peers'], stdout=subprocess.PIPE)
#    data.stdout
    data = data.stdout.decode('utf-8')
    logging.debug("data: %s " % data)

    for line in data.splitlines():
        if line.startswith('9'):
            logging.debug("line in data: %s " % line)

            if '/' in line:
                peer = line.split('/', 1)[0]
                peer_list.append(peer)
            else:
                peer = line.split(' ', 1)[0]
                peer_list.append(peer)
    logging.debug("peer_list:\n\t %s " % peer_list)

    # Get additional data about peer (get peer from peer_list)
    del data
    description = 0
    callerid = 0
    phone = 0
    mac = 0
    ip = 0

    for peer in peer_list:
        arg2 = "-x sip show peer " + str(peer)
        data = subprocess.run(['asterisk', arg2], stdout=subprocess.PIPE)
        data.stdout
        data = data.stdout.decode('utf-8')
        logging.debug("peer: %s, data: %s" % (peer, data))

        for line in data.splitlines():
            # logging.debug("line in data: %s " %line )

            if line.startswith('  Description'):
                logging.debug("Before split --- Description: %s " % line)
                description = line.split(': ')[1]
                logging.debug("peer: %s " % peer)
                logging.debug("description: %s " % description)

            if line.startswith('  Callerid'):
                logging.debug("Before split --- Callerid: %s " % line)
                callerid = line.split(': ')[1]
                logging.debug("callerid: %s " % callerid)

            if line.startswith('  Useragent'):
                logging.debug("Before split --- Useragent (phone): %s " % line)
                phone = line.split(': ')[1]
                logging.debug("phone: %s " % phone)

            if line.startswith('  Addr->IP'):
                logging.debug("Before split --- Addr->IP (ip): %s " % line)
                ip = line.split(': ')[1]
                ip = ip.split(':', )[0]
                logging.debug("ip: %s " % ip)

                # Need to be in the same subnetwork to get mac:
            #  if ip != '(null)':
            #      args_param = "-c 1 -I ens18 " + str(ip)
            #      args_ip = "arping " + args_param
            #      logging.debug("args_ip: %s " %args_ip )
            #      p = os.popen(args_ip)
            #      data_mac = p.read()
            #      logging.debug("data_mac: %s " %data_mac )
            #
            #      for line in data_mac.splitlines():
            #          logging.debug("line in data: %s " %line )
            #
            #          if 'bytes' in line:
            #              mac = line.split('from ')[1]
            #              mac = mac.split(' (')[0]
            #              logging.debug("mac: %s " %mac )

        db_data = (peer, description, callerid, phone, ip)
        # db_data = (peer, description, callerid, phone, ip, mac)
        cursor, db = db_connect()
        check = """select 1 from %(table)s where peer = '%(peer)s' limit 1""" % {"table": table, "peer": peer}
        cursor.execute(check)
        peer_exists = cursor.fetchone()

        if peer_exists:
            logging.info("Peer %s exists! Updating peer. Peer data:\n\t%s\n" % (peer, (db_data,)))
            # without mac:
            sql = """UPDATE %(table)s SET description = '%(description)s',
                                         callerid = '%(callerid)s', 
                                         phone = '%(phone)s', 
                                         ip = '%(ip)s' 
                                         where peer = '%(peer)s'""" % {
                "table": table,
                "peer": peer,
                "description": description,
                "callerid": callerid,
                "phone": phone,
                "ip": ip}
                # #with mac:
                # sql = """UPDATE %(table)s SET description = '%(description)s',
                #                              callerid = '%(callerid)s',
                #                              phone = '%(phone)s',
                #                              ip = '%(ip)s',
                #                              mac = '%(mac)s'
                #                              where peer = '%(peer)s'""" %{
                #                                      "table":table,
                #                                      "peer":peer,
                #                                      "description":description,
                #                                      "callerid":callerid,
                #                                      "phone":phone,
                #                                      "ip":ip,
                #                                      "mac":mac}


            cursor.execute(sql)
            db.commit()
            db.close()

        else:
            logging.info("New peer %s. Peer data:\n\t%s\n" % (peer, (db_data,)))
            # without mac:
            sql = """INSERT INTO %(table)s(peer, description, callerid, phone, ip)
                VALUES ('%(peer)s', '%(description)s', '%(callerid)s', '%(phone)s', '%(ip)s')""" % {
                "table":table, 
                "peer": peer,
                "description": description,
                "callerid": callerid,
                "phone": phone,
                "ip": ip}
            # #with mac:
            #  sql = """INSERT INTO %(table)s(peer, description, callerid, phone, ip, mac)
            #      VALUES ('%(peer)s', '%(description)s', '%(callerid)s', '%(phone)s', '%(ip)s', '%(mac)s')
            #              """%{"table":table, "peer":peer, "description":description, "callerid":callerid, "phone":phone, "ip":ip, "mac":mac}
            cursor.execute(sql)
            db.commit()
            db.close()
    gc.collect()

def func_existnumb(number, peerN):
    number_list = []
    number_list.append(''.join(number))
    # existnumb - list of numbers from peernumber[peerN]
    existnumb = peernumber.get(peerN)
    # if number is in existnumb[] - NOP
    # else - append number to peernumber[peerN] numbers list
    if existnumb:
        if not set(number).issubset(set(existnumb)):
            value = peernumber[peerN]
            value.append(''.join(number))
            peernumber[peerN] = value
    else:
        peernumber[peerN] = number_list
        peer.append(peerN)

def get_number():
    if os.path.exists(exten):
        f = open(exten, 'r')
    else:
        print('No such file!')

    for line in f:
        if re.match(shablon,line) is not None:
           # print('string matched =', line)
            # number[] = XXXXXXX from line - exten => XXXXXXX,201,Dial(SIP/937&SIP/916,60,to)
            number = re.findall(number_shablon, line)
            # peer1 - peers in line - Dial(SIP/937&SIP/916,60,to). peer1 = 937, 916
            peer1 = line.split('SIP')
            for i in peer1[1::]:
                peer2 = re.findall(peer_shablon, i)
                if peer2 is not None:
                    peer2 = ''.join(peer2).split('/')
                    func_existnumb(number, ''.join(peer2[-1::]))

    cursor, db = db_connect()
    for i in peer:
        number = peernumber.get(i)
        numb = ', '.join(number)
        sql = """UPDATE %(table)s SET incoming= '(%(number)s)' WHERE peer='%(peer)s'""" %{
            "table":table,
            "number":numb,
            "peer":i}
        cursor.execute(sql)
        db.commit()
    db.close()
    #print('list of peers = ', sorted(peer))
    #print('tuple = ', sorted(peernumber.items()))
   


def initial():
    #cursor, db = db_connect()
    try:
        get_info()
        get_number()
    except pymysql.err.OperationalError:
        db_connect()
    except (pymysql.err.ProgrammingError, pymysql.err.DataError, pymysql.err.IntegrityError) as error:
        logging.debug("Something went wrong with query!")
        logging.info("Something went wrong with query!")
        logging.debug(error)
        logging.info(error)
    #db.close()

if __name__ == '__main__':
    initial()

