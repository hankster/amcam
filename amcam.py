#! /usr/bin/env python
"""
amcam.py -- A Python program to download media files from an Amcrest camera.

Sample usage:

 amcam.py -m mp4 -s "2020-10-10 12:00:00" -e "2020-10-10 23:59:59"

Complete specification:

 amcam.py -a addr:port -c channel -d -e endtime -f filename -h -m media -n number -p password -s starttime -u user -v --addr=ip:port --channel=channel --debug --end=endtime --file=filename --help --media=media --number=number --password=password --start=starttime --user=user --version

 where

 -a, --addr           Camera IP address
 -c, --channel        Channel
 -d, --debug          Turn debug statements on
 -e, --end-time       End time for search
 -f, --file           Input filename (not used)
 -h, --help           Print usage information
 -m, --media          Media type
 -p, --password       Password
 -n, --number         Maximum number of foles to request
 -s, --start          Start time for search
 -u, --user           Username
 -v, --version        Report program version

Copyright (2020) H. S. Magnuski
All rights reserved

"""

import sys
import os, os.path
import time
import getopt
import string
import math
import random
import requests
from requests.auth import HTTPBasicAuth
from requests.auth import HTTPDigestAuth

# Command line parameters
addr = '192.168.0.100:80'
channel = 0
debug = False
end_time = ''
filename = ''
media_type = 'jpg'
password = '123456'
start_time = ''
user = 'admin'

# Other global parameters
timeout = 180
number_files_max = 100
total_files_found = 0

def Usage():
    print('Usage:  amcam.py -a addr:port -c channel -d -e endtime -f filename -h -m media -n number -p password -s starttime -u user -v --addr=ip:port --channel=channel --debug --end=endtime --file=filename --help --media=media --number=number --password=password --start=starttime --user=user --version')

# Action factory.create
def factoryCreate(auth):

    print('Amcam - factory.create')
    try:
        factory = requests.get('http://' + addr + '/cgi-bin/mediaFileFind.cgi?action=factory.create', auth=auth, timeout=timeout) 
    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as err:
        print('Amcam - factoryCreate Error %s' % err)
        sys.exit(-1)
    if factory.status_code != 200:
        print('Amcam - factoryCreate status code %d' % factory.status_code)
        sys.exit(factory.status_code)
    if len(factory.text) >= 2:
        factory_object = factory.text.split('=')[1].strip()
        print('Amcam - factory.create object id = %s' % factory_object)
        if len(factory.cookies) > 0:
            if debug:
                for c in factory.cookies:
                    print(c.name, c.value)
            cookies = factory.cookies
        else:
            if debug:
                print('Amcam - no factory.create cookies')
    return factory_object

# Action factory.close
def factoryClose(factory_object, auth):

    print('Amcam - factory.close object %s' % factory_object)
    try:
        ok = requests.get('http://' + addr + '/cgi-bin/mediaFileFind.cgi?action=close&object={0}'.format(factory_object), auth=auth, timeout=timeout)
    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as err:
        print('Amcam - factoryClose Error %s' % err)
        sys.exit(-1)

# Action findFile
def findFile(factory_object, channel, st, et, media, auth):
                
    print('Amcam - findFile from %s to %s with media %s on channel %d' % (st, et, media, channel))
    try:
        response = requests.get('http://' + addr + '/cgi-bin/mediaFileFind.cgi?action=findFile&object={0}&condition.Channel={1}&condition.StartTime={2}&condition.EndTime={3}&condition.Types[0]={4}'.format(factory_object, channel, st, et, media), auth=auth, timeout=timeout)
        if response.status_code != 200:
            print('Amcam - findFile status code %d' % response.status_code)
            return False
    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as err:
        print('Amcam - findFile Error %s' % err)
        return False
    if len(response.cookies) > 0:
        if debug:
            for c in response.cookies:
                print(c.name, c.value)
        cookies = response.cookies
    else:
        if debug:
            print('Amcam - no findFile cookies')

    if debug:
        print('findFile: %s' % response.text)
 
    if 'OK' in response.text:
        return True
    else:
        print('Amcam - findFile not OK: %s' % response.text)
        return False

# Action findNextFile
def findNextFile(factory_object, number_files, auth, cookies):

#    found=1
#    items[0].Channel=0
#    items[0].Cluster=0
#    items[0].Compressed=false
#    items[0].Disk=0
#    items[0].Duration=0
#    items[0].EndTime=2020-09-17 11:10:52
#    items[0].Events[0]=VideoMotion
#    items[0].FilePath=/mnt/sd/2020-09-17/001/jpg/11/10/52[M][0@0][0].jpg
#    items[0].Flags[0]=Event
#    items[0].Length=982248
#    items[0].Overwrites=0
#    items[0].Partition=0
#    items[0].Redundant=false
#    items[0].Repeat=0
#    items[0].StartTime=2020-09-17 11:10:52
#    items[0].Summary.TrafficCar.PlateColor=Yellow
#    items[0].Summary.TrafficCar.PlateNumber= 
#    items[0].Summary.TrafficCar.PlateType=Yellow
#    items[0].Summary.TrafficCar.Speed=60
#    items[0].Summary.TrafficCar.VehicleColor=White
#    items[0].SummaryOffset=0
#    items[0].Type=jpg
#    items[0].WorkDir=/mnt/sd
#    items[0].WorkDirSN=0

    global total_files_found

    print('Amcam - findNextFile - %d files' % number_files)
    try:
        files = requests.get('http://' + addr + '/cgi-bin/mediaFileFind.cgi?action=findNextFile&object={0}&count={1}'.format(factory_object, number_files), auth=auth, timeout=timeout, cookies=cookies)
    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as err:
        print('Amcam - findNextFile Error %s' % err)
        return -1

    files = files.text.strip()
    if debug:
        print(files)

    l = files.split('\n')
    mediafile = ''
    number_found = 0
    number_downloaded = 0

    for line in l:
        line = line.decode().strip()
        if debug:
            print('Next file line [%s]' % line)
        if 'found' in line:
            number_found = int(line.split('=')[1])
            print('Amcam - found %d files.' % number_found)
            total_files_found += number_found
            if number_found == 0:
                return number_found
        if 'FilePath' in line:
            path = line.split('=')[1]
            if 'ftp://' in path:
                mediafile = ''
                print('Amcam - file is in ftp directory %s' % path)
            else:
                cmd = 'http://' + addr + '/cgi-bin/RPC_Loadfile'+path
                print('Amcam - running: ' + cmd)
                retries = 0
                while True:
                    try:
                        resp = requests.get(cmd, auth=auth, timeout=timeout, cookies=cookies)
                        mediafile = '-'.join(cmd.split(os.path.sep)[-6:])
                        with open(mediafile, 'wb') as out:
                            out.write(resp.content)
                        break
                    except requests.exceptions.ReadTimeout:
                        print('Amcam - Read Timeout')
                        retries += 1
                        if retries == 3:
                            print('Amcam - retry count exceeded. Aborting.')
                            return -1
                    except requests.exceptions.ConnectionError:
                        print('Amcam - Connection Error')
                        retries += 1
                        if retries == 3:
                            print('Amcam - retry count exceeded. Aborting.')
                            return -1
        if 'EndTime' in line:
            end = line.split('=')[1]
        if 'StartTime' in line:
            start = line.split('=')[1]
            start_name = start[0:10] + ' ' + start[11:13] + '.' + start[14:16] + '.' + start[17:19] + '.' + media_type
            if mediafile != '':
                os.rename(mediafile, start_name)
                number_downloaded += 1
                print('Amcam - received (%d/%d) file %s' % (number_downloaded, number_found, start_name))

    # If the return count is less than the requested number of files, we've exhausted the search space 
    if number_found < number_files:
        print('Amcam - number of files found: %d. Search is over.' % total_files_found)
        return 0

    end_seconds = int(time.mktime(time.strptime(end, '%Y-%m-%d %H:%M:%S')))
    return end_seconds

#
# Main program starts here
#

def main():

    global start_time, end_time
    
    authb = HTTPBasicAuth(user, password)
    authd = HTTPDigestAuth(user, password)
    #DHLangCookie30=English; username=admin; DHVideoWHMode=Adaptive%20Window; DhWebClientSessionID=55853819
    #cookies = {'DHLangCookie30':'English', 'username':'admin', 'DHVideoWHMode':'Adaptive Window', 'DhWebClientSessionID':'55853819', 'DhWebCookie':'long goofy string'}
    cookies = {}

    # Cleanup times - add HH:MM:SS if missing, force colons in string
    #2020-10-10 00:00:00

    if start_time == '':
        Usage()
        sys.exit(-1)

    if end_time == '':
        end_time = start_time[0:10]

    if len (start_time) < 19:
        start_time = start_time + ' 00:00:00'
    start_time = start_time[0:10] + ' ' + start_time[11:13] + ':' + start_time[14:16] + ':' + start_time[17:19]

    if len(end_time) < 19:
        end_time = end_time + ' 23:59:59'
    end_time = end_time[0:10] + ' ' + end_time[11:13] + ':' + end_time[14:16] + ':' + end_time[17:19]

    stime = int(time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S')))
    etime = int(time.mktime(time.strptime(end_time, '%Y-%m-%d %H:%M:%S')))

    while (stime < etime):

        factory_number = factoryCreate(authd)

        results = findFile(factory_number, channel, start_time, end_time, media_type, authd)
        if results == False:
            factoryClose(factory_number, authd)
            sys.exit(-1)
        stime = findNextFile(factory_number, number_files_max, authd, cookies)
        if stime < 0:
            factoryClose(factory_number, authd)
            sys.exit(-1)
        if stime == 0:
            factoryClose(factory_number, authd)
            break
        stime += 1
        start_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stime))
        print('Amcam - new start time = %s' % start_time)

        factoryClose(factory_number, authd)


if __name__=='__main__':


    #
    # Get options and call the main program
    #                                                                                            

    try:
        options, args = getopt.getopt(sys.argv[1:], 'a:c:de:f:hm:n:p:s:u:v', ['addr=', 'channel=', 'debug', 'end=', 'file=', 'help', 'media=', 'number=', 'password=', 'start=', 'user=','version'])
    except getopt.GetoptError:
        Usage()
        sys.exit(2)

    for o, a in options:
        if o in ('-a', '--addr'):
            addr = a
        if o in ('-c', '--channel'):
            channel = int(a)
        if o in ('-d', '--debug'):
            debug = True
        if o in ('-e', '--end'):
            end_time = a
        if o in ('-f', '--file'):
            filename = a
        if o in ('-h', '--help'):
            Usage()
            sys.exit(0)
        if o in ('-m', '--media'):
            media_type = a
        if o in ('-n', '--number'):
            number_files_max = int(a)
        if o in ('-p', '--password'):
            password = a
        if o in ('-s', '--start'):
            start_time = a
        if o in ('-u', '--user'):
            user = a
        if o in ('-v', '--version'):
            print('amcam.py Version 1.0')
            sys.exit(0)
        
    main()
    sys.exit(0)
