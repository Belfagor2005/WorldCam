#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

PY3 = sys.version_info.major >= 3
print("Update.py")


def upd_done():
    from os import popen
    installUrl = 'https://raw.githubusercontent.com/Belfagor2005/WorldCam/main/installer.sh'
    cmd00 = 'wget -q "--no-check-certificate" ' + installUrl + ' -O - | /bin/sh'
    popen(cmd00)
    # cmd01 = "wget --no-cache --no-dns-cache  http://patbuweb.com/worldcam/worldcam.tar -O /tmp/worldcam.tar --post-data='action=purge';tar -xvf /tmp/worldcam.tar -C /;rm -rf /tmp/worldcam.tar"
    # cmd02 = "wget --no-check-certificate --no-cache --no-dns-cache  -U 'Enigma2 - worldcam Plugin' -c 'http://patbuweb.com/worldcam/worldcam.tar' -O '/tmp/worldcam.tar' --post-data='action=purge';tar -xvf /tmp/worldcam.tar -C /;rm -rf /tmp/worldcam.tar"
    # cmd22 = 'find /usr/bin -name "wget"'
    # cmd10 = 'rm -rf /tmp/worldcam.tar'
    # res = popen(cmd22).read()
    # if 'wget' not in res.lower():
        # if os.path.exists('/etc/opkg'):
            # cmd23 = 'opkg update && opkg install wget'
        # else:
            # cmd23 = 'apt-get update && apt-get install wget'
        # popen(cmd23)
    # try:
        # popen(cmd02)
    # except:
        # popen(cmd01)
    # popen(cmd10)
    # # system('rm -rf /tmp/worldcam.tar')
    return
