#pcd and lululla enjoy
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
from Plugins.Extensions.WorldCam.lib.Utils import RSList, showlist, webcamList
from Tools.Directories import fileExists
from Components.AVSwitch import AVSwitch
from enigma import *
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigText, ConfigYesNo, getConfigListEntry
from Components.config import NoSave
from Components.ConfigList import ConfigListScreen
from Screens.Standby import TryQuitMainloop
from os import path, system
import socket
from htmlentitydefs import name2codepoint as n2cp
##python2
# import httplib
# import urlparse
# import urllib2
# from urllib2 import Request, urlopen
# from urllib2 import URLError
# from urlparse import parse_qs
# from urllib import unquote_plus
## python 3
# from html.entities import name2codepoint as n2cp
# import http.client
# import urllib.parse
# import urllib.request, urllib.error, urllib.parse
# from urllib.request import Request, urlopen
# from urllib.error import URLError
# from urllib.parse import parse_qs
# from urllib.parse import unquote_plus

THISPLUG  = os.path.dirname(sys.modules[__name__].__file__)
path = THISPLUG + '/channels/'
DESKHEIGHT = getDesktop(0).size().height()
version = '3.4_r1'
config.plugins.WorldCam = ConfigSubsection()
config.plugins.WorldCam.vlcip = ConfigText('192.168.1.1', False)

PY3 = sys.version_info.major >= 3

if PY3:
## python 3
    import http.client
    import urllib.parse
    import urllib.request, urllib.error, urllib.parse
    from urllib.request import Request, urlopen
    from urllib.request import HTTPPasswordMgrWithDefaultRealm
    from urllib.request import HTTPBasicAuthHandler
    from urllib.request import build_opener
    from urllib.error import URLError
    from urllib.parse import parse_qs
    from urllib.parse import unquote_plus
else:
    import httplib
    import urlparse
    import urllib2
    from urllib2 import Request, urlopen
    from urllib2 import URLError
    from urlparse import parse_qs
    from urllib import unquote_plus
    from urllib2 import HTTPPasswordMgrWithDefaultRealm
    from urllib2 import HTTPBasicAuthHandler
    from urllib2 import build_opener
    

def checkStr(txt):
    # convert variable to type str both in Python 2 and 3
    if PY3:
        # Python 3
        if type(txt) == type(bytes()):
            txt = txt.decode('utf-8')
    else:
        #Python 2
        if type(txt) == type(unicode()):
            txt = txt.encode('utf-8')
        
    return txt
    


# SCREEN PATH SETTING
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
        Screen.__init__(self, session)
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

def getUrl(url):
    print('Here in client2 getUrl url =', url)
    try:
        req = Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        # response = urlopen(req)
        
        response = checkStr(urlopen(req))
        link = response.read()
        response.close()
        return link
    except:
        return ''

def getUrl2(url, referer):
    print('Here in getUrl2 url =', url)
    req = Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36')
    req.add_header('Referer', referer)
    # response = urlopen(req)
    
    response = checkStr(urlopen(req))    
    link = response.read()
    response.close()
    return link

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
        self.urls.append('https://www.skylinewebcams.com/en.html')
        self.names.append('earthcam.com')
        self.urls.append('https://www.earthcam.com')
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
        elif 'earthcam' in name:
            self.session.open(Webcam6)
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
        url = 'http://www.livecameras.gr/'
        content = getUrl(url)
        print('content d =', content)
        regexvideo = 'a class="item1" href="(.*?)".*?data-title="(.*?)"'
        match = re.compile(regexvideo, re.DOTALL).findall(content)
        print('match =', match)
        items = []
        for url, name in match:
            url1 = 'http:' + url
            item = name + "###" + url1
            items.append(item)
        items.sort()
        for item in items:
            name = item.split("###")[0]
            url1 = item.split("###")[1]

            self.names.append(name)
            self.urls.append(url1)
        showlist(self.names, self['list'])

    def okClicked(self):
        idx = self['list'].getSelectionIndex()
        if idx is None:
            return
        name = self.names[idx]
        url = self.urls[idx]
        self.session.open(Playstream1, name, url)


    def cancel(self):
        Screen.close(self, False)

class Webcam6(Screen):

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
        self['info'].setText('EarthCam')
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
        url = 'https://www.earthcam.com/'
        content = getUrl(url)
        print('content C =', content)
        regexvideo = '<a class="noDec" href="(.*?)".*?alt="(.*?)"'
        match = re.compile(regexvideo, re.DOTALL).findall(content)
        print('match =', match)
        items = []
        for url, name in match:
            if not "https://www.earthcam.com" in url:
                   continue
            url1 = url
            item = name + "###" + url1
            items.append(item)
        items.sort()
        for item in items:
            name = item.split("###")[0]
            url1 = item.split("###")[1]
            self.names.append(name)
            self.urls.append(url1)
        showlist(self.names, self['list'])

    def okClicked(self):
        idx = self['list'].getSelectionIndex()
        if idx is None:
            return
        url1 = self.urls[idx]
        name = self.names[idx]
        content = getUrl(url1)
        print('content C =', content)
        regexvideo = 'html5_streamingdomain"\:"(.*?)".*?html5_streampath"\:"(.*?)m3u8'
        match = re.compile(regexvideo, re.DOTALL).findall(content)
        print('match =', match)
        try:
            url = match[0][0] + match[0][1] + "m3u8"
            url = url.replace("\\", "")
            print("In Webcam7 url =", url)
            self.session.open(Playstream1, name, url)
        except:
            return

    def cancel(self):
        Screen.close(self, False)


class Webcam2(Screen):

    def __init__(self, session):
        self.session = session
        skin = SKIN_PATH + '/Webcam1.xml'
        f = open(skin, 'r')
        self.skin = f.read()
        f.close()
        Screen.__init__(self, session)
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
        contenta = getUrl('https://www.skylinewebcams.com/en.html')
        print('content A =', contenta)
        n1 = contenta.find('menu-title text-center">', 0)
        n2 = contenta.find('id="cams-category', n1)
        content = contenta[n1:n2]
        print('content B =', content)
        regexvideo = 'a href="(.*?)" class="menu-item">(.*?)</a>'
        match = re.compile(regexvideo,re.DOTALL).findall(content)
        print('match =', match)
        items = []
        for url, name in match:
            url1 = 'https://www.skylinewebcams.com' + url
            item = name + "###" + url1
            items.append(item)
        items.sort()
        for item in items:
            name = item.split("###")[0]
            url1 = item.split("###")[1]
            self.names.append(name)
            self.urls.append(url1)
        showlist(self.names, self['list'])


    def okClicked(self):
        idx = self['list'].getSelectionIndex()
        if idx is None:
            return
        name = self.names[idx]
        url = self.urls[idx]
        self.session.open(Webcam5, name, url)

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
        self['info'].setText('SkylineWebcams')
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
        print('content B =', content)
        regexvideo = 'webcam">.*?<a href="(.*?)".*?alt="(.*?)"'
        match = re.compile(regexvideo, re.DOTALL).findall(content)
        print('match =', match)
        items = []
        for url, name in match:
            url = 'https://www.skylinewebcams.com' + url
            ###
            item = name + "###" + url
            items.append(item)
        items.sort()
        for item in items:
            name = item.split("###")[0]
            url = item.split("###")[1]
            self.names.append(name)
            self.urls.append(url)
            ####
        showlist(self.names, self['list'])



    def okClicked(self):
        idx = self['list'].getSelectionIndex()
        url1 = self.urls[idx]
        name = self.names[idx]
        content = getUrl(url1)
        print('content C =', content)

        if 'source:"' in content:
            regexvideo = 'source:"(.*?)"'
            print(' aaaaaaaaaaaaaaaaaa', regexvideo)
            match = re.compile(regexvideo, re.DOTALL).findall(content)
            print('match =', match)
            try:
                url = match[0]
                self.session.open(Playstream1, name, url)
            except:
                return
        else: 
            if '"og:url" content="' in content:
                regexvideo = '"og:url" content="(.*?)"'
                print(' oooooooooooooo', regexvideo)
                match = re.compile(regexvideo, re.DOTALL).findall(content)
                url2 = match[0]
                print('url2 match 0 ', url2)
                content2 = getUrl(url2)
                regexvideo2 = ',source:"(.*?)"'
                match2 = re.compile(regexvideo2, re.DOTALL).findall(content2)
                print('match2 =', match2)
                try:
                    url = match2[0]
                    self.session.open(Playstream1, name, url)
                except:
                    return


    def cancel(self):
        self.session.nav.stopService()
        self.session.nav.playService(srefInit)
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
        self.names.append('Preview')
        self.urls.append(url)
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

    def playfile(self, serverint):
        self.serverList[serverint].play(self.session, self.url, self.name)

    def play(self):
        desc = ' '
        url = self.url
        name = self.name
        self.session.open(Playstream2, self.name1, url)


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
        # try:
            # password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
            # password_mgr.add_password(None, self.hostaddr, '', 'Admin')
            # handler = urllib2.HTTPBasicAuthHandler(password_mgr)
            # opener = urllib2.build_opener(handler)
            # f = opener.open(self.hostaddr + '/requests/status.xml?command=pl_stop')
            # f = opener.open(self.hostaddr + '/requests/status.xml?command=pl_empty')
        # except:
            # pass
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






class Playstream2(Screen, InfoBarMenu, InfoBarBase, InfoBarSeek, InfoBarNotifications, InfoBarShowHide):

    def __init__(self, session, name, url):
        Screen.__init__(self, session)
        self.skinName = 'MoviePlayer'
        title = 'Play'
        self['list'] = MenuList([])
        InfoBarMenu.__init__(self)
        InfoBarNotifications.__init__(self)
        InfoBarBase.__init__(self)
        InfoBarShowHide.__init__(self)
        self['actions'] = ActionMap(['WizardActions',
         'MoviePlayerActions',
         'EPGSelectActions',
         'MediaPlayerSeekActions',
         'ColorActions',
         'InfobarShowHideActions',
         'InfobarActions'], {'leavePlayer': self.cancel,
         'back': self.cancel}, -1)
        self.allowPiP = False
        InfoBarSeek.__init__(self, actionmap='MediaPlayerSeekActions')
        url = url.replace(':', '%3a')
        self.url = url
        self.name = name
        self.srefOld = self.session.nav.getCurrentlyPlayingServiceReference()
        self.onLayoutFinish.append(self.openTest)

    def openTest(self):
           url = self.url

           if 'youtube' in url :
               import youtube_dl
               print("Here in getVideos4 url 1=", url)
               from youtube_dl import YoutubeDL
               print("Here in getVideos4 url 2", url)
               ydl_opts = {'format': 'best'}
               ydl = YoutubeDL(ydl_opts)
               ydl.add_default_info_extractors()
              # url = "https://www.youtube.com/watch?v=CSYCEyMQWQA"
               result = ydl.extract_info(url, download=False)
               print("result =", result)
               url = result["url"]
               print("Here in Test url =", url)
           ref = '4097:0:1:0:0:0:0:0:0:0:' + url
           sref = eServiceReference(ref)
           sref.setName(self.name)
           self.session.nav.stopService()
           self.session.nav.playService(sref)

    def cancel(self):
        if os.path.exists('/tmp/hls.avi'):
            os.remove('/tmp/hls.avi')
        self.session.nav.stopService()
        self.session.nav.playService(self.srefOld)
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
