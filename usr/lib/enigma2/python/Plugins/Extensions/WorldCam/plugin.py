#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Plugin Worldcam is developed by Linuxsat-Support Team
last update 07 04 2023
edited from Lululla: updated to 20220113
"""
# from __future__ import unicode_literals
from __future__ import print_function
from . import Utils
from . import html_conv
from Components.AVSwitch import AVSwitch
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText
from Components.MultiContent import MultiContentEntryPixmapAlphaTest
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.config import config
from Plugins.Plugin import PluginDescriptor
from Screens.InfoBarGenerics import InfoBarMenu, InfoBarSeek
from Screens.InfoBarGenerics import InfoBarAudioSelection
from Screens.InfoBarGenerics import InfoBarSubtitleSupport
from Screens.InfoBarGenerics import InfoBarNotifications
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from enigma import RT_VALIGN_CENTER
from enigma import RT_HALIGN_LEFT
from enigma import eTimer
from enigma import eListboxPythonMultiContent
from enigma import eServiceReference
from enigma import loadPNG, gFont
from enigma import iPlayableService
import os
import re
import sys
import six
import ssl
global SKIN_PATH

version = '4.3'  # edit lululla 07/11/2022
setup_title = ('WORLDCAM v.' + version)
THISPLUG = '/usr/lib/enigma2/python/Plugins/Extensions/WorldCam'
ico_path1 = os.path.join(THISPLUG, 'pics/webcam.png')
iconpic = 'plugin.png'
refer = 'https://www.skylinewebcams.com/'
_firstStartwrd = True
SKIN_PATH = os.path.join(THISPLUG, 'skin/hd/')
if Utils.isFHD():
    SKIN_PATH = os.path.join(THISPLUG, 'skin/fhd/')
else:
    SKIN_PATH = os.path.join(THISPLUG, 'skin/hd/')

PY3 = False
PY3 = sys.version_info.major >= 3

if sys.version_info >= (2, 7, 9):
    try:
        import ssl
        sslContext = ssl._create_unverified_context()
    except:
        sslContext = None

leng = os.popen("cat /etc/enigma2/settings | grep config.osd.language|sed '/^config.osd.language=/!d'").read()
leng2 = leng.replace('config.osd.language=', '').replace('_', '-').replace('\n', '')
language = leng2[:-3]


class webcamList(MenuList):
    def __init__(self, list):
        MenuList.__init__(self, list, True, eListboxPythonMultiContent)
        if Utils.isFHD():
            self.l.setItemHeight(50)
            textfont = int(30)
            self.l.setFont(0, gFont('Regular', textfont))
        else:
            self.l.setItemHeight(40)
            textfont = int(24)
            self.l.setFont(0, gFont('Regular', textfont))


def wcListEntry(name):
    pngx = ico_path1
    res = [name]
    if Utils.isFHD:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(40, 40), png=loadPNG(pngx)))
        res.append(MultiContentEntryText(pos=(70, 0), size=(1000, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    else:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(3, 8), size=(40, 40), png=loadPNG(pngx)))
        res.append(MultiContentEntryText(pos=(50, 0), size=(500, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    return res


def showlist(data, list):
    icount = 0
    plist = []
    for line in data:
        name = data[icount]
        plist.append(wcListEntry(name))
        icount += 1
        list.setList(plist)


def paypal():
    conthelp = "If you like what I do you\n"
    conthelp += "can contribute with a coffee\n"
    conthelp += "scan the qr code and donate € 1.00"
    return conthelp


class Webcam1(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(SKIN_PATH, 'Webcam1.xml')
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.list = []
        self['list'] = webcamList([])
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('')
        self['info'] = Label('HOME VIEW')
        self["paypal"] = Label()
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ButtonSetupActions',
                                     'ColorActions'], {'red': self.close,
                                                       'green': self.okClicked,
                                                       'cancel': self.cancel,
                                                       'back': self.cancel,
                                                       'ok': self.okClicked}, -2)
        self.onFirstExecBegin.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        payp = paypal()
        self["paypal"].setText(payp)

    def openTest(self):
        self.names = []
        self.urls = []
        self.names.append('User Lists')
        self.urls.append('http://worldcam.eu/')  # THISPLUG + '/Playlists'
        self.names.append('skylinewebcams')
        self.urls.append('https://www.skylinewebcams.com/')
        self.names.append('skylinetop')
        self.urls.append('https://www.skylinewebcams.com/')  # {0}/top-live-cams.html'.format(language))
        self.names.append('webcamhopper')
        self.urls.append('https://www.webcamhopper.com/countries.html')

        showlist(self.names, self['list'])

    def okClicked(self):
        idx = self['list'].getSelectionIndex()
        name = self.names[idx]
        if 'User' in name:
            self.session.open(Webcam2)
        elif 'skylinewebcams' in name:
            self.session.open(Webcam4)
        elif 'skylinetop' in name:
            self.session.open(Webcam7)
        elif 'webcamhopper' in name:
            self.session.open(Webcam10)
        else:
            return

    def cancel(self):
        self.close()


class Webcam2(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(SKIN_PATH, 'Webcam1.xml')
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.list = []
        self['list'] = webcamList([])
        self['info'] = Label('UserList')
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('')
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ButtonSetupActions',
                                     'ColorActions'], {'red': self.close,
                                                       'green': self.okClicked,
                                                       'cancel': self.cancel,
                                                       'back': self.cancel,
                                                       'ok': self.okClicked}, -2)
        self.onFirstExecBegin.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        payp = paypal()
        self["paypal"].setText(payp)

    def openTest(self):
        uLists = os.path.join(THISPLUG, 'Playlists')
        self.names = []
        for root, dirs, files in os.walk(uLists):
            for name in files:
                self.names.append(name)
        showlist(self.names, self['list'])

    def okClicked(self):
        i = len(self.names)
        if i < 0:
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
        skin = os.path.join(SKIN_PATH, 'Webcam1.xml')
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.list = []
        self.name = name
        self['list'] = webcamList([])
        self['info'] = Label('UserList')
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('')
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ButtonSetupActions',
                                     'ColorActions'], {'red': self.close,
                                                       'green': self.okClicked,
                                                       'cancel': self.cancel,
                                                       'back': self.cancel,
                                                       'ok': self.okClicked}, -2)
        self.onFirstExecBegin.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        payp = paypal()
        self["paypal"].setText(payp)

    def openTest(self):
        uLists = os.path.join(THISPLUG, 'Playlists')
        file1 = uLists + '/' + self.name
        self.names = []
        self.urls = []
        f1 = open(file1, 'r')
        try:
            for line in f1.readlines():
                if '###' not in line:
                    continue
                line = line.replace('\n', '').strip()
                items = line.split('###')
                name = items[0]
                url = items[1]
                name = html_conv.html_unescape(name)
                self.names.append(name)
                self.urls.append(url)
        except Exception as e:
            print(e)
        showlist(self.names, self['list'])

    def okClicked(self):
        i = len(self.names)
        if i < 0:
            return
        idx = self['list'].getSelectionIndex()
        name = self.names[idx]
        desc = self.names[idx]
        url = self.urls[idx]
        self.session.open(PlayWorldcam, name, url, desc)

    def cancel(self):
        self.close()


class Webcam4(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(SKIN_PATH, 'Webcam1.xml')
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.list = []
        self['list'] = webcamList([])
        self['info'] = Label('Skyline Webcams')
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('')
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ButtonSetupActions',
                                     'ColorActions'], {'red': self.close,
                                                       'green': self.okClicked,
                                                       'cancel': self.cancel,
                                                       'back': self.cancel,
                                                       'ok': self.okClicked}, -2)
        self.onFirstExecBegin.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        payp = paypal()
        self["paypal"].setText(payp)

    def openTest(self):
        self.names = []
        self.urls = []
        BASEURL = 'https://www.skylinewebcams.com/'
        from . import client
        headers = {'User-Agent': client.agent(), 'Referer': BASEURL}
        content = six.ensure_str(client.request(BASEURL, headers=headers))
        regexvideo = 'class="ln_css ln-(.+?)" alt="(.+?)"'
        match = re.compile(regexvideo, re.DOTALL).findall(content)
        items = []
        for url, name in match:
            url1 = '{}/{}.html'.format('https://www.skylinewebcams.com', url)
            name = html_conv.html_unescape(name)
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
        if i < 0:
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
        skin = os.path.join(SKIN_PATH, 'Webcam1.xml')
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.list = []
        self['list'] = webcamList([])
        self['info'] = Label(name)
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('')
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ButtonSetupActions',
                                     'ColorActions'], {'red': self.close,
                                                       'green': self.okClicked,
                                                       'cancel': self.cancel,
                                                       'back': self.cancel,
                                                       'ok': self.okClicked}, -2)
        self.name = name
        self.url = url
        self.onFirstExecBegin.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        payp = paypal()
        self["paypal"].setText(payp)

    def openTest(self):
        self.names = []
        self.urls = []
        BASEURL = 'https://www.skylinewebcams.com/'
        from . import client
        headers = {'User-Agent': client.agent(), 'Referer': BASEURL}
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
        if i < 0:
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
        skin = os.path.join(SKIN_PATH, 'Webcam1.xml')
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.list = []
        self['list'] = webcamList([])
        self['info'] = Label(name)
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('')
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ButtonSetupActions',
                                     'ColorActions'], {'red': self.close,
                                                       'green': self.okClicked,
                                                       'cancel': self.cancel,
                                                       'back': self.cancel,
                                                       'ok': self.okClicked}, -2)
        self.name = name
        self.url = url
        self.onFirstExecBegin.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        payp = paypal()
        self["paypal"].setText(payp)

    def openTest(self):
        self.names = []
        self.urls = []
        BASEURL = 'https://www.skylinewebcams.com/'
        from . import client
        headers = {'User-Agent': client.agent(), 'Referer': BASEURL}
        content = six.ensure_str(client.request(self.url, headers=headers))
        n1 = content.find('col-xs-12"><h1>', 0)
        n2 = content.find('</div>', n1)
        content2 = content[n1:n2]
        ctry = self.url.replace('https://www.skylinewebcams.com/', '')
        ctry = ctry.replace('.html', '')
        regexvideo = '<a href="/' + ctry + '/(.+?)".*?tag">(.+?)</a>'
        match = re.compile(regexvideo, re.DOTALL).findall(content2)
        items = []
        for url, name in match:
            url1 = '{}/{}/{}'.format('https://www.skylinewebcams.com', ctry, url)
            name = html_conv.html_unescape(name)
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
        if i < 0:
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
        skin = os.path.join(SKIN_PATH, 'Webcam1.xml')
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.list = []
        self.name = name
        self.url = url
        self['list'] = webcamList([])
        self['info'] = Label(name)
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('Export')
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ButtonSetupActions',
                                     'ColorActions'], {'red': self.close,
                                                       'green': self.okClicked,
                                                       'cancel': self.cancel,
                                                       'yellow': self.crea_bouquet,
                                                       'back': self.cancel,
                                                       'ok': self.okClicked}, -2)
        self.onFirstExecBegin.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        payp = paypal()
        self["paypal"].setText(payp)

    def openTest(self):
        self.names = []
        self.urls = []
        BASEURL = 'https://www.skylinewebcams.com/'
        from . import client
        headers = {'User-Agent': client.agent(), 'Referer': BASEURL}
        content = six.ensure_str(client.request(self.url, headers=headers))
        stext = self.url.replace('https://www.skylinewebcams.com/', '')
        stext = stext.replace('.html', '')
        stext = stext + '/'
        regexvideo = '><a href="' + stext + '(.+?)".*?alt="(.+?)"'
        match = re.compile(regexvideo, re.DOTALL).findall(content)

        items = []
        for url, name in match:
            url1 = '{}/{}{}'.format('https://www.skylinewebcams.com', stext, url)
            name = html_conv.html_unescape(name)
            item = name + "###" + url1 + '\n'
            items.append(item)
        items.sort()

        self.xxxname = '/tmp/' + self.name + '_conv.m3u'
        with open(self.xxxname, 'w') as e:
            for item in items:
                e.write(item)
        e.close

        for item in items:
            name = item.split('###')[0]
            url1 = item.split('###')[1]
            self.names.append(name)
            self.urls.append(url1)

        showlist(self.names, self['list'])

    def okClicked(self):
        i = len(self.names)
        if i < 0:
            return
        idx = self['list'].getSelectionIndex()
        url1 = self.urls[idx]
        name = self.names[idx]
        self.getVid(name, url1)

    def getVid(self, name, url):
        try:
            content = Utils.ReadUrl2(url, refer)
            if PY3:
                content = six.ensure_str(content)

            if "source:'livee.m3u8" in content:
                regexvideo = "source:'livee.m3u8(.+?)'"
                match = re.compile(regexvideo, re.DOTALL).findall(content)
                id = match[0]
                id = id.replace('?a=', '')
                if id or id != '':
                    url = "https://hd-auth.skylinewebcams.com/live.m3u8?a=" + id
                    ref = url.replace(":", "%3a").replace("\\", "/")
                    desc = name
                    self.session.open(PlayWorldcam2, name, ref, desc)

            elif "videoId:" in content:
                regexvideo = "videoId.*?'(.*?)'"
                match = re.compile(regexvideo, re.DOTALL).findall(content)
                id = match[0]
                ref = 'https://www.youtube.com/watch?v=' + id
                desc = name
                try:
                    self.session.open(PlayWorldcam, name, ref, desc)
                except:
                    pass
            else:
                return 'http://patbuweb.com/iptv/e2liste/startend.avi'
        except Exception as e:
            print(e)

    def cancel(self):
        self.close()

    def crea_bouquet(self, answer=None):
        if answer is None:
            self.session.openWithCallback(self.crea_bouquet, MessageBox, _("Do you want to Convert to Favorite Bouquet ?\n\nAttention!! Wait while converting !!!"))
        elif answer:

            if os.path.exists(self.xxxname) and os.stat(self.xxxname).st_size > 0:
                name_clean = Utils.cleanName(self.name)
                name_file = name_clean.replace('.m3u', '')
                bouquetname = 'userbouquet.%s.tv' % (name_file.lower())
                print("Converting Bouquet %s" % name_file)
                path1 = '/etc/enigma2/' + str(bouquetname)
                path2 = '/etc/enigma2/bouquets.tv'
                name = ''
                servicez = ''
                descriptionz = ''
                self.tmplist = []
                self.tmplist.append('#NAME %s Worldcam by Lululla' % name_file)
                self.tmplist.append('#SERVICE 1:64:0:0:0:0:0:0:0:0::%s CHANNELS' % name_file)
                self.tmplist.append('#DESCRIPTION --- %s ---' % name_file)
                tag = '1'
                for line in open(self.xxxname):
                    name = line.split('###')[0]
                    ref = line.split('###')[1]

                    # if PY3:
                        # content = six.ensure_str(content)

                    ref = 'streamlink%3a//' + ref.replace(":", "%3a").replace("\\", "/")

                    descriptiona = ('#DESCRIPTION %s' % name).splitlines()
                    descriptionz = ''.join(descriptiona)
                    servicea = ('#SERVICE 4097:0:%s:0:0:0:0:0:0:0:%s' % (tag, ref))
                    servicex = (servicea + ':' + name).splitlines()
                    servicez = ''.join(servicex)
                    print(descriptionz)
                    print(servicez)
                    # if servicez not in self.tmplist:
                    self.tmplist.append(servicez)
                    self.tmplist.append(descriptionz)

                with open(path1, 'w+') as s:
                    for item in self.tmplist:
                        # if item not in s.read():
                        s.write("%s\n" % item)
                        print('item  -> ', item)
                    # s.close()
                in_bouquets = 0
                for line in open('/etc/enigma2/bouquets.tv'):
                    if bouquetname in line:
                        in_bouquets = 1
                if in_bouquets == 0:
                    with open(path2, 'a+') as f:
                        bouquetTvString = '#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "' + str(bouquetname) + '" ORDER BY bouquet\n'
                        f.write(str(bouquetTvString))
                try:
                    from enigma import eDVBDB
                    eDVBDB.getInstance().reloadServicelist()
                    eDVBDB.getInstance().reloadBouquets()
                    print('all bouquets reloaded...')
                except:
                    eDVBDB = None
                    os.system('wget -qO - http://127.0.0.1/web/servicelistreload?mode=2 > /dev/null 2>&1 &')
                    print('bouquets reloaded...')
                # f.close()
                # for x in self.tmplist:
                    # del self.tmplist[0]
                # del self.tmplist[:]
                message = self.session.open(MessageBox, _('bouquets reloaded..'), MessageBox.TYPE_INFO, timeout=5)
                message.setTitle(_("Reload Bouquet"))
            return


class Webcam7(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(SKIN_PATH, 'Webcam1.xml')
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.list = []
        self['list'] = webcamList([])
        self['info'] = Label('Skyline Top')
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('')
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ButtonSetupActions',
                                     'ColorActions'], {'red': self.close,
                                                       'green': self.okClicked,
                                                       'cancel': self.cancel,
                                                       'back': self.cancel,
                                                       'ok': self.okClicked}, -2)
        self.onFirstExecBegin.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        payp = paypal()
        self["paypal"].setText(payp)

    def openTest(self):
        self.names = []
        self.urls = []
        BASEURL = 'https://www.skylinewebcams.com/'
        from . import client
        headers = {'User-Agent': client.agent(), 'Referer': BASEURL}
        content = six.ensure_str(client.request(BASEURL, headers=headers))
        n1 = content.find('dropdown-menu mega-dropdown-menu cat', 0)
        n2 = content.find('</div></div>', n1)
        content2 = content[n1:n2]
        regexvideo = 'href="(.+?)".*?tcam">(.+?)</p>'
        match = re.compile(regexvideo, re.DOTALL).findall(content2)
        for url, name, in match:
            url1 = 'https://www.skylinewebcams.com' + url
            name = html_conv.html_unescape(name)
            self.names.append(name)
            self.urls.append(url1)
        showlist(self.names, self['list'])

    def okClicked(self):
        i = len(self.names)
        if i < 0:
            return
        idx = self['list'].getSelectionIndex()
        name = self.names[idx]
        url = self.urls[idx]
        self.session.open(Webcam8, name, url)  # Webcam5

    def cancel(self):
        self.close()


class Webcam8(Screen):
    def __init__(self, session, name, url):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(SKIN_PATH, 'Webcam1.xml')
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.list = []
        self['list'] = webcamList([])
        self['info'] = Label(name)
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('Export')
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ButtonSetupActions',
                                     'ColorActions'], {'red': self.close,
                                                       'green': self.okClicked,
                                                       'yellow': self.crea_bouquet,
                                                       'cancel': self.cancel,
                                                       'back': self.cancel,
                                                       'ok': self.okClicked}, -2)
        self.name = name
        self.url = url
        self.onFirstExecBegin.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        payp = paypal()
        self["paypal"].setText(payp)

    def openTest(self):
        self.names = []
        self.urls = []
        items = []
        BASEURL = 'https://www.skylinewebcams.com/{0}/webcam.html'
        from . import client, dom_parser as dom   # ,control
        headers = {'User-Agent': client.agent(), 'Referer': BASEURL}
        content = six.ensure_str(client.request(self.url, headers=headers))
        data = client.parseDOM(content, 'div', attrs={'class': 'container'})[0]
        data = dom.parse_dom(data, 'a', req='href')
        data = [i for i in data if 'subt' in i.content]
        for item in data:
            link = item.attrs['href']
            if link == '#':
                continue
            link = html_conv.html_unescape(link)
            name = client.parseDOM(item.content, 'img', ret='alt')[0]
            name = html_conv.html_unescape(name)
            if six.PY2:
                link = link.encode('utf-8')
                name = name.encode('utf-8')
            base_url = 'https://www.skylinewebcams.com'
            url = '{}/{}'.format(base_url, link)
            name = html_conv.html_unescape(name)
            item = name + "###" + url + '\n'
            items.append(item)
        items.sort()

        self.xxxname = '/tmp/' + self.name + '_conv.m3u'
        with open(self.xxxname, 'w') as e:
            for item in items:
                e.write(item)
        e.close
        for item in items:
            name = item.split('###')[0]
            url = item.split('###')[1]
            self.names.append(name)
            self.urls.append(url)
        showlist(self.names, self['list'])

    def okClicked(self):
        i = len(self.names)
        if i < 0:
            return
        idx = self['list'].getSelectionIndex()
        url1 = self.urls[idx]
        name = self.names[idx]
        self.getVid(name, url1)

    def getVid(self, name, url):
        try:
            content = Utils.ReadUrl2(url, refer)
            if PY3:
                content = six.ensure_str(content)
            if "source:'livee.m3u8" in content:
                regexvideo = "source:'livee.m3u8(.+?)'"
                match = re.compile(regexvideo, re.DOTALL).findall(content)
                id = match[0]
                id = id.replace('?a=', '')
                if id or id != '':
                    url = "https://hd-auth.skylinewebcams.com/live.m3u8?a=" + id
                    ref = url.replace(":", "%3a").replace("\\", "/")
                    desc = name
                    self.session.open(PlayWorldcam2, name, ref, desc)
            elif "videoId:" in content:
                regexvideo = "videoId.*?'(.*?)'"
                match = re.compile(regexvideo, re.DOTALL).findall(content)
                id = match[0]
                ref = 'https://www.youtube.com/watch?v=' + id
                desc = name
                try:
                    self.session.open(PlayWorldcam, name, ref, desc)
                except:
                    pass
            else:
                return 'http://patbuweb.com/iptv/e2liste/startend.avi'
        except Exception as e:
            print(e)

    def crea_bouquet(self, answer=None):
        if answer is None:
            self.session.openWithCallback(self.crea_bouquet, MessageBox, _("Do you want to Convert to Favorite Bouquet ?\n\nAttention!! Wait while converting !!!"))
        elif answer:
            if os.path.exists(self.xxxname) and os.stat(self.xxxname).st_size > 0:
                name_clean = Utils.cleanName(self.name)
                name_file = name_clean.replace('.m3u', '')
                bouquetname = 'userbouquet.%s.tv' % (name_file.lower())
                print("Converting Bouquet %s" % name_file)
                path1 = '/etc/enigma2/' + str(bouquetname)
                path2 = '/etc/enigma2/bouquets.tv'
                name = ''
                servicez = ''
                descriptionz = ''
                self.tmplist = []
                self.tmplist.append('#NAME %s Worldcam by Lululla' % name_file)
                self.tmplist.append('#SERVICE 1:64:0:0:0:0:0:0:0:0::%s CHANNELS' % name_file)
                self.tmplist.append('#DESCRIPTION --- %s ---' % name_file)
                tag = '1'
                for line in open(self.xxxname):
                    name = line.split('###')[0]
                    ref = line.split('###')[1]
                    # if PY3:
                        # content = six.ensure_str(content)
                    ref = 'streamlink%3a//' + ref.replace(":", "%3a").replace("\\", "/")
                    descriptiona = ('#DESCRIPTION %s' % name).splitlines()
                    descriptionz = ''.join(descriptiona)
                    servicea = ('#SERVICE 4097:0:%s:0:0:0:0:0:0:0:%s' % (tag, ref))
                    servicex = (servicea + ':' + name).splitlines()
                    servicez = ''.join(servicex)
                    print(descriptionz)
                    print(servicez)
                    # if servicez not in self.tmplist:
                    self.tmplist.append(servicez)
                    self.tmplist.append(descriptionz)

                with open(path1, 'w+') as s:
                    for item in self.tmplist:
                        # if item not in s.read():
                        s.write("%s\n" % item)
                        print('item  -> ', item)
                    # s.close()
                in_bouquets = 0
                for line in open('/etc/enigma2/bouquets.tv'):
                    if bouquetname in line:
                        in_bouquets = 1
                if in_bouquets == 0:
                    with open(path2, 'a+') as f:
                        bouquetTvString = '#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "' + str(bouquetname) + '" ORDER BY bouquet\n'
                        f.write(str(bouquetTvString))
                try:
                    from enigma import eDVBDB
                    eDVBDB.getInstance().reloadServicelist()
                    eDVBDB.getInstance().reloadBouquets()
                    print('all bouquets reloaded...')
                except:
                    eDVBDB = None
                    os.system('wget -qO - http://127.0.0.1/web/servicelistreload?mode=2 > /dev/null 2>&1 &')
                    print('bouquets reloaded...')
                # f.close()
                # for x in self.tmplist:
                    # del self.tmplist[0]
                # del self.tmplist[:]
                message = self.session.open(MessageBox, _('bouquets reloaded..'), MessageBox.TYPE_INFO, timeout=5)
                message.setTitle(_("Reload Bouquet"))
            return

    def cancel(self):
        self.close()


class Webcam10(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(SKIN_PATH, 'Webcam1.xml')
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.list = []
        self['list'] = webcamList([])
        self['info'] = Label('Webcam Hopper Cams')
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('')
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ButtonSetupActions',
                                     'ColorActions'], {'red': self.close,
                                                       'green': self.okClicked,
                                                       'cancel': self.cancel,
                                                       'back': self.cancel,
                                                       'ok': self.okClicked}, -2)
        self.onFirstExecBegin.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        payp = paypal()
        self["paypal"].setText(payp)

    def openTest(self):
        self.names = []
        self.urls = []
        BASEURL = 'https://www.webcamhopper.com/'
        from . import client
        headers = {'User-Agent': client.agent(), 'Referer': BASEURL}
        content = six.ensure_str(client.request('https://www.webcamhopper.com/countries.html', headers=headers))
        n1 = content.find('Webcams by Country', 0)
        n2 = content.find('</a></li></ul>', n1)
        content2 = content[n1:n2]
        print('content2 ', content2)
        regexvideo = '<li><a tabindex="-1" href="(.+?)">(.+?)<span'
        match = re.compile(regexvideo, re.DOTALL).findall(content2)
        print('match2 ', match)
        items = []
        for url, name in match:
            url1 = '{}/{}'.format('https://www.webcamhopper.com', url)
            name = html_conv.html_unescape(name)
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
        if i < 0:
            return
        idx = self['list'].getSelectionIndex()
        name = self.names[idx]
        url = self.urls[idx]
        self.session.open(Webcam11, name, url)

    def cancel(self):
        self.close()


class Webcam11(Screen):
    def __init__(self, session, name, url):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(SKIN_PATH, 'Webcam1.xml')
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.list = []
        self.name = name
        self.url = url
        self['list'] = webcamList([])
        self['info'] = Label(name)
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('')
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ButtonSetupActions',
                                     'ColorActions'], {'red': self.close,
                                                       'green': self.okClicked,
                                                       'cancel': self.cancel,
                                                       'back': self.cancel,
                                                       'ok': self.okClicked}, -2)
        self.onFirstExecBegin.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        payp = paypal()
        self["paypal"].setText(payp)

    def openTest(self):
        self.names = []
        self.urls = []
        BASEURL = 'https://www.webcamhopper.com/'
        from . import client
        headers = {'User-Agent': client.agent(), 'Referer': BASEURL}
        content = six.ensure_str(client.request(self.url, headers=headers))
        n1 = content.find('"mc-top-left"', 0)
        n2 = content.find('mc-top-right', n1)
        content2 = content[n1:n2]
        print('content2 ', content2)
        regexvideo = '<div class="rank-section"><div class="rank-pic"><a href="(.+?)".*?img src="(.+?)".*?alt="(.+?)".*?">(.+?)</a></div></div><div '  # width="'
        match = re.compile(regexvideo, re.DOTALL).findall(content2)
        print('match2 ', match)

        items = []
        for url, pic, name, name2 in match:
            # url1 = '{}/{}'.format('https://www.webcamhopper.com', url)
            name = html_conv.html_unescape(name)
            pic = 'https://www.webcamhopper.com/' + pic
            url = url
            name2 = name2
            print(name + '\n' + pic + '\n' + url + '\n' + '\n' + name2 + '\n')
            item = name + "###" + url
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
        if i < 0:
            return
        idx = self['list'].getSelectionIndex()
        name = self.names[idx]
        url = self.urls[idx]
        print(name + '\n' + url + '\n')
        self.session.open(Webcam12, name, url)

    def cancel(self):
        self.close()


class Webcam12(Screen):
    def __init__(self, session, name, url):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(SKIN_PATH, 'Webcam1.xml')
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.list = []
        self.name = name
        self.url = url
        self['list'] = webcamList([])
        self['info'] = Label('Skyline Webcams')
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('')
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ButtonSetupActions',
                                     'ColorActions'], {'red': self.close,
                                                       'green': self.okClicked,
                                                       'cancel': self.cancel,
                                                       'back': self.cancel,
                                                       'ok': self.okClicked}, -2)

        self.onFirstExecBegin.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        payp = paypal()
        self["paypal"].setText(payp)

    def openTest(self):
        self.names = []
        self.urls = []
        BASEURL = 'https://www.webcamhopper.com/'
        from . import client
        try:
            headers = {'User-Agent': client.agent(), 'Referer': BASEURL}
            content = six.ensure_str(client.request(self.url, headers=headers))
            print('content: ', content)
            n0 = content.find('skylinewebcams')
            print('n0 skiline ', n0)
            if n0 != -1:  # if 'skylinewebcams' in content:
                regexvideo = 'href="https://www.skylinewebcams.com/(.+?)"'
                match = re.compile(regexvideo, re.DOTALL).findall(content)
                url = 'https://www.skylinewebcams.com/' + match[0]
                print(url)
                content = Utils.ReadUrl2(url, refer)
                if PY3:
                    content = six.ensure_str(content)
                if "source:'livee.m3u8" in content:
                    regexvideo = "source:'livee.m3u8(.+?)'"
                    match = re.compile(regexvideo, re.DOTALL).findall(content)
                    id = match[0]
                    id = id.replace('?a=', '')
                    if id or id != '':
                        url = "https://hd-auth.skylinewebcams.com/live.m3u8?a=" + id
                        ref = url.replace(":", "%3a").replace("\\", "/")
                        desc = self.name
                        self.session.open(PlayWorldcam2, self.name, ref, desc)
                elif "videoId:" in content:
                    regexvideo = "videoId.*?'(.*?)'"
                    match = re.compile(regexvideo, re.DOTALL).findall(content)
                    id = match[0]
                    ref = 'https://www.youtube.com/watch?v=' + id
                    desc = self.name
                    try:
                        self.session.open(PlayWorldcam, self.name, ref, desc)
                    except:
                        pass
                else:
                    return 'http://patbuweb.com/iptv/e2liste/startend.avi'
                self.close()
            else:
                n1 = content.find('class="map-data-host">', 0)
                n2 = content.find('View Webcam</a></div></div>', n1)
                content2 = content[n1:n2]
                print('content2 ', content2)

                regexvideo = 'image"><a href="(.+?)".*?img src="(.+?)".*?alt="(.+?)"'
                match = re.compile(regexvideo, re.DOTALL).findall(content)
                items = []
                for url, pic, name in match:
                    # url1 = '{}/{}'.format('https://www.webcamhopper.com', url)
                    url = url
                    pic = 'https://www.webcamhopper.com/' + pic
                    name = html_conv.html_unescape(name)
                    print(name + '\n' + pic + '\n' + url + '\n')
                    item = name + "###" + url
                    items.append(item)
                items.sort()
                for item in items:
                    name = item.split('###')[0]
                    url1 = item.split('###')[1]
                    self.names.append(name)
                    self.urls.append(url1)
                showlist(self.names, self['list'])
        except Exception as e:
            print('openTest ', e)

    def okClicked(self):
        i = len(self.names)
        if i < 0:
            return
        idx = self['list'].getSelectionIndex()
        name = self.names[idx]
        url = self.urls[idx]
        print(name + '\n' + url + '\n')
        self.session.open(PlayWorldcam, name, url, name)

    def cancel(self):
        self.close()


class PlayWorldcam(Screen):
    def __init__(self, session, name, url, desc):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(SKIN_PATH, 'Webcam1.xml')
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.list = []
        self.name = name
        self.url = url
        self.desc = desc
        self.srefInit = self.session.nav.getCurrentlyPlayingServiceReference()
        self['list'] = webcamList([])
        self['info'] = Label('Select Player')
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('')
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ButtonSetupActions',
                                     'ColorActions'], {'red': self.close,
                                                       'green': self.okClicked,
                                                       'cancel': self.cancel,
                                                       'back': self.cancel,
                                                       'ok': self.okClicked}, -2)
        self.onFirstExecBegin.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        payp = paypal()
        self["paypal"].setText(payp)

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
        self.names.append('Streamlink')
        self.urls.append(url)
        # self.names.append('Test Youtube')
        # self.urls.append(url)
        showlist(self.names, self['list'])

    def okClicked(self):
        i = len(self.names)
        if i < 0:
            return
        idx = self['list'].getSelectionIndex()
        # self.name = self.names[idx]
        self.url = self.urls[idx]
        cmd = ''
        if idx == 0:
            self.play()
        elif idx == 1:
            try:
                os.remove('/tmp/hls.avi')
            except:
                pass
            header = ''
            cmd = 'python "/usr/lib/enigma2/python/Plugins/Extensions/WorldCam/lib/hlsclient.py" "' + self.url + '" "1" "' + header + '" + &'
            os.system(cmd)
            os.system('sleep 3')
            self.url = '/tmp/hls.avi'
            self.play()
        elif idx == 2:
            try:
                os.remove('/tmp/hls.avi')
            except:
                pass
            cmd = 'python "/usr/lib/enigma2/python/Plugins/Extensions/WorldCam/lib/tsclient.py" "' + self.url + '" "1" + &'
            os.system(cmd)
            os.system('sleep 3')
            self.url = '/tmp/hls.avi'
            # self.name = self.names[idx]
            self.play()
        elif idx == 3:
            self.play2()
        else:
            '''
            try:
                os.remove('/tmp/vid.txt')
            except:
                pass
            cmd = "python '/usr/lib/enigma2/python/Plugins/Extensions/WorldCam/scripts/script.module.ytdl/lib/__main__.py' -f mp4/bestvideo+bestaudio --no-check-certificate --skip-download --get-url " + self.url + " > /tmp/vid.txt"
            os.system(cmd)
            os.system('sleep 3')
            currenturl = open('/tmp/vid.txt', 'r')
            currenturl = currenturl.read()
            self.url = currenturl.strip()  # '/tmp/vid.txt'
            self.name = self.names[idx]
            self.play()
            '''
            pass
        print('In playVideo url =', self.url)
        print('In playVideo  cmd =', cmd)
        return

    def playfile(self, serverint):
        self.serverList[serverint].play(self.session, self.url, self.name)

    def play(self):
        desc = self.desc
        name = self.name
        self.session.open(PlayWorldcam2, name, self.url, desc)

    def play2(self):
        if Utils.isStreamlinkAvailable():
            desc = self.desc
            name = self.name
            url = self.url
            url = url.replace(':', '%3a')
            # print('In url =', url)
            # print(type(url))
            sref = 'http%3a//127.0.0.1%3a8088/' + url
            self.session.open(PlayWorldcam2, name, sref, desc)
            self.close()
        else:
            self.session.open(MessageBox, 'Install Streamlink first', MessageBox.TYPE_INFO, timeout=5)

    def cancel(self):
        self.session.nav.stopService()
        self.session.nav.playService(self.srefInit)
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
        self["ShowHideActions"] = ActionMap(["InfobarShowHideActions"], {"toggleShow": self.OkPressed, "hide": self.hide}, 0)
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

    def debug(obj, text=""):
        print(text + " %s\n" % obj)


class PlayWorldcam2(
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
        global streaml
        # global _session
        Screen.__init__(self, session)
        self.session = session
        self.skinName = 'MoviePlayer'
        # _session = session
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
        self.srefInit = self.session.nav.getCurrentlyPlayingServiceReference()
        self.allowPiP = False
        self.service = None
        self.url = url
        self.desc = desc
        self.name = html_conv.html_unescape(name)
        self.state = self.STATE_PLAYING
        self['actions'] = ActionMap(['MoviePlayerActions',
                                     'MovieSelectionActions',
                                     'MediaPlayerActions',
                                     'EPGSelectActions',
                                     'MediaPlayerSeekActions',
                                     'DirectionActions',
                                     'ButtonSetupActions',
                                     'OkCancelActions',
                                     'InfobarShowHideActions',
                                     'InfobarActions',
                                     'InfobarSeekActions'], {'stop': self.cancel,
                                                             # 'epg': self.showIMDB,
                                                             'leavePlayer': self.cancel,
                                                             'epg': self.cicleStreamType,
                                                             # 'info': self.showIMDB,
                                                             'playpauseService': self.playpauseService,
                                                             'yellow': self.subtitles,
                                                             'tv': self.cicleStreamType,
                                                             'cancel': self.cancel,
                                                             'back': self.leavePlayer,
                                                             'down': self.av}, -1)
        # if "youtube" or 'skylinewebcams' in self.url.lower():
        if "youtube" in self.url.lower():
            print('youtube in url')
            self.onFirstExecBegin.append(self.openYtdl)
        elif "vistalive" in self.url.lower():
            print('vistalive in url')
            self.onFirstExecBegin.append(self.openYtdl)            
            
        elif '8088' in self.url:
            self.onFirstExecBegin.append(self.slinkPlay)
        else:
            self.onFirstExecBegin.append(self.cicleStreamType)
        # self.onFirstExecBegin.append(self.openYtdl)
        self.onClose.append(self.cancel)

    def getAspect(self):
        return AVSwitch().getAspectRatioSetting()

    def getAspectString(self, aspectnum):
        return {
            0: '4:3 Letterbox',
            1: '4:3 PanScan',
            2: '16:9',
            3: '16:9 always',
            4: '16:10 Letterbox',
            5: '16:10 PanScan',
            6: '16:9 Letterbox'
        }[aspectnum]

    def setAspect(self, aspect):
        map = {
            0: '4_3_letterbox',
            1: '4_3_panscan',
            2: '16_9',
            3: '16_9_always',
            4: '16_10_letterbox',
            5: '16_10_panscan',
            6: '16_9_letterbox'
        }
        config.av.aspectratio.setValue(map[aspect])
        try:
            AVSwitch().setAspectRatio(aspect)
        except:
            pass

    def av(self):
        temp = int(self.getAspect())
        temp += 1
        if temp > 6:
            temp = 0
        self.new_aspect = temp
        self.setAspect(temp)

    def to_bytes(value, encoding='utf-8'):
        """
        Makes sure the value is encoded as a byte string.

        :param value: The Python string value to encode.
        :param encoding: The encoding to use.
        :return: The byte string that was encoded.
        """
        if isinstance(value, six.binary_type):
            return value
        return value.encode(encoding)

    def slinkPlay(self):
        name = self.name
        url = '5002:0:1:0:0:0:0:0:0:0:' + self.url
        if PY3:
            url = url.encode()
        print('type url value ', type(url))
        sref = eServiceReference(url)
        sref.setName(name)
        self.session.nav.stopService()
        self.session.nav.playService(sref)

    def openPlay(self, servicetype, url):
        try:
            name = self.name
            ref = "{0}:0:1:0:0:0:0:0:0:0:{1}:{2}".format(servicetype, url.replace(":", "%3a"), name.replace(":", "%3a"))
            print('reference:   ', ref)
            if streaml is True:
                url = 'http://127.0.0.1:8088/' + url
                ref = "{0}:0:1:0:0:0:0:0:0:0:{1}:{2}".format(servicetype, url.replace(":", "%3a"), name.replace(":", "%3a"))
                print('streaml reference:   ', ref)
            print('final reference:   ', ref)
            sref = eServiceReference(ref)
            sref.setName(name)
            self.session.nav.stopService()
            self.session.nav.playService(sref)
        except Exception as e:
            print('error player ', e)

    def openYtdl(self):
        name = self.name
        url = 'streamlink%3a//' + self.url
        servicetype = '4097'
        ref = "{0}:0:1:0:0:0:0:0:0:0:{1}:{2}".format(servicetype, url.replace(":", "%3a"), name.replace(":", "%3a"))
        print('reference youtube:   ', ref)
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
        if "youtube" in url.lower():
            print('youtube in url')
            url = 'streamlink%3a//' + url
            print('final 1 youtube in url')
        '''
        # # if "youtube" in str(self.url):
            # # self.mbox = self.session.open(MessageBox, _('For Stream Youtube coming soon!'), MessageBox.TYPE_INFO, timeout=5)
            # # return
        # if os.path.exists("/usr/bin/gstplayer"):
            # streamtypelist.append("5001")
        # if os.path.exists("/usr/bin/exteplayer3"):
            # streamtypelist.append("5002")
        # if os.path.exists("/usr/bin/apt-get"):
            # streamtypelist.append("8193")
        # if Utils.isStreamlinkAvailable():
            # streamtypelist.append("5002")  # ref = '5002:0:1:0:0:0:0:0:0:0:http%3a//127.0.0.1%3a8088/' + url
            # streaml = True
        # if os.path.exists("/usr/bin/gstplayer"):
            # streamtypelist.append("5001")
        # if os.path.exists("/usr/bin/exteplayer3"):
            # streamtypelist.append("5002")
        # if os.path.exists("/usr/bin/apt-get"):
            # streamtypelist.append("8193")
        '''
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

    def subtitles(self):
        self.session.open(MessageBox, 'Please install script.module.SubSupport.', MessageBox.TYPE_ERROR, timeout=10)

    def showAfterSeek(self):
        if isinstance(self, TvInfoBarShowHide):
            self.doShow()

    def cancel(self):
        if os.path.exists('/tmp/hls.avi'):
            os.remove('/tmp/hls.avi')
        self.session.nav.stopService()
        self.session.nav.playService(self.srefInit)
        if not self.new_aspect == self.init_aspect:
            try:
                self.setAspect(self.init_aspect)
            except:
                pass
        streaml = False
        self.close()

    def leavePlayer(self):
        self.close()


class AutoStartTimerwrd:

    def __init__(self, session):
        self.session = session
        global _firstStartwrd
        print("*** running AutoStartTimerwrd ***")
        if _firstStartwrd:
            self.runUpdate()

    def runUpdate(self):
        print("*** running update ***")
        try:
            from . import Update
            Update.upd_done()
            _firstStartwrd = False
        except Exception as e:
            print('error Fxy', e)


def autostart(reason, session=None, **kwargs):
    print("*** running autostart ***")
    global autoStartTimerwrd
    global _firstStartwrd
    if reason == 0:
        if session is not None:
            _firstStartwrd = True
            autoStartTimerwrd = AutoStartTimerwrd(session)
    return


def main(session, **kwargs):
    global _session
    _session = session
    try:
        _session.open(Webcam1)
    except:
        import traceback
        traceback.print_exc()
        pass


def Plugins(**kwargs):
    result = [PluginDescriptor(name='WorldCam', description='Webcams from around the world V. ' + version, where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart),
              PluginDescriptor(name='WorldCam', description='Webcams from around the world V. ' + version, where=PluginDescriptor.WHERE_PLUGINMENU, icon='plugin.png', fnc=main)]
    return result
