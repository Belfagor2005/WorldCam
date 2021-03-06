#!/usr/bin/python
# -*- coding: utf-8 -*-
#######################################################################
#   Enigma2 plugin Worldcam is coded by Lululla and Pcd               #
#   This is free software; you can redistribute it and/or modify it.  #
#   But no delete this message support on forum linuxsat-support      #
#######################################################################
#06/06/2021
#Info http://t.me/tivustream
from __future__ import print_function
from Components.MenuList import MenuList
from Components.Label import Label
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.Input import Input
from Components.Pixmap import Pixmap
from Components.FileList import FileList
from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBarGenerics import *
from Screens.InfoBar import MoviePlayer, InfoBar
from Screens.Console import Console
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import ActionMap, NumberActionMap
from Components.Button import Button
from Components.SelectionList import SelectionList, SelectionEntryComponent
from Components.ScrollLabel import ScrollLabel
import Components.PluginComponent
from Screens.InputBox import InputBox
from twisted.web.client import getPage, downloadPage
import os, re, sys
from enigma import eServiceReference
from enigma import eServiceCenter
from enigma import getDesktop
from Plugins.Extensions.WorldCam.lib.Utils import showlist, webcamList
from Tools.Directories import fileExists
from Components.AVSwitch import AVSwitch
from enigma import *
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigText, ConfigYesNo, getConfigListEntry
from Components.config import NoSave
from Components.ConfigList import ConfigListScreen
from Screens.Standby import TryQuitMainloop
from os import path
from os import system
import socket
import ssl
from sys import version_info
import six

THISPLUG  = os.path.dirname(sys.modules[__name__].__file__)
path = THISPLUG + '/channels/'
DESKHEIGHT = getDesktop(0).size().height()
version = '3.6_r1'
config.plugins.WorldCam = ConfigSubsection()
config.plugins.WorldCam.vlcip = ConfigText('192.168.1.2', False)

wDreamOs = False
PY3 = sys.version_info.major >= 3
print('Py3: ',PY3)
from six.moves.urllib.request import urlopen
from six.moves.urllib.request import Request
from six.moves.urllib.error import HTTPError, URLError
from six.moves.urllib.request import urlretrieve    
from six.moves.urllib.parse import urlparse
from six.moves.urllib.parse import parse_qs
from six.moves.urllib.request import build_opener

import six.moves.urllib.request
import six.moves.urllib.parse
import six.moves.urllib.error

try:
    from enigma import eMediaDatabase
    wDreamOs = True
except:
    wDreamOs = False

try:
    import http.client
    from urllib.request import HTTPPasswordMgrWithDefaultRealm
    from urllib.request import HTTPBasicAuthHandler
except:
    import httplib
    import urlparse
    import urllib2
    from urllib2 import HTTPPasswordMgrWithDefaultRealm
    from urllib2 import HTTPBasicAuthHandler

if sys.version_info >= (2, 7, 9):
    try:
        import ssl
        sslContext = ssl._create_unverified_context()
    except:
        sslContext = None

def ssl_urlopen(url):
    if sslContext:
        return urlopen(url, context=sslContext)
    else:
        return urlopen(url)

def checkStr(txt):
    if PY3:
        if isinstance(txt, type(bytes())):
            txt = txt.decode('utf-8')
    else:
        if isinstance(txt, type(six.text_type())):
            txt = txt.encode('utf-8')
    return txt
       
def getUrl2(url, referer):
        try:
            req = urllib.request.Request(url)
        except:
            req = urllib2.Request(url)       
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        req.add_header('Referer', referer)
        try:
            try:
                response = urllib.request.urlopen(req)
            except:       
                response = urllib2.urlopen(req)
            link=response.read()
            response.close()
            return link
        except:
            import ssl
            gcontext = ssl._create_unverified_context()
            try:
                response = urllib.request.urlopen(req)
            except:       
                response = urllib2.urlopen(req)
            link=response.read()
            response.close()
            return link 
            
def getUrl(url):
        print( "Here in getUrl url =", url)
        try:
               req = urllib.request.Request(url)
        except:
               req = urllib2.Request(url)       
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        try:
            try:
                response = urllib.request.urlopen(req)
            except:       
                response = urllib2.urlopen(req)
            link=response.read()
            response.close()
            return link
        except:
            import ssl
            gcontext = ssl._create_unverified_context()
            try:
                response = urllib.request.urlopen(req)
            except:       
                response = urllib2.urlopen(req)
            link=response.read()
            response.close()
            return link

SKIN_PATH = THISPLUG
HD = getDesktop(0).size()
iconpic = 'plugin.png'

if HD.width() > 1280:
    SKIN_PATH = THISPLUG + '/skin/fhd'
else:
    SKIN_PATH = THISPLUG + '/skin/hd'

class ConfscreenFHD(Screen):
    skin = '\n          <screen name="Confiptv" position="center,center" size="1260,1050" title=" " >\n        <!--ePixmap position="0,0" zPosition="-10" size="930,1080" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/WebMedia/icons/menu.png" /-->\n        <!--widget name="title" position="1020,75" size="600,75" zPosition="3" halign="center" foregroundColor="#e5b243" backgroundColor="black" font="Regular;60" transparent="1" /-->\n        <ePixmap name="red"    position="0,975"   zPosition="2" size="210,60" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />\n\t<ePixmap name="green"  position="210,975" zPosition="2" size="210,60" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />\n\n\t<widget name="key_red" position="0,975" size="210,60" valign="center" halign="center" zPosition="4"  foregroundColor="#ffffff" font="Regular;30" transparent="1" shadowColor="#25062748" shadowOffset="-2,-2" /> \n\t<widget name="key_green" position="210,975" size="210,60" valign="center" halign="center" zPosition="4"  foregroundColor="#ffffff" font="Regular;30" transparent="1" shadowColor="#25062748" shadowOffset="-2,-2" /> \n\n\t<widget name="config" position="75,120" size="825,210" scrollbarMode="showOnDemand" />\n\n</screen>'

class ConfscreenHD(Screen):
    skin = '\n        <screen name="Confiptv" position="center,center" size="840,700" title=" " >\n        <!--ePixmap position="0,0" zPosition="-10" size="620,720" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/WebMedia/icons/menu.png" /-->\n        <!--widget name="title" position="680,50" size="400,50" zPosition="3" halign="center" foregroundColor="#e5b243" backgroundColor="black" font="Regular;40" transparent="1" /-->\n        <ePixmap name="red"    position="0,650"   zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />\n\t<ePixmap name="green"  position="140,650" zPosition="2" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />\n\n\t<widget name="key_red" position="0,650" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="#ffffff" font="Regular;20" transparent="1" shadowColor="#25062748" shadowOffset="-2,-2" /> \n\t<widget name="key_green" position="140,650" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="#ffffff" font="Regular;20" transparent="1" shadowColor="#25062748" shadowOffset="-2,-2" /> \n\n\t<widget name="config" position="50,80" size="550,140" scrollbarMode="showOnDemand" />\n\n</screen>'

class IPTVConf(ConfigListScreen, Screen):

    def __init__(self, session, args = 0):
        Screen.__init__(self, session)
        self.session = session
        self.setup_title = _('Plugin Configuration')
        self['title'] = Button(self.setup_title)
        if DESKHEIGHT > 1000:
            self.skin = ConfscreenFHD.skin
        else:
            self.skin = ConfscreenHD.skin
        cfg = config.plugins.WorldCam
        self.list = [getConfigListEntry(_('vlc server ip'), cfg.vlcip)]
        ConfigListScreen.__init__(self, self.list, session=self.session, on_change=self.changedEntry)
        self['status'] = Label()
        self['statusbar'] = Label()
        self['key_red'] = Button(_('Exit'))
        self['key_green'] = Button(_('Save'))
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions', 'TimerEditActions'], {'red': self.cancel,
         'green': self.save,
         'cancel': self.cancel,
         'ok': self.save}, -2)
        self.onChangedEntry = []

    def changedEntry(self):
        for x in self.onChangedEntry:
            x()

    def getCurrentEntry(self):
        return self['config'].getCurrent()[0]

    def getCurrentValue(self):
        return str(self['config'].getCurrent()[1].getText())

    def createSummary(self):
        from Screens.Setup import SetupSummary
        return SetupSummary

    def cancel(self):
        for x in self['config'].list:
            x[1].cancel()
        self.close()

    def save(self):
        print('Here in Save')
        self.saveAll()
        self.session.open(TryQuitMainloop, 3)
        self.close()

class Webcam1(Screen):

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = SKIN_PATH + '/Webcam1.xml'
        f = open(skin, 'r')
        self.skin = f.read()
        f.close()
        self.list = []
        self['list'] = webcamList([])
        self['info'] = Label()
        self['key_red'] = Button(_('Exit'))
        self['key_green'] = Button(_('Select'))
        self['info'].setText('HOME VIEW')
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions', 'TimerEditActions'], {'red': self.close,
         'green': self.okClicked,
         'cancel': self.cancel,
         'ok': self.okClicked}, -2)
        self.srefOld = self.session.nav.getCurrentlyPlayingServiceReference()
        self.onLayoutFinish.append(self.openTest)

    def openTest(self):
        self.names = []
        self.urls = []
        self.names.append('User Lists')
        self.urls.append('http://worldcam.eu/')
        self.names.append('skylinewebcams.com')
        self.urls.append('https://www.skylinewebcams.com/')
        self.names.append('livecameras.gr')
        self.urls.append('http://www.livecameras.gr/')
        showlist(self.names, self['list'])

    def okClicked(self):
        idx = self['list'].getSelectionIndex()
        if idx is None:
            return
        name = self.names[idx]
        url = self.urls[idx]
        if 'User' in name:
            self.session.open(Webcam2)
        elif 'skylinewebcams' in name:
            self.session.open(Webcam4)
        elif 'livecameras' in name:
            self.session.open(Webcam8)

    def cancel(self):
        Screen.close(self, False)

class Webcam8(Screen):

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = SKIN_PATH + '/Webcam1.xml'
        f = open(skin, 'r')
        self.skin = f.read()
        f.close()
        self.list = []
        self['list'] = webcamList([])
        self['info'] = Label()
        self['info'].setText('livecameras')
        self['key_red'] = Button(_('Exit'))
        self['key_green'] = Button(_('Select'))
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions', 'TimerEditActions'], {'red': self.close,
         'green': self.okClicked,
         'cancel': self.cancel,
         'ok': self.okClicked}, -2)
        self.srefOld = self.session.nav.getCurrentlyPlayingServiceReference()
        self.onLayoutFinish.append(self.openTest)

    def openTest(self):
        self.names = []
        self.urls = []
        content = getUrl('http://www.livecameras.gr/')
        regexvideo = '<a class="item1" href="/(.*?)".*?data-title="(.*?)"'
        match = re.compile(regexvideo, re.DOTALL).findall(content)
        pic = ' '
        for url, name in match:
            url1 = 'https://www.livecameras.gr/' + url
            self.names.append(name)
            self.urls.append(url1)
        showlist(self.names, self['list'])

    def okClicked(self):
        idx = self['list'].getSelectionIndex()
        if idx is None:
            return
        else:
            url = self.urls[idx]
            name = self.names[idx]
            self.session.open(Playstream1, name, url)


    def cancel(self):
        Screen.close(self, False)

class Webcam8(Screen):

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = SKIN_PATH + '/Webcam1.xml'
        f = open(skin, 'r')
        self.skin = f.read()
        f.close()
        self.list = []
        self['list'] = webcamList([])
        self['info'] = Label()
        self['info'].setText('livecameras')
        self['key_red'] = Button(_('Exit'))
        self['key_green'] = Button(_('Select'))
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions', 'TimerEditActions'], {'red': self.close,
         'green': self.okClicked,
         'cancel': self.cancel,
         'ok': self.okClicked}, -2)
        self.srefOld = self.session.nav.getCurrentlyPlayingServiceReference()
        self.onLayoutFinish.append(self.openTest)

    def openTest(self):
        self.names = []
        self.urls = []
        content = getUrl('http://www.livecameras.gr/')
        content = six.ensure_str(content)
        print('content: ',content)
        regexvideo = 'a class="item1" href="(.*?)".*?data-title="(.*?)"'
        match = re.compile(regexvideo, re.DOTALL).findall(content)
        pic = ' '
        for url, name in match:
            url1 = 'http:' + url
            url1 = checkStr(url1)
            name = checkStr(name)
            self.names.append(name)
            self.urls.append(url1)
        showlist(self.names, self['list'])

    def okClicked(self):
        idx = self['list'].getSelectionIndex()
        if idx is None:
            return
        else:
            url = self.urls[idx]
            name = self.names[idx]
            self.session.open(Playstream1, name, url)

    def cancel(self):
        Screen.close(self, False)

class Webcam2(Screen):

    def __init__(self, session):
        Screen.__init__(self, session)    
        self.session = session
        skin = SKIN_PATH + '/Webcam1.xml'
        f = open(skin, 'r')
        self.skin = f.read()
        f.close()
        self.list = []
        self['list'] = webcamList([])
        self['info'] = Label()
        self['info'].setText('UserList')
        self['key_red'] = Button(_('Exit'))
        self['key_green'] = Button(_('Select'))
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions', 'TimerEditActions'], {'red': self.close,
         'green': self.okClicked,
         'cancel': self.cancel,
         'ok': self.okClicked}, -2)
        self.srefOld = self.session.nav.getCurrentlyPlayingServiceReference()
        self.onLayoutFinish.append(self.openTest)

    def openTest(self):
        uLists = THISPLUG + '/Playlists'
        self.names = []
        for root, dirs, files in os.walk(uLists):
            for name in files:
                self.names.append(name)
        showlist(self.names, self['list'])

    def okClicked(self):
        idx = self['list'].getSelectionIndex()
        if idx is None:
            return
        name = self.names[idx]
        self.session.open(Webcam3, name)

    def cancel(self):
        Screen.close(self, False)

class Webcam3(Screen):

    def __init__(self, session, name):
        Screen.__init__(self, session)
        self.session = session
        skin = SKIN_PATH + '/Webcam1.xml'
        f = open(skin, 'r')
        self.skin = f.read()
        f.close()
        self.name = name
        self.list = []
        self['list'] = webcamList([])
        self['info'] = Label()
        self['info'].setText('UserList')
        self['key_red'] = Button(_('Exit'))
        self['key_green'] = Button(_('Select'))
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions', 'TimerEditActions'], {'red': self.close,
         'green': self.okClicked,
         'cancel': self.cancel,
         'ok': self.okClicked}, -2)
        self.srefOld = self.session.nav.getCurrentlyPlayingServiceReference()
        self.onLayoutFinish.append(self.openTest)

    def openTest(self):
        uLists = THISPLUG + '/Playlists'
        file1 = uLists + '/' + self.name
        print('Here in showContentA2 file1 = ', file1)
        self.names = []
        self.urls = []
        f1 = open(file1, 'r')
        for line in f1.readlines():
            if '##' not in line:
                continue
            line = line.replace('\n', '')
            items = line.split('###')
            name = items[0]
            url = items[1]
            self.names.append(name)
            self.urls.append(url)
        showlist(self.names, self['list'])

    def okClicked(self):
        idx = self['list'].getSelectionIndex()
        if idx is None:
            return
        name = self.names[idx]
        url = self.urls[idx]
        self.session.open(Playstream1, name, url)
        return
            
    def cancel(self):
        Screen.close(self, False)

class Webcam4(Screen):

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = SKIN_PATH + '/Webcam1.xml'
        f = open(skin, 'r')
        self.skin = f.read()
        f.close()
        self.list = []
        self['list'] = webcamList([])
        self['info'] = Label()
        self['info'].setText('SkylineWebcams')
        self['key_red'] = Button(_('Exit'))
        self['key_green'] = Button(_('Select'))
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions', 'TimerEditActions'], {'red': self.close,
         'green': self.okClicked,
         'cancel': self.cancel,
         'ok': self.okClicked}, -2)
        self.srefOld = self.session.nav.getCurrentlyPlayingServiceReference()
        self.onLayoutFinish.append(self.openTest)

    def openTest(self):
        self.names = []
        self.urls = []
        content = getUrl('http://www.skylinewebcams.com/')
        content = six.ensure_str(content)
        print('content: ',content)
        regexvideo = 'class="ln_css ln-(.*?)" alt="(.*?)"'
        match = re.compile(regexvideo, re.DOTALL).findall(content)
        items = []
        for url, name in match:
            try:
                url = 'https://www.skylinewebcams.com/' + url + '.html'
            except:
                url = b'https://www.skylinewebcams.com/'  + six.binary_type(url, encoding="utf-8") + b'.html'

            url1 = checkStr(url)
            item = checkStr(name) + "###" + url1
            print('Items sort: ', item)
            items.append(item)
        items.sort()
        for item in items:
            name = item.split('###')[0]
            url1 = item.split('###')[1]
            self.names.append(name)
            self.urls.append(url1)
        showlist(self.names, self['list'])
        
    def okClicked(self):
        idx = self['list'].getSelectionIndex()
        if idx is None:
            return
        else:
            name = self.names[idx]
            url = self.urls[idx]
            self.session.open(Webcam5, name, url)
            return

    def cancel(self):
        Screen.close(self, False)

class Webcam5(Screen):

    def __init__(self, session, name, url):
        Screen.__init__(self, session)
        self.session = session
        skin = SKIN_PATH + '/Webcam1.xml'
        f = open(skin, 'r')
        self.skin = f.read()
        f.close()
        self.list = []
        self['list'] = webcamList([])
        self['info'] = Label()
        self['info'].setText(name)
        self['key_red'] = Button(_('Exit'))
        self['key_green'] = Button(_('Select'))
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions', 'TimerEditActions'], {'red': self.close,
         'green': self.okClicked,
         'cancel': self.cancel,
         'ok': self.okClicked}, -2)
        self.name = name
        self.url = url
        self.srefOld = self.session.nav.getCurrentlyPlayingServiceReference()
        global srefInit
        self.initialservice = self.session.nav.getCurrentlyPlayingServiceReference()
        srefInit = self.initialservice
        self.onLayoutFinish.append(self.openTest)

    def openTest(self):
        self.names = []
        self.urls = []
        content = getUrl(self.url)
        content = six.ensure_str(content)
        start = 0

        n1 = content.find('div class="dropdown-menu mega-dropdown-menu', start)
        n2 = content.find('div class="collapse navbar-collapse', n1) 
        # if wDreamOs:
            # n1 = content.find(b'div class="dropdown-menu mega-dropdown-menu', start)
            # n2 = content.find(b'div class="collapse navbar-collapse', n1)                
        
        content2 = content[n1:n2]
        ctry = self.url.replace('https://www.skylinewebcams.com/', '')
        ctry = ctry.replace('.html', '')
        regexvideo = '<a href="/' + ctry + '/webcam(.*?)">(.*?)</a>'        
        if wDreamOs:      
            regexvideo = b'<a href="/' + ctry.encode("UTF-8") + b'/webcam(.*?)">(.*?)</a>' 
        match = re.compile(regexvideo, re.DOTALL).findall(content2)
        items = []
        for url, name in match:
        
            try:
                url = 'https://www.skylinewebcams.com/' + ctry + '/webcam' + url
            except:
                url = b'https://www.skylinewebcams.com/' + ctry + '/webcam'  + six.binary_type(url, encoding="utf-8")
        
            # url1 = 'https://www.skylinewebcams.com/' + ctry + '/webcam' + url
            url1 = checkStr(url)
            item = checkStr(name) + "###" + url1
            print('Items sort 2: ', item)            
            items.append(item)
        items.sort()
        for item in items:
            name = item.split('###')[0]
            url1 = item.split('###')[1]
            self.names.append(name)
            self.urls.append(url1)
        showlist(self.names, self['list'])

    def okClicked(self):
        idx = self['list'].getSelectionIndex()
        if idx is None:
            return
        else:
            name = self.names[idx]
            url = self.urls[idx]
            self.session.open(Webcam6, name, url)
            return
    def cancel(self):
        Screen.close(self, False)
        
class Webcam6(Screen):

    def __init__(self, session, name, url):
        Screen.__init__(self, session)
        self.session = session
        skin = SKIN_PATH + '/Webcam1.xml'
        f = open(skin, 'r')
        self.skin = f.read()
        f.close()
        self.list = []
        self.name = name
        self.url = url
        self['list'] = webcamList([])
        self['info'] = Label()
        self['info'].setText(name)
        self['key_red'] = Button(_('Exit'))
        self['key_green'] = Button(_('Select'))
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions', 'TimerEditActions'], {'red': self.close,
         'green': self.okClicked,
         'cancel': self.cancel,
         'ok': self.okClicked}, -2)
        self.srefOld = self.session.nav.getCurrentlyPlayingServiceReference()
        self.onLayoutFinish.append(self.openTest)

    def openTest(self):
        self.names = []
        self.urls = []
        content = getUrl(self.url)
        content = six.ensure_str(content)
        stext = self.url.replace('https://www.skylinewebcams.com/', '')
        stext = stext.replace('.html', '')
        stext = stext + '/'
        regexvideo = '><a href="' + stext + '(.*?)".*?alt="(.*?)"'        
        if wDreamOs: 
            # regexvideo = '><a href="' + stext.encode("UTF-8") + '(.*?)".*?alt="(.*?)"'  
            regexvideo = '><a href="' + stext + '(.*?)".*?alt="(.*?)"'              
        match = re.compile(regexvideo, re.DOTALL).findall(content)
        items = []
        for url, name in match:
            try:
                url1 = 'https://www.skylinewebcams.com/' + stext + url
            except:
                url1 = b'https://www.skylinewebcams.com/' + stext + six.binary_type(url, encoding="utf-8")
                
            # url1 = 'https://www.skylinewebcams.com/' + stext + url
            url1 = checkStr(url1)
            item = checkStr(name) + "###" + url1            
            items.append(item)
        items.sort()
        for item in items:
            name = item.split('###')[0]
            url1 = item.split('###')[1]
            self.names.append(name)
            self.urls.append(url1)
        showlist(self.names, self['list'])

    def okClicked(self):
        idx = self['list'].getSelectionIndex()
        if idx is None:
            return
        else:
            url1 = self.urls[idx]
            name = self.names[idx]
            self.getVid(name, url1)
            return

    def getVid(self, name, url):
        content = getUrl(url)
        content = six.ensure_str(content)  
        print('in content getvideo ', content)
        regexvideo = "source:'(.*?)'"
        if wDreamOs:   
            regexvideo = b'source\:\'(.*?)\','        
           
        match = re.compile(regexvideo, re.DOTALL).findall(content)
        
        print('match 0 ', match)
        try:
            url = 'https://hd-auth.skylinewebcams.com/' + match[0]
        except:
            url = b'https://hd-auth.skylinewebcams.com/' +  six.binary_type(match[0], encoding="utf-8")
                
        # url = "https://hd-auth.skylinewebcams.com/" + match[0]
        # if wDreamOs:   
            # url = "https://hd-auth.skylinewebcams.com/" + match[0].decode()        
        print("Here in Test url =", url)
        self.session.open(Playstream1, name, url)

#https://hd-auth.skylinewebcams.com/live.m3u8?a=t6mgjuhfnp8psqh66uch0nnvu1
#https://hd-auth.skylinewebcams.com/live.m3u8?a=f1g2q7u9m75qf2kgdbdrafhif1

    def cancel(self):
        Screen.close(self, False)

class Playstream1(Screen):

    def __init__(self, session, name, url):
        Screen.__init__(self, session)
        self.session = session
        skin = SKIN_PATH + '/Webcam1.xml'
        f = open(skin, 'r')
        self.skin = f.read()
        f.close()
        self.list = []
        self['list'] = webcamList([])
        self['info'] = Label()
        self['info'].setText('Select Player')
        self['key_red'] = Button(_('Exit'))
        self['key_green'] = Button(_('Select'))
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions', 'TimerEditActions'], {'red': self.cancel,
         'green': self.okClicked,
         'back' : self.cancel,
         'cancel': self.cancel,
         'ok': self.okClicked}, -2)
        self.name1 = name
        self.url = url
        print('In Playstream1 self.url =', url)
        global srefInit
        self.initialservice = self.session.nav.getCurrentlyPlayingServiceReference()
        srefInit = self.initialservice
        self.onLayoutFinish.append(self.openTest)

    def openTest(self):
        url = self.url
        self.names = []
        self.urls = []
        self.names.append('Play direct')
        self.urls.append(url)
        self.names.append('Play .m3u8')
        self.urls.append(url)
        self.names.append('Play .ts')
        self.urls.append(url)
        # self.names.append('Preview')
        # self.urls.append(url)
        showlist(self.names, self['list'])

    def okClicked(self):
        idx = self['list'].getSelectionIndex()
        if idx is None:
            return
        self.name = self.names[idx]
        self.url = self.urls[idx]
        if idx == 0:
            self.name = self.names[idx]
            self.url = self.urls[idx]
            print('In playVideo url D=', self.url)
            self.play()
        elif idx == 1:
            print('In playVideo url B=', self.url)
            self.name = self.names[idx]
            self.url = self.urls[idx]
            try:
                os.remove('/tmp/hls.avi')
            except:
                pass
            header = ''
            cmd = 'python "/usr/lib/enigma2/python/Plugins/Extensions/KodiLite/lib/hlsclient.py" "' + self.url + '" "1" "' + header + '" + &'
            print('In playVideo cmd =', cmd)
            os.system(cmd)
            os.system('sleep 3')
            self.url = '/tmp/hls.avi'
            self.play()
        elif idx == 2:
            print('In playVideo url A=', self.url)
            url = self.url
            try:
                os.remove('/tmp/hls.avi')
            except:
                pass

            cmd = 'python "/usr/lib/enigma2/python/Plugins/Extensions/KodiLite/lib/tsclient.py" "' + url + '" "1" + &'
            print('hls cmd = ', cmd)
            os.system(cmd)
            os.system('sleep 3')
            self.url = '/tmp/hls.avi'
            self.name = self.names[idx]
            self.play()

        elif idx == 3:
            self.name = self.names[idx]
            self.url = self.urls[idx]
            print('In playVideo url D=', self.url)
            self.play2()
        else:
            self.name = self.names[idx]
            self.url = self.urls[idx]
            print('In playVideo url D=', self.url)
            self.play()
        return                  

    def playfile(self, serverint):
        self.serverList[serverint].play(self.session, self.url, self.name)

    def play(self):
        desc = ' '
        url = self.url
        name = self.name
        self.session.open(Playstream2, name, url, desc)


    def play2(self):
        desc = ' '
        self['info'].setText(self.name)
        url = self.url
        url = url.replace(':', '%3a')
        print('In WorldCam url =', url)
        ref = '4097:0:1:0:0:0:0:0:0:0:' + url
        sref = eServiceReference(ref)
        print('SREF: ', sref)
        sref.setName(self.name)
        self.session.nav.playService(sref)

    def cancel(self):
        try:
            password_mgr = HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(None, self.hostaddr, '', 'Admin')
            handler = HTTPBasicAuthHandler(password_mgr)
            opener = build_opener(handler)
            f = opener.open(self.hostaddr + '/requests/status.xml?command=pl_stop')
            f = opener.open(self.hostaddr + '/requests/status.xml?command=pl_empty')
        except:
            pass
        self.session.nav.stopService()
        self.session.nav.playService(srefInit)
        self.close()
        return              

        
class Playstream2(Screen, InfoBarMenu, InfoBarBase, InfoBarSeek, InfoBarNotifications, InfoBarShowHide):
    STATE_PLAYING = 1
    STATE_PAUSED = 2

    def __init__(self, session, name, url, desc):
        global SREF
        Screen.__init__(self, session)
        self.skinName = 'Movieplayer'
        title = 'Play'
        self.sref = None
        self['title'] = Button(title)
        self['list'] = MenuList([])
        self['info'] = Label()
        self['key_yellow'] = Button(_(' '))
        InfoBarMenu.__init__(self)
        InfoBarNotifications.__init__(self)
        InfoBarBase.__init__(self)
        InfoBarShowHide.__init__(self)
        try:
            self.init_aspect = int(self.getAspect())
        except:
            self.init_aspect = 0
        self.new_aspect = self.init_aspect
        self['actions'] = ActionMap(['WizardActions',
         'MoviePlayerActions',
         'EPGSelectActions',
         'MediaPlayerSeekActions',
         'ColorActions',
         'InfobarShowHideActions',
         'InfobarSeekActions',
         'InfobarActions'], {'leavePlayer': self.cancel,
         'back': self.cancel,
         'info': self.showinfo,
         'playpauseService': self.playpauseService,
         'yellow': self.subtitles,
         'down': self.av}, -1)
        self.allowPiP = False
        InfoBarSeek.__init__(self, actionmap='MediaPlayerSeekActions')
        self.icount = 0
        self.name = name
        self.url = url
        self.desc = desc
        self.pcip = 'None'
        self.state = self.STATE_PLAYING
        self.srefOld = self.session.nav.getCurrentlyPlayingServiceReference()
        SREF = self.srefOld
        self.onLayoutFinish.append(self.openTest)
        return

    def getAspect(self):
        return AVSwitch().getAspectRatioSetting()

    def getAspectString(self, aspectnum):
        return {0: _('4:3 Letterbox'),
         1: _('4:3 PanScan'),
         2: _('16:9'),
         3: _('16:9 always'),
         4: _('16:10 Letterbox'),
         5: _('16:10 PanScan'),
         6: _('16:9 Letterbox')}[aspectnum]

    def setAspect(self, aspect):
        map = {0: '4_3_letterbox',
         1: '4_3_panscan',
         2: '16_9',
         3: '16_9_always',
         4: '16_10_letterbox',
         5: '16_10_panscan',
         6: '16_9_letterbox'}
        config.av.aspectratio.setValue(map[aspect])
        try:
            AVSwitch().setAspectRatio(aspect)
        except:
            pass

    def av(self):
        temp = int(self.getAspect())

        temp = temp + 1
        if temp > 6:
            temp = 0
        self.new_aspect = temp
        self.setAspect(temp)

    def showinfo(self):
        sTitle = ''
        sServiceref = ''
        try:
            servicename, serviceurl = getserviceinfo(sref)
            if servicename is not None:
                sTitle = servicename
            else:
                sTitle = ''
            if serviceurl is not None:
                sServiceref = serviceurl
            else:
                sServiceref = ''
            currPlay = self.session.nav.getCurrentService()
            sTagCodec = currPlay.info().getInfoString(iServiceInformation.sTagCodec)
            sTagVideoCodec = currPlay.info().getInfoString(iServiceInformation.sTagVideoCodec)
            sTagAudioCodec = currPlay.info().getInfoString(iServiceInformation.sTagAudioCodec)
            message = 'stitle:' + str(sTitle) + '\n' + 'sServiceref:' + str(sServiceref) + '\n' + 'sTagCodec:' + str(sTagCodec) + '\n' + 'sTagVideoCodec:' + str(sTagVideoCodec) + '\n' + 'sTagAudioCodec :' + str(sTagAudioCodec)
            self.mbox = self.session.open(MessageBox, message, MessageBox.TYPE_INFO)
        except:
            pass
        return

    def playpauseService(self):
        if self.state == self.STATE_PLAYING:
            self.pause()
            self.state = self.STATE_PAUSED
        elif self.state == self.STATE_PAUSED:
            self.unpause()
            self.state = self.STATE_PLAYING

    def pause(self):
        self.session.nav.pause(True)

    def unpause(self):
        self.session.nav.pause(False)

    def openTest(self):
        if '5002' in self.url:
            ref = self.url
            sref = eServiceReference(ref)
            sref.setName(self.name)
            self.session.nav.stopService()
            self.session.nav.playService(sref)
        else:
 
            url = self.url
            name = self.name
            name = name.replace(':', '-')
            name = name.replace('&', '-')
            name = name.replace(' ', '-')
            name = name.replace('/', '-')
            name = name.replace(',', '-')

            if url is not None:
                url = str(url)
                url = url.replace(':', '%3a')
                url = url.replace('\\', '/')
                ref = '4097:0:1:0:0:0:0:0:0:0:' + url
                sref = eServiceReference(ref)
                sref.setName(self.name)
                self.session.nav.stopService()
                self.session.nav.playService(sref)
            else:
                return
        return

    def subtitles(self):
        self.session.open(MessageBox, _('Please install script.module.SubSupport.'), MessageBox.TYPE_ERROR, timeout=10)
                                         
    def cancel(self):
        if os.path.exists('/tmp/hls.avi'):
            os.remove('/tmp/hls.avi')
        self.session.nav.stopService()

        self.session.nav.playService(SREF)
        if self.pcip != 'None':
            url2 = 'http://' + self.pcip + ':8080/requests/status.xml?command=pl_stop'

            resp = urlopen(url2)
        if not self.new_aspect == self.init_aspect:
            try:
                self.setAspect(self.init_aspect)
            except:
                pass

        self.close()

    def keyLeft(self):
        self['text'].left()

    def keyRight(self):
        self['text'].right()

    def keyNumberGlobal(self, number):
        self['text'].number(number)

                               
def main(session, **kwargs):
    global _session
    _session = session
    session.open(Webcam1)


def Plugins(**kwargs):
    return PluginDescriptor(name='WorldCam', description='Webcams from around the world V. ' + version, where=PluginDescriptor.WHERE_PLUGINMENU,icon='plugin.png', fnc=main)
