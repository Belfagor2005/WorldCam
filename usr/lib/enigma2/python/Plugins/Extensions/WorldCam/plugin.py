#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Plugin Worldcam is developed by Linuxsat-Support Team
last update 13 08 2022
edited from Lululla: updated to 20220113
"""
from __future__ import print_function
from Components.AVSwitch import AVSwitch
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.ConfigList import ConfigListScreen
from Components.FileList import FileList
from Components.Input import Input
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.Pixmap import Pixmap
from Components.ScrollLabel import ScrollLabel
from Components.SelectionList import SelectionList, SelectionEntryComponent
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.Sources.List import List
from Components.Sources.Source import Source
from Components.Sources.StaticText import StaticText
from Components.config import NoSave, ConfigYesNo, ConfigSelection, ConfigText
from Components.config import config, ConfigSubsection, getConfigListEntry
from Plugins.Plugin import PluginDescriptor
from Screens.ChoiceBox import ChoiceBox
from Screens.Console import Console
from Screens.InfoBar import MoviePlayer, InfoBar
from Screens.InfoBarGenerics import *
from Screens.InfoBarGenerics import InfoBarMenu, InfoBarSeek, InfoBarAudioSelection, InfoBarMoviePlayerSummarySupport, \
    InfoBarSubtitleSupport, InfoBarSummarySupport, InfoBarServiceErrorPopupSupport, InfoBarNotifications
from Screens.InputBox import InputBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Screens.VirtualKeyBoard import VirtualKeyBoard
from ServiceReference import ServiceReference
from Tools.Directories import SCOPE_PLUGINS, resolveFilename
from Tools.Downloader import downloadWithProgress
from Tools.LoadPixmap import LoadPixmap
from enigma import *
from enigma import RT_HALIGN_CENTER, RT_VALIGN_CENTER
from enigma import RT_HALIGN_LEFT, RT_HALIGN_RIGHT
from enigma import eListbox, eTimer
from enigma import eListboxPythonMultiContent, eConsoleAppContainer
from enigma import eServiceCenter
from enigma import eServiceReference
from enigma import eSize, ePicLoad
from enigma import iServiceInformation
from enigma import loadPNG, gFont
from enigma import quitMainloop
from enigma import iPlayableService
from sys import version_info
from twisted.web.client import getPage, downloadPage
from xml.sax.saxutils import escape, unescape
from six.moves.html_parser import HTMLParser
import Components.PluginComponent
import os, re, sys
import six
import socket
import ssl
from . import Utils

version = '4.2_r5' #edit lululla 07/02/2022
THISPLUG = '/usr/lib/enigma2/python/Plugins/Extensions/WorldCam'
ico_path1 = '/usr/lib/enigma2/python/Plugins/Extensions/WorldCam/pics/plugin.png'
ico_path2 = '/usr/lib/enigma2/python/Plugins/Extensions/WorldCam/pics/plugins.png'
iconpic = 'plugin.png'
SKIN_PATH = THISPLUG + '/skin/hd'
if Utils.isFHD():
    SKIN_PATH = THISPLUG + '/skin/fhd'

pythonFull = float(str(sys.version_info.major) + "." + str(sys.version_info.minor))
pythonVer = sys.version_info.major
PY3 = False

if sys.version_info >= (2, 7, 9):
    try:
        import ssl
        sslContext = ssl._create_unverified_context()
    except:
        sslContext = None

leng1 = os.popen("cat /etc/enigma2/settings | grep config.osd.language|sed '/^config.osd.language=/!d'").read().replace('config.osd.language=', '').replace('_', '-').replace('\n', '')
language = leng1[:-3]
print('lengg: ', language)

try:
    import httplib
    import urlparse
    import urllib2
    from urllib2 import Request, urlopen
    from urllib2 import URLError
    from urlparse import parse_qs
    from urllib2 import HTTPPasswordMgrWithDefaultRealm
    from urllib2 import HTTPBasicAuthHandler
    from urllib2 import build_opener
    # _str = str
    # str = unicode
    # range = xrange
    # unicode = unicode
    # basestring = basestring
except:
# if PY3:
    # import http.client
    import http.client as httplib
    import urllib.parse
    import urllib.request, urllib.error, urllib.parse
    from urllib.request import Request, urlopen
    from urllib.request import HTTPPasswordMgrWithDefaultRealm
    from urllib.request import HTTPBasicAuthHandler
    from urllib.request import build_opener
    from urllib.error import URLError
    from urllib.parse import parse_qs
    PY3 = True; unicode = str; unichr = chr; long = int
    unichr = chr; long = int

class webcamList(MenuList):
    def __init__(self, list):
        MenuList.__init__(self, list, True, eListboxPythonMultiContent)
        if Utils.isFHD():
            self.l.setItemHeight(50)
            textfont=int(34)
            self.l.setFont(0, gFont('Regular', textfont))
        else:
            self.l.setItemHeight(50)
            textfont=int(22)
            self.l.setFont(0, gFont('Regular', textfont))

def wcListEntry(name):
    pngx = ico_path1
    res = [name]
    if Utils.isFHD:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 12), size=(34, 25), png=loadPNG(pngx)))
        res.append(MultiContentEntryText(pos=(60, 0), size=(1900, 50), font=0, text=name, color = 0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    else:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 12), size=(34, 25), png=loadPNG(pngx)))
        res.append(MultiContentEntryText(pos=(60, 0), size=(1000, 50), font=0, text=name, color = 0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    return res

def showlist(data, list):
    icount = 0
    plist = []
    for line in data:
        name = data[icount]
        plist.append(wcListEntry(name))
        icount = icount+1
        list.setList(plist)

def paypal():
    conthelp = "If you like what I do you\n"
    conthelp += " can contribute with a coffee\n\n"
    conthelp += "scan the qr code and donate € 1.00"
    return conthelp


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
        self['key_red'] = Button(_('Exit'))
        self['key_green'] = Button(_('Select'))
        self['info'] = Label('HOME VIEW')
        self["paypal"] = Label()
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions', 'TimerEditActions'], {'red': self.close,
         'green': self.okClicked,
         'cancel': self.cancel,
         'ok': self.okClicked}, -2)
        self.onLayoutFinish.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        self["paypal"].setText(paypal)

    def openTest(self):
        self.names = []
        self.urls = []
        self.names.append('User Lists')
        self.urls.append('http://worldcam.eu/')  # THISPLUG + '/Playlists'
        self.names.append('skylinewebcams')
        self.urls.append('https://www.skylinewebcams.com/')
        self.names.append('skylinetop')
        self.urls.append('https://www.skylinewebcams.com/')  # {0}/top-live-cams.html'.format(language))
        showlist(self.names, self['list'])

    def okClicked(self):
        i = len(self.names)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self['list'].getSelectionIndex()
        name = self.names[idx]
        url = self.urls[idx]
        if 'User' in name:
            self.session.open(Webcam2)
        elif 'skylinewebcams' in name:
            self.session.open(Webcam4)
        elif 'skylinetop' in name:
            self.session.open(Webcam7)

    def cancel(self):
        Utils.deletetmp()
        self.close()

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
        self['info'] = Label('UserList')
        self["paypal"] = Label()
        self['key_red'] = Button(_('Exit'))
        self['key_green'] = Button(_('Select'))
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions', 'TimerEditActions'], {'red': self.close,
         'green': self.okClicked,
         'cancel': self.cancel,
         'ok': self.okClicked}, -2)
        self.onLayoutFinish.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        self["paypal"].setText(paypal)

    def openTest(self):
        uLists = THISPLUG + '/Playlists'
        self.names = []
        for root, dirs, files in os.walk(uLists):
            for name in files:
                self.names.append(name)
        showlist(self.names, self['list'])

    def okClicked(self):
        i = len(self.names)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self['list'].getSelectionIndex()
        name = self.names[idx]
        self.session.open(Webcam3, name)

    def cancel(self):
        self.close()

class Webcam3(Screen):
    def __init__(self, session, name):
        Screen.__init__(self, session)
        self.session = session
        skin = SKIN_PATH + '/Webcam1.xml'
        f = open(skin, 'r')
        self.skin = f.read()
        f.close()
        self.list = []
        self.name = name
        self['list'] = webcamList([])
        self['info'] = Label('UserList')
        self["paypal"] = Label()
        self['key_red'] = Button(_('Exit'))
        self['key_green'] = Button(_('Select'))
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions', 'TimerEditActions'], {'red': self.close,
         'green': self.okClicked,
         'cancel': self.cancel,
         'ok': self.okClicked}, -2)
        self.onLayoutFinish.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        self["paypal"].setText(paypal)

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
            name = Utils.checkStr(name)
            url = Utils.checkStr(url)
            self.names.append(name)
            self.urls.append(url)
        showlist(self.names, self['list'])

    def okClicked(self):
        i = len(self.names)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self['list'].getSelectionIndex()
        name = self.names[idx]
        url = self.urls[idx]
        self.session.open(Playstream1, name, url)

    def cancel(self):
        self.close()

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
        self['info'] = Label('Skyline Webcams')
        self["paypal"] = Label()
        self['key_red'] = Button(_('Exit'))
        self['key_green'] = Button(_('Select'))
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions', 'TimerEditActions'], {'red': self.close,
         'green': self.okClicked,
         'cancel': self.cancel,
         'ok': self.okClicked}, -2)
        self.onLayoutFinish.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        self["paypal"].setText(paypal)

    def openTest(self):
        self.names = []
        self.urls = []
        BASEURL = 'https://www.skylinewebcams.com/'
        from . import client, dom_parser as dom
        headers = {'User-Agent': client.agent(),
           'Referer': BASEURL}
        content = six.ensure_str(client.request(BASEURL, headers=headers))

        regexvideo = 'class="ln_css ln-(.+?)" alt="(.+?)"'
        match = re.compile(regexvideo, re.DOTALL).findall(content)
        print('Webcam4 match = ', match)
        items = []
        for url, name in match:
            url1 = '{}/{}.html'.format('https://www.skylinewebcams.com', url)
            url1 = Utils.checkStr(url1)
            name = Utils.checkStr(name)
            item = name + "###" + url1
            print('Webcam4 Items sort: ', item)
            items.append(item)
        items.sort()
        for item in items:
            name = item.split('###')[0]
            url1 = item.split('###')[1]
            self.names.append(name)
            self.urls.append(url1)
        showlist(self.names, self['list'])

    def okClicked(self):
        i = len(self.names)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self['list'].getSelectionIndex()
        name = self.names[idx]
        url = self.urls[idx]
        self.session.open(Webcam5, name, url)

    def cancel(self):
        self.close()

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
        self['info'] = Label(name)
        self["paypal"] = Label()
        self['key_red'] = Button(_('Exit'))
        self['key_green'] = Button(_('Select'))
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions', 'TimerEditActions'], {'red': self.close,
         'green': self.okClicked,
         'cancel': self.cancel,
         'ok': self.okClicked}, -2)
        self.name = name
        self.url = url
        self.onLayoutFinish.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        self["paypal"].setText(paypal)

    def openTest(self):
        self.names = []
        self.urls = []
        BASEURL = 'https://www.skylinewebcams.com/'
        from . import client
        headers = {'User-Agent': client.agent(),
           'Referer': BASEURL}
        content = six.ensure_str(client.request(self.url, headers=headers))
        start = 0
        n1 = content.find('div class="dropdown-menu mega-dropdown-menu', start)
        n2 = content.find('div class="collapse navbar-collapse', n1)
        content2 = content[n1:n2]
        ctry = self.url.replace('https://www.skylinewebcams.com/', '')
        ctry = ctry.replace('.html', '')
        regexvideo = '<a href="/' + ctry + '/webcam(.+?)">(.+?)</a>'
        match = re.compile(regexvideo, re.DOTALL).findall(content2)
        items = []
        for url, name in match:
            url1 = '{}/{}/webcam{}'.format('https://www.skylinewebcams.com', ctry, url)
            item = name + "###" + url1
            print('Items sort 2: ', item)
            items.append(item)
        items.sort()
        for item in items:
            name = item.split('###')[0]
            url1 = item.split('###')[1]
            self.names.append(name)
            self.urls.append(url1)
            print("Webcam5 self.names =", self.names)
            print("Webcam5 self.urls =", self.urls)
        showlist(self.names, self['list'])

    def okClicked(self):
        i = len(self.names)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self['list'].getSelectionIndex()
        name = self.names[idx]
        url = self.urls[idx]
        self.session.open(Webcam5a, name, url)

    def cancel(self):
        self.close()

class Webcam5a(Screen):
    def __init__(self, session, name, url):
        Screen.__init__(self, session)
        self.session = session
        skin = SKIN_PATH + '/Webcam1.xml'
        f = open(skin, 'r')
        self.skin = f.read()
        f.close()
        self.list = []
        self['list'] = webcamList([])
        self['info'] = Label(name)
        self["paypal"] = Label()
        self['key_red'] = Button(_('Exit'))
        self['key_green'] = Button(_('Select'))
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions', 'TimerEditActions'], {'red': self.close,
         'green': self.okClicked,
         'cancel': self.cancel,
         'ok': self.okClicked}, -2)
        self.name = name
        self.url = url
        self.onLayoutFinish.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)

    def paypal2(self):
        conthelp = "If you like what I do you\n"
        conthelp += " can contribute with a coffee\n\n"
        conthelp += "scan the qr code and donate € 1.00"
        return conthelp

    def layoutFinished(self):
        self["paypal"].setText(paypal)

    def openTest(self):
        self.names = []
        self.urls = []
        BASEURL = 'https://www.skylinewebcams.com/'
        from . import client
        headers = {'User-Agent': client.agent(),
           'Referer': BASEURL}
        content = six.ensure_str(client.request(self.url, headers=headers))
        n1 = content.find('col-xs-12"><h1>', 0)
        n2 = content.find('</div>', n1)
        content2 = content[n1:n2]
        ctry = self.url.replace('https://www.skylinewebcams.com/', '')
        ctry = ctry.replace('.html', '')
        print('------->>> ctry: ', ctry)
        regexvideo = '<a href="/' + ctry + '/(.+?)".*?tag">(.+?)</a>'
        match = re.compile(regexvideo, re.DOTALL).findall(content2)
        items = []
        for url, name in match:
            url1 = '{}/{}/{}'.format('https://www.skylinewebcams.com', ctry, url)
            url1 = Utils.checkStr(url1)
            name = Utils.checkStr(name)
            item = name + "###" + url1
            print('Items sort 2: ', item)
            items.append(item)
        items.sort()
        for item in items:
            name = item.split('###')[0]
            url1 = item.split('###')[1]
            self.names.append(name)
            self.urls.append(url1)
            print("Webcam5 self.names =", self.names)
            print("Webcam5 self.urls =", self.urls)
        showlist(self.names, self['list'])

    def okClicked(self):
        i = len(self.names)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self['list'].getSelectionIndex()
        name = self.names[idx]
        url = self.urls[idx]
        self.session.open(Webcam6, name, url)

    def cancel(self):
        self.close()

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
        self['info'] = Label(name)
        self["paypal"] = Label()
        self['key_red'] = Button(_('Exit'))
        self['key_green'] = Button(_('Select'))
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions', 'TimerEditActions'], {'red': self.close,
         'green': self.okClicked,
         'cancel': self.cancel,
         'ok': self.okClicked}, -2)
        self.onLayoutFinish.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        self["paypal"].setText(paypal)

    def openTest(self):
        self.names = []
        self.urls = []
        BASEURL = 'https://www.skylinewebcams.com/'
        from . import client
        headers = {'User-Agent': client.agent(),
           'Referer': BASEURL}
        content = six.ensure_str(client.request(self.url, headers=headers))
        stext = self.url.replace('https://www.skylinewebcams.com/', '')
        stext = stext.replace('.html', '')
        stext = stext + '/'
        regexvideo = '><a href="' + stext + '(.+?)".*?alt="(.+?)"'
        match = re.compile(regexvideo, re.DOTALL).findall(content)
        items = []
        for url, name in match:
            url1 = '{}/{}{}'.format('https://www.skylinewebcams.com', stext, url)
            url1 = Utils.checkStr(url1)
            name = Utils.checkStr(name)
            item = name + "###" + url1
            items.append(item)
        items.sort()
        for item in items:
            name = item.split('###')[0]
            url1 = item.split('###')[1]
            self.names.append(name)
            self.urls.append(url1)
        showlist(self.names, self['list'])

    def okClicked(self):
        i = len(self.names)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self['list'].getSelectionIndex()
        url1 = self.urls[idx]
        name = self.names[idx]
        self.getVid(name, url1)

    def getVid(self, name, url):
        try:
            content = Utils.ReadUrl2(url)
            if PY3:
                content = six.ensure_str(content)
            print('content ============================ ', content)
            regexvideo = "source:'livee.m3u8(.+?)'"
            match = re.compile(regexvideo, re.DOTALL).findall(content)
            print('id: ', match)
            id = match[0]
            id = id.replace('?a=','')
            if id or id != '':
                url = "https://hd-auth.skylinewebcams.com/live.m3u8?a=" + id
                print( "Here in plugin.py getVid play with streamlink url =", url)
                url = url.replace(":", "%3a")
                url = url.replace("\\", "/")
                ref = url
                desc = ' '
                self.session.open(Playstream2, name, ref, desc)
            else:
                return
        except Exception as e:
           print(str(e))

    def cancel(self):
        self.close()

#topcam
class Webcam7(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = SKIN_PATH + '/Webcam1.xml'
        f = open(skin, 'r')
        self.skin = f.read()
        f.close()
        self.list = []
        self['list'] = webcamList([])
        self['info'] = Label('Skyline Top')
        self["paypal"] = Label()
        self['key_red'] = Button(_('Exit'))
        self['key_green'] = Button(_('Select'))
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions', 'TimerEditActions'], {'red': self.close,
         'green': self.okClicked,
         'cancel': self.cancel,
         'ok': self.okClicked}, -2)
        self.onLayoutFinish.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        self["paypal"].setText(paypal)

    def openTest(self):
        self.names = []
        self.urls = []
        BASEURL = 'https://www.skylinewebcams.com/'
        from . import client
        headers = {'User-Agent': client.agent(),
           'Referer': BASEURL}
        content = six.ensure_str(client.request(BASEURL, headers=headers))
        print('content: ',content)
        n1 = content.find('dropdown-menu mega-dropdown-menu cat', 0)
        n2 = content.find('</div></div>', n1)
        content2 = content[n1:n2]
        regexvideo = 'href="(.+?)".*?tcam">(.+?)</p>'
        match = re.compile(regexvideo, re.DOTALL).findall(content2)
        items = []
        for url, name, in match:
            url1 = 'https://www.skylinewebcams.com' + url
            url1 = Utils.checkStr(url1)
            name = Utils.checkStr(name)
            self.names.append(name)
            self.urls.append(url1)
        showlist(self.names, self['list'])

    def okClicked(self):
        i = len(self.names)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self['list'].getSelectionIndex()
        name = self.names[idx]
        url = self.urls[idx]
        self.session.open(Webcam8, name, url) #Webcam5

    def cancel(self):
        self.close()

class Webcam8(Screen):
    def __init__(self, session, name, url):
        Screen.__init__(self, session)
        self.session = session
        skin = SKIN_PATH + '/Webcam1.xml'
        f = open(skin, 'r')
        self.skin = f.read()
        f.close()
        self.list = []
        self['list'] = webcamList([])
        self['info'] = Label(name)
        self["paypal"] = Label()
        self['key_red'] = Button(_('Exit'))
        self['key_green'] = Button(_('Select'))
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions', 'TimerEditActions'], {'red': self.close,
         'green': self.okClicked,
         'cancel': self.cancel,
         'ok': self.okClicked}, -2)
        self.name = name
        self.url = url
        self.onLayoutFinish.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        self["paypal"].setText(paypal)

    def openTest(self):
        self.names = []
        self.urls = []
        items = []
        BASEURL = 'https://www.skylinewebcams.com/{0}/webcam.html'
        from . import client, dom_parser as dom   #,control
        headers = {'User-Agent': client.agent(),
           'Referer': BASEURL}
        content = six.ensure_str(client.request(self.url, headers=headers))
        data = client.parseDOM(content, 'div', attrs={'class': 'container'})[0]
        data = dom.parse_dom(data, 'a', req='href')
        data = [i for i in data if 'subt' in i.content]
        for item in data:
            link = item.attrs['href']
            if link == '#':
                continue
            link = Utils.decodeHtml(link)
            name = client.parseDOM(item.content, 'img', ret='alt')[0]
            name = Utils.decodeHtml(name)
            if six.PY2:
                link = link.encode('utf-8')
                name = name.encode('utf-8')
            base_url = 'https://www.skylinewebcams.com'
            url = '{}/{}'.format(base_url, link)
            url = Utils.checkStr(url)
            name = Utils.checkStr(name)
            item = name + "###" + url
            print('Items sort 2: ', item)
            items.append(item)

        items.sort()
        for item in items:
            name = item.split('###')[0]
            url = item.split('###')[1]
            self.names.append(name)
            self.urls.append(url)
            print("Webcam5 self.names =", self.names)
            print("Webcam5 self.urls =", self.urls)
        showlist(self.names, self['list'])

    def okClicked(self):
        i = len(self.names)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self['list'].getSelectionIndex()
        url1 = self.urls[idx]
        name = self.names[idx]
        self.getVid(name, url1)

    def getVid(self, name, url):
        try:
            content = Utils.ReadUrl2(url)
            if PY3:
                content = six.ensure_str(content)
            print('content ============================ ', content)
            regexvideo = "source:'livee.m3u8(.+?)'"
            match = re.compile(regexvideo, re.DOTALL).findall(content)
            print('id: ', match)
            id = match[0]
            id = id.replace('?a=','')
            if id or id != '':
                url = "https://hd-auth.skylinewebcams.com/live.m3u8?a=" + id
                print( "Here in plugin.py getVid play with streamlink url =", url)
                url = url.replace(":", "%3a")
                url = url.replace("\\", "/")
                ref = url
                desc = ' '
                self.session.open(Playstream2, name, ref, desc)
            else:
                return
        except Exception as e:
           print(str(e))

    def cancel(self):
        self.close()

class Webcam9(Screen):
    def __init__(self, session, name, url):
        Screen.__init__(self, session)
        self.session = session
        self.name = name
        self.url = url
        skin = SKIN_PATH + '/Webcam1.xml'
        f = open(skin, 'r')
        self.skin = f.read()
        f.close()
        self.list = []
        self['list'] = webcamList([])
        self['info'] = Label(name)
        self["paypal"] = Label()
        self['key_red'] = Button(_('Exit'))
        self['key_green'] = Button(_('Select'))
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions', 'TimerEditActions'], {'red': self.close,
         'green': self.okClicked,
         'cancel': self.cancel,
         'ok': self.okClicked}, -2)
        self.onLayoutFinish.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        self["paypal"].setText(paypal)

    def openTest(self, name, url):
        try:
            content = Utils.ReadUrl2(url)
            if PY3:
                content = six.ensure_str(content)
            print('content ============================ ', content)
            regexvideo = "source:'livee.m3u8(.+?)'"
            match = re.compile(regexvideo, re.DOTALL).findall(content)
            print('id: ', match)
            id = match[0]
            id = id.replace('?a=','')
            if id or id != '':
                url = "https://hd-auth.skylinewebcams.com/live.m3u8?a=" + id
                print( "Here in plugin.py getVid play with streamlink url =", url)
                url = url.replace(":", "%3a")
                url = url.replace("\\", "/")
                ref = url
                desc = ' '
                self.session.open(Playstream2, name, ref, desc)
            else:
                return
        except Exception as e:
           print(str(e))

    def cancel(self):
        self.close()

class Playstream1(Screen):
    def __init__(self, session, name, url):
        Screen.__init__(self, session)
        self.session = session
        skin = SKIN_PATH + '/Webcam1.xml'
        f = open(skin, 'r')
        self.skin = f.read()
        f.close()
        self.list = []
        self.name1 = name
        self.url = url
        print('In Playstream1 self.url =', url)
        global srefInit
        self.initialservice = self.session.nav.getCurrentlyPlayingServiceReference()
        srefInit = self.initialservice
        self['list'] = webcamList([])
        self['info'] = Label('Select Player')
        self["paypal"] = Label()
        self['key_red'] = Button(_('Exit'))
        self['key_green'] = Button(_('Select'))
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions', 'TimerEditActions'], {'red': self.cancel,
         'green': self.okClicked,
         'back' : self.cancel,
         'cancel': self.cancel,
         'ok': self.okClicked}, -2)
        self.onLayoutFinish.append(self.layoutFinished)
        self.onLayoutFinish.append(self.openTest)

    def layoutFinished(self):
        self["paypal"].setText(paypal)

    def openTest(self):
        url = self.url
        self.names = []
        self.urls = []
        self.names.append('Play Direct')
        self.urls.append(url)
        self.names.append('Play Hls')
        self.urls.append(url)
        self.names.append('Play Ts')
        self.urls.append(url)
        showlist(self.names, self['list'])

    def okClicked(self):
        i = len(self.names)
        print('iiiiii= ',i)
        if i < 1:
            return
        idx = self['list'].getSelectionIndex()
        self.name = self.names[idx]
        self.url = self.urls[idx]
        if idx == 0:
            print('In playVideo url D=', self.url)
            self.play()
        elif idx == 1:
            print('In playVideo url B=', self.url)
            try:
                os.remove('/tmp/hls.avi')
            except:
                pass
            header = ''
            cmd = 'python "/usr/lib/enigma2/python/Plugins/Extensions/WorldCam/lib/hlsclient.py" "' + self.url + '" "1" "' + header + '" + &'
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
            cmd = 'python "/usr/lib/enigma2/python/Plugins/Extensions/WorldCam/lib/tsclient.py" "' + url + '" "1" + &'
            print('ts cmd = ', cmd)
            os.system(cmd)
            os.system('sleep 3')
            self.url = '/tmp/hls.avi'
            self.name = self.names[idx]
            self.play()

        elif idx == 3:
            print('In playVideo url D=', self.url)
            self.play2()
        else:
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
        self.session.nav.stopService()
        self.session.nav.playService(srefInit)
        self.close()

class TvInfoBarShowHide():
    """ InfoBar show/hide control, accepts toggleShow and hide actions, might start
    fancy animations. """
    STATE_HIDDEN = 0
    STATE_HIDING = 1
    STATE_SHOWING = 2
    STATE_SHOWN = 3
    skipToggleShow = False

    def __init__(self):
        self["ShowHideActions"] = ActionMap(["InfobarShowHideActions"], {"toggleShow": self.OkPressed,
         "hide": self.hide}, 0)
        self.__event_tracker = ServiceEventTracker(screen=self, eventmap={iPlayableService.evStart: self.serviceStarted})
        self.__state = self.STATE_SHOWN
        self.__locked = 0
        self.hideTimer = eTimer()
        try:
            self.hideTimer_conn = self.hideTimer.timeout.connect(self.doTimerHide)
        except:
            self.hideTimer.callback.append(self.doTimerHide)
        self.hideTimer.start(5000, True)
        self.onShow.append(self.__onShow)
        self.onHide.append(self.__onHide)

    def OkPressed(self):
        self.toggleShow()

    def toggleShow(self):
        if self.skipToggleShow:
            self.skipToggleShow = False
            return
        if self.__state == self.STATE_HIDDEN:
            self.show()
            self.hideTimer.stop()
        else:
            self.hide()
            self.startHideTimer()

    def serviceStarted(self):
        if self.execing:
            if config.usage.show_infobar_on_zap.value:
                self.doShow()

    def __onShow(self):
        self.__state = self.STATE_SHOWN
        self.startHideTimer()

    def startHideTimer(self):
        if self.__state == self.STATE_SHOWN and not self.__locked:
            idx = config.usage.infobar_timeout.index
            if idx:
                self.hideTimer.start(idx * 1500, True)

    def __onHide(self):
        self.__state = self.STATE_HIDDEN

    def doShow(self):
        self.hideTimer.stop()
        self.show()
        self.startHideTimer()

    def doTimerHide(self):
        self.hideTimer.stop()
        if self.__state == self.STATE_SHOWN:
            self.hide()

    def lockShow(self):
        try:
            self.__locked += 1
        except:
            self.__locked = 0
        if self.execing:
            self.show()
            self.hideTimer.stop()
            self.skipToggleShow = False

    def unlockShow(self):
        try:
            self.__locked -= 1
        except:
            self.__locked = 0
        if self.__locked < 0:
            self.__locked = 0
        if self.execing:
            self.startHideTimer()

    def debug(obj, text = ""):
        print(text + " %s\n" % obj)

class Playstream2(
    InfoBarBase,
    InfoBarMenu,
    InfoBarSeek,
    InfoBarAudioSelection,
    InfoBarSubtitleSupport,
    InfoBarNotifications,
    TvInfoBarShowHide,
    Screen
):
    STATE_IDLE = 0
    STATE_PLAYING = 1
    STATE_PAUSED = 2
    ENABLE_RESUME_SUPPORT = True
    ALLOW_SUSPEND = True
    screen_timeout = 5000
    def __init__(self, session, name, url, desc):
        global SREF, streaml
        Screen.__init__(self, session)
        self.session = session
        self.skinName = 'MoviePlayer'
        title = name
        streaml = False
        for x in InfoBarBase, \
                InfoBarMenu, \
                InfoBarSeek, \
                InfoBarAudioSelection, \
                InfoBarSubtitleSupport, \
                InfoBarNotifications, \
                TvInfoBarShowHide:
            x.__init__(self)
        try:
            self.init_aspect = int(self.getAspect())
        except:
            self.init_aspect = 0
        self.new_aspect = self.init_aspect
        SREF = self.session.nav.getCurrentlyPlayingServiceReference()
        self.allowPiP = False
        self.service = None
        service = None
        self.url = url
        self.desc = desc
        self.name = Utils.decodeHtml(name)
        self.state = self.STATE_PLAYING
        self['actions'] = ActionMap(['MoviePlayerActions',
         'MovieSelectionActions',
         'MediaPlayerActions',
         'EPGSelectActions',
         'MediaPlayerSeekActions',
         'SetupActions',
         'ColorActions',
         'InfobarShowHideActions',
         'InfobarActions',
         'InfobarSeekActions'], {'stop': self.cancel,
         'epg': self.showIMDB,
         'info': self.showIMDB,
         'playpauseService': self.playpauseService,
         'yellow': self.subtitles,
         'tv': self.cicleStreamType,
         'stop': self.cancel,
         'cancel': self.cancel,
         'back': self.cancel,
         'down': self.av}, -1)
        if '8088' in str(self.url):
            self.onFirstExecBegin.append(self.slinkPlay)
        else:
            self.onFirstExecBegin.append(self.cicleStreamType)
        self.onClose.append(self.cancel)

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
            if servicename != None:
                sTitle = servicename
            else:
                sTitle = ''
            if serviceurl != None:
                sServiceref = serviceurl
            else:
                sServiceref = ''
            currPlay = self.session.nav.getCurrentService()
            sTagCodec = currPlay.info().getInfoString(iServiceInformation.sTagCodec)
            sTagVideoCodec = currPlay.info().getInfoString(iServiceInformation.sTagVideoCodec)
            sTagAudioCodec = currPlay.info().getInfoString(iServiceInformation.sTagAudioCodec)
            message = 'stitle:' + str(sTitle) + '\n' + 'sServiceref:' + str(sServiceref) + '\n' + 'sTagCodec:' + str(sTagCodec) + '\n' + 'sTagVideoCodec:' + str(sTagVideoCodec) + '\n' + 'sTagAudioCodec :' + str(sTagAudioCodec)
            self.session.open(MessageBox, message, MessageBox.TYPE_INFO)
        except:
            pass
        return

    def showIMDB(self):
        TMDB = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('TMDB'))
        IMDb = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('IMDb'))
        if os.path.exists(TMDB):
            from Plugins.Extensions.TMBD.plugin import TMBD
            text_clear = self.name
            text = Utils.charRemove(text_clear)
            self.session.open(TMBD, text, False)
        elif os.path.exists(IMDb):
            from Plugins.Extensions.IMDb.plugin import IMDB
            text_clear = self.name
            text = Utils.charRemove(text_clear)
            self.session.open(IMDB, text)
        else:
            text_clear = self.name
            self.session.open(MessageBox, text_clear, MessageBox.TYPE_INFO)

    def slinkPlay(self, url):
        name = self.name
        ref = "{0}:{1}".format(url.replace(":", "%3a"), name.replace(":", "%3a"))
        print('final reference:   ', ref)
        sref = eServiceReference(ref)
        sref.setName(name)
        self.session.nav.stopService()
        self.session.nav.playService(sref)

    def openPlay(self, servicetype, url):
        name = self.name
        ref = "{0}:0:0:0:0:0:0:0:0:0:{1}:{2}".format(servicetype, url.replace(":", "%3a"), name.replace(":", "%3a"))
        print('reference:   ', ref)
        if streaml == True:
            url = 'http://127.0.0.1:8088/' + str(url)
            ref = "{0}:0:1:0:0:0:0:0:0:0:{1}:{2}".format(servicetype, url.replace(":", "%3a"), name.replace(":", "%3a"))
            print('streaml reference:   ', ref)
        print('final reference:   ', ref)
        sref = eServiceReference(ref)
        sref.setName(name)
        self.session.nav.stopService()
        self.session.nav.playService(sref)

    def cicleStreamType(self):
        global streaml
        streaml = False
        from itertools import cycle, islice
        self.servicetype = '4097'
        print('servicetype1: ', self.servicetype)
        url = str(self.url)
        if str(os.path.splitext(self.url)[-1]) == ".m3u8":
            # if self.servicetype == "1":
                self.servicetype = "4097"
        currentindex = 0
        streamtypelist = ["4097"]
        # if "youtube" in str(self.url):
            # self.mbox = self.session.open(MessageBox, _('For Stream Youtube coming soon!'), MessageBox.TYPE_INFO, timeout=5)
            # return
        if Utils.isStreamlinkAvailable():
            streamtypelist.append("5002") #ref = '5002:0:1:0:0:0:0:0:0:0:http%3a//127.0.0.1%3a8088/' + url
            streaml = True
        if os.path.exists("/usr/bin/gstplayer"):
            streamtypelist.append("5001")
        if os.path.exists("/usr/bin/exteplayer3"):
            streamtypelist.append("5002")
        if os.path.exists("/usr/bin/apt-get"):
            streamtypelist.append("8193")
        for index, item in enumerate(streamtypelist, start=0):
            if str(item) == str(self.servicetype):
                currentindex = index
                break
        nextStreamType = islice(cycle(streamtypelist), currentindex + 1, None)
        self.servicetype = str(next(nextStreamType))
        print('servicetype2: ', self.servicetype)
        self.openPlay(self.servicetype, url)

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

    def up(self):
        pass

    def down(self):
        self.up()

    def doEofInternal(self, playing):
        self.close()

    def __evEOF(self):
        self.end = True

    def openTest(self):
        name = self.name
        name = name.replace(':', '-').replace('&', '-').replace(' ', '-')
        name = name.replace('/', '-').replace(',', '-')
        url = self.url
        if url != None:
            if '5002' in url:
                # ref = self.url
                ref = "5002:0:0:0:0:0:0:0:0:0:{0}:{1}".format(url.replace(":", "%3a"), name.replace(":", "%3a"))
                sref = eServiceReference(ref)
                sref.setName(self.name)
                self.session.nav.stopService()
                self.session.nav.playService(sref)
            else:
                ref = "4097:0:0:0:0:0:0:0:0:0:{0}:{1}".format(url.replace(":", "%3a"), name.replace(":", "%3a"))
                sref = eServiceReference(ref)
                sref.setName(self.name)
                self.session.nav.stopService()
                self.session.nav.playService(sref)
        return

    def subtitles(self):
        self.session.open(MessageBox, _('Please install script.module.SubSupport.'), MessageBox.TYPE_ERROR, timeout=10)

    def showAfterSeek(self):
        if isinstance(self, TvInfoBarShowHide):
            self.doShow()

    def cancel(self):
        if os.path.exists('/tmp/hls.avi'):
            os.remove('/tmp/hls.avi')
        self.session.nav.stopService()
        self.session.nav.playService(SREF)
        # if self.pcip != 'None':
            # url2 = 'http://' + self.pcip + ':8080/requests/status.xml?command=pl_stop'
            # resp = urlopen(url2)
        if not self.new_aspect == self.init_aspect:
            try:
                self.setAspect(self.init_aspect)
            except:
                pass
        streaml = False
        self.close()

    def leavePlayer(self):
        self.close()

def main(session, **kwargs):
    global _session
    _session = session
    if Utils.zCheckInternet(1):
        try:
            from . import Update
            Update.upd_done()
            # session.open(Webcam1)
        except:
            import traceback
            traceback.print_exc()
            pass
        session.open(Webcam1)
    else:
        from Screens.MessageBox import MessageBox
        from Tools.Notifications import AddPopup
        AddPopup(_("Sorry but No Internet :("),MessageBox.TYPE_INFO, 10, 'Sorry')


def Plugins(**kwargs):
    return PluginDescriptor(name='WorldCam', description='Webcams from around the world V. ' + version, where=PluginDescriptor.WHERE_PLUGINMENU,icon='plugin.png', fnc=main)

