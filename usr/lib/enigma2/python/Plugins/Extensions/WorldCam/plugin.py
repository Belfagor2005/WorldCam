#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Plugin Worldcam is developed by Linuxsat-Support Team
last update 01 09 2023
edited from Lululla: updated to 20220113
"""
from __future__ import print_function

from . import _, paypal
from .lib import Utils
from .lib import html_conv
from .lib import client
from .lib.Console import Console as xConsole

from Components.AVSwitch import AVSwitch
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryPixmapAlphaTest, MultiContentEntryText
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.config import config
from datetime import datetime
from enigma import (
    eListboxPythonMultiContent,
    loadPNG,
    gFont,
    # gPixmapPtr,
    eServiceReference,
    eTimer,
    iPlayableService,
    getDesktop,
    RT_VALIGN_CENTER,
    RT_HALIGN_LEFT,
)
from Plugins.Plugin import PluginDescriptor
from Screens.InfoBarGenerics import (
    InfoBarSeek,
    InfoBarAudioSelection,
    InfoBarSubtitleSupport,
    InfoBarMenu,
    InfoBarNotifications,
)
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

import codecs
import json
import os
import re
import six
import ssl
import sys
# import unicodedata

global SKIN_PATH

currversion = '4.6'
setup_title = ('WORLDCAM V.' + currversion)
THISPLUG = '/usr/lib/enigma2/python/Plugins/Extensions/WorldCam'
ico_path1 = os.path.join(THISPLUG, 'pics/webcam.png')
iconpic = 'plugin.png'
enigma_path = '/etc/enigma2'
refer = 'https://www.skylinewebcams.com/'

SKIN_PATH = os.path.join(THISPLUG, 'skin/hd/')
installer_url = 'aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0JlbGZhZ29yMjAwNS9Xb3JsZENhbS9tYWluL2luc3RhbGxlci5zaA=='
developer_url = 'aHR0cHM6Ly9hcGkuZ2l0aHViLmNvbS9yZXBvcy9CZWxmYWdvcjIwMDUvV29ybGRDYW0='

screenwidth = getDesktop(0).size()
if screenwidth.width() == 2560:
    SKIN_PATH = os.path.join(THISPLUG, 'skin/uhd')
elif screenwidth.width() == 1920:
    SKIN_PATH = os.path.join(THISPLUG, 'skin/fhd')
else:
    SKIN_PATH = os.path.join(THISPLUG, 'skin/hd')

PY3 = False
PY3 = sys.version_info.major >= 3

if PY3:
    PY3 = True
    unicode = str


if sys.version_info >= (2, 7, 9):
    try:
        sslContext = ssl._create_unverified_context()
    except:
        sslContext = None

leng = os.popen("cat /etc/enigma2/settings | grep config.osd.language|sed '/^config.osd.language=/!d'").read()
leng2 = leng.replace('config.osd.language=', '').replace('_', '-').replace('\n', '')
language = leng2[:-3]


class webcamList(MenuList):
    def __init__(self, list):
        MenuList.__init__(self, list, True, eListboxPythonMultiContent)
        screen_width = screenwidth.width()
        if screen_width == 2560:
            self.l.setFont(0, gFont('Regular', 48))
            self.l.setItemHeight(56)
        elif screen_width == 1920:
            self.l.setFont(0, gFont('Regular', 30))
            self.l.setItemHeight(50)
        else:
            self.l.setFont(0, gFont('Regular', 24))
            self.l.setItemHeight(45)


def wcListEntry(name):
    pngx = ico_path1
    res = [name]
    screen_width = screenwidth.width()
    if screen_width == 2560:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(60, 60), png=loadPNG(pngx)))
        res.append(MultiContentEntryText(pos=(90, 0), size=(1200, 60), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    elif screen_width == 1920:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(40, 40), png=loadPNG(pngx)))
        res.append(MultiContentEntryText(pos=(70, 0), size=(1000, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    else:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(3, 2), size=(40, 40), png=loadPNG(pngx)))
        res.append(MultiContentEntryText(pos=(50, 0), size=(500, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    return res


def showlist(data, list_widget):
    plist = [wcListEntry(name) for name in data]
    list_widget.setList(plist)


class Webcam1(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(SKIN_PATH, 'Webcam1.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.list = []
        self.srefInit = self.session.nav.getCurrentlyPlayingServiceReference()
        self['list'] = webcamList([])
        self['info'] = Label('HOME VIEW')
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('Update')
        self['key_blue'] = Button('Remove')
        self['key_green'].hide()
        self.Update = False
        self['actions'] = ActionMap(['OkCancelActions',
                                     'DirectionActions',
                                     'HotkeyActions',
                                     'InfobarEPGActions',
                                     'ChannelSelectBaseActions'], {'ok': self.okClicked,
                                                                   'back': self.close,
                                                                   'cancel': self.close,
                                                                   'yellow': self.update_me,  # update_me,
                                                                   'green': self.okClicked,
                                                                   'blue': self.removeb,
                                                                   'yellow_long': self.update_dev,
                                                                   'info_long': self.update_dev,
                                                                   'infolong': self.update_dev,
                                                                   'showEventInfoPlugin': self.update_dev,
                                                                   'red': self.close}, -1)
        self.timer = eTimer()
        if os.path.exists("/usr/bin/apt-get"):
            self.timer_conn = self.timer.timeout.connect(self.check_vers)
        else:
            self.timer.callback.append(self.check_vers)
        self.timer.start(500, 1)
        self.onFirstExecBegin.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)

    def check_vers(self):
        remote_version = '0.0'
        remote_changelog = ''
        req = Utils.Request(Utils.b64decoder(installer_url), headers={'User-Agent': 'Mozilla/5.0'})
        page = Utils.urlopen(req).read()
        if PY3:
            data = page.decode("utf-8")
        else:
            data = page.encode("utf-8")
        if data:
            lines = data.split("\n")
            for line in lines:
                if line.startswith("version"):
                    remote_version = line.split("=")
                    remote_version = line.split("'")[1]
                if line.startswith("changelog"):
                    remote_changelog = line.split("=")
                    remote_changelog = line.split("'")[1]
                    break
        self.new_version = remote_version
        self.new_changelog = remote_changelog
        # if float(currversion) < float(remote_version):
        if currversion < remote_version:
            self.Update = True
            self['key_green'].show()
            self.session.open(MessageBox, _('New version %s is available\n\nChangelog: %s\n\nPress info_long or yellow_long button to start force updating.') % (self.new_version, self.new_changelog), MessageBox.TYPE_INFO, timeout=5)

    def update_me(self):
        if self.Update is True:
            self.session.openWithCallback(self.install_update, MessageBox, _("New version %s is available.\n\nChangelog: %s \n\nDo you want to install it now?") % (self.new_version, self.new_changelog), MessageBox.TYPE_YESNO)
        else:
            self.session.open(MessageBox, _("Congrats! You already have the latest version..."),  MessageBox.TYPE_INFO, timeout=4)

    def update_dev(self):
        try:
            req = Utils.Request(Utils.b64decoder(developer_url), headers={'User-Agent': 'Mozilla/5.0'})
            page = Utils.urlopen(req).read()
            data = json.loads(page)
            remote_date = data['pushed_at']
            strp_remote_date = datetime.strptime(remote_date, '%Y-%m-%dT%H:%M:%SZ')
            remote_date = strp_remote_date.strftime('%Y-%m-%d')
            self.session.openWithCallback(self.install_update, MessageBox, _("Do you want to install update ( %s ) now?") % (remote_date), MessageBox.TYPE_YESNO)
        except Exception as e:
            print('error xcons:', e)

    def install_update(self, answer=False):
        if answer:
            cmd1 = 'wget -q "--no-check-certificate" ' + Utils.b64decoder(installer_url) + ' -O - | /bin/sh'
            self.session.open(xConsole, 'Upgrading...', cmdlist=[cmd1], finishedCallback=self.myCallback, closeOnSuccess=False)
        else:
            self.session.open(MessageBox, _("Update Aborted!"),  MessageBox.TYPE_INFO, timeout=3)

    def myCallback(self, result=None):
        print('result:', result)
        return

    def layoutFinished(self):
        payp = paypal()
        self["paypal"].setText(payp)

    def removeb(self):
        conv = Webcam3(self.session, None)
        conv.removeb()

    def openTest(self):
        self.names = []
        self.urls = []
        self.names.append('User Lists')
        self.urls.append('http://worldcam.eu/')

        self.names.append('skylinewebcams')
        self.urls.append('https://www.skylinewebcams.com/')

        self.names.append('skylinetop')
        self.urls.append('https://www.skylinewebcams.com/')

        showlist(self.names, self['list'])

    def okClicked(self):
        idx = self['list'].getSelectionIndex()
        name = self.names[idx]
        if 'user' in name.lower():
            self.session.open(Webcam2)
        elif 'skylinewebcams' in name:
            self.session.open(Webcam4)
        elif 'skylinetop' in name:
            self.session.open(Webcam7)
        else:
            return

    def cancel(self):
        self.close()


class Webcam2(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(SKIN_PATH, 'Webcam1.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.list = []
        self['list'] = webcamList([])
        self['info'] = Label('UserList')
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('')
        self['key_blue'] = Button('')
        self['key_yellow'].hide()
        self['key_blue'].hide()
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
                self.names.append(str(name))
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
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.list = []
        self.name = name
        self.xxxname = '/tmp/' + str(name) + '_conv.m3u'
        self.srefInit = self.session.nav.getCurrentlyPlayingServiceReference()
        self['list'] = webcamList([])
        self['info'] = Label('UserList')
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('Export')
        self['key_blue'] = Button('Remove')
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ButtonSetupActions',
                                     'ColorActions'], {'red': self.close,
                                                       'green': self.okClicked,
                                                       'cancel': self.cancel,
                                                       'yellow': self.export,
                                                       'blue': self.removeb,
                                                       'back': self.cancel,
                                                       'ok': self.okClicked}, -2)
        self.onFirstExecBegin.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        payp = paypal()
        self["paypal"].setText(payp)

    def export(self):
        conv = Webcam6(self.session, self.name, None)
        conv.crea_bouquet()

    def openTest(self):
        uLists = os.path.join(THISPLUG, 'Playlists')
        file1 = uLists + '/' + self.name
        self.names = []
        self.urls = []
        items = []
        f1 = ''
        if sys.version_info[0] == 3:
            f1 = open(file1, 'r', encoding='UTF-8')
        else:
            f1 = open(file1, 'r')
        try:
            for line in f1.readlines():
                if '###' not in line:
                    continue
                line = line.replace('\n', '').strip()
                itemx = line.split('###')
                name = itemx[0]
                url = itemx[1]
                name = name.replace('.txt', '')
                name = html_conv.html_unescape(name)
                self.names.append(str(name))
                self.urls.append(url)
                item = name + "###" + url + '\n'
                items.append(item)
            items.sort()

            self.xxxname = '/tmp/' + str(self.name) + '_conv.m3u'
            with open(self.xxxname, 'w') as e:
                for item in items:
                    e.write(item)
            showlist(self.names, self['list'])
        except Exception as e:
            print(e)

    def okClicked(self):
        i = len(self.names)
        if i < 0:
            return
        idx = self['list'].getSelectionIndex()
        title = self.names[idx]
        video_url = self.urls[idx]
        stream = eServiceReference(4097, 0, video_url)
        stream.setName(str(title))
        self.session.open(MoviePlayer, stream)

    def cancel(self):
        self.close()

    def removeb(self):
        self.session.openWithCallback(self.deleteBouquets, MessageBox, _("Remove all Worldcam Favorite Bouquet ?"), MessageBox.TYPE_YESNO, timeout=5, default=True)

    def deleteBouquets(self, result):
        """
        Clean up routine to remove any previously made changes
        """
        if result:
            try:
                for fname in os.listdir(enigma_path):
                    if 'userbouquet.wrd_' in fname:
                        Utils.purge(enigma_path, fname)
                    elif 'bouquets.tv.bak' in fname:
                        Utils.purge(enigma_path, fname)
                """
                # if os.path.isdir(epgimport_path):
                    # for fname in os.listdir(epgimport_path):
                        # if 'hbc_' in fname:
                            # os.remove(os.path.join(epgimport_path, fname))
                            """
                os.rename(os.path.join(enigma_path, 'bouquets.tv'), os.path.join(enigma_path, 'bouquets.tv.bak'))
                tvfile = open(os.path.join(enigma_path, 'bouquets.tv'), 'w+')
                bakfile = open(os.path.join(enigma_path, 'bouquets.tv.bak'))
                for line in bakfile:
                    if '.wrd_' not in line:
                        tvfile.write(line)
                bakfile.close()
                tvfile.close()
                self.session.open(MessageBox, _('Worldcam Favorites List have been removed'), MessageBox.TYPE_INFO, timeout=5)
                Utils.ReloadBouquets()
            except Exception as ex:
                print(str(ex))
                raise
        return


class Webcam4(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(SKIN_PATH, 'Webcam1.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.list = []
        self['list'] = webcamList([])
        self['info'] = Label('Skyline Webcams')
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('')
        self['key_blue'] = Button('')
        self['key_yellow'].hide()
        self['key_blue'].hide()
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
        # from . import client
        headers = {'User-Agent': client.agent(), 'Referer': BASEURL}
        content = six.ensure_text(client.request(BASEURL, headers=headers), encoding='utf-8')

        regexvideo = 'class="ln_css ln-(.+?)" alt="(.+?)"'
        match = re.compile(regexvideo, re.DOTALL).findall(content)
        items = []

        for url, name in match:
            url1 = '{}/{}.html'.format('https://www.skylinewebcams.com', url)
            item = name + "###" + url1
            items.append(item)

        items.sort()
        for item in items:
            name = item.split('###')[0]
            url1 = item.split('###')[1]
            name = Utils.getEncodedString(name) if not isinstance(name, unicode) else name
            name = Utils.decodeHtml(name)

            self.names.append(name)
            self.urls.append(url1)

        showlist(self.names, self['list'])

    """
    def openTest(self):
        self.names = []
        self.urls = []
        BASEURL = 'https://www.skylinewebcams.com/'
        # from . import client
        headers = {'User-Agent': client.agent(), 'Referer': BASEURL}
        content = six.ensure_str(client.request(BASEURL, headers=headers))
        regexvideo = 'class="ln_css ln-(.+?)" alt="(.+?)"'
        match = re.compile(regexvideo, re.DOTALL).findall(content)
        items = []
        for url, name in match:
            url1 = '{}/{}.html'.format('https://www.skylinewebcams.com', url)
            item = name + "###" + url1
            items.append(item)
        items.sort()
        for item in items:
            name = item.split('###')[0]
            url1 = item.split('###')[1]
            name = Utils.getEncodedString(name)
            self.names.append(Utils.decodeHtml(name))
            self.urls.append(url1)
        showlist(self.names, self['list'])
    """

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
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.list = []
        self['list'] = webcamList([])
        self['info'] = Label(name)
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('')
        self['key_blue'] = Button('')
        self['key_yellow'].hide()
        self['key_blue'].hide()
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
        # # from . import client
        headers = {'User-Agent': client.agent(), 'Referer': BASEURL}
        content = six.ensure_text(client.request(self.url, headers=headers), encoding='utf-8')

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
            name = Utils.getEncodedString(name) if not isinstance(name, unicode) else name
            name = Utils.decodeHtml(name)
            self.names.append(name)
            self.urls.append(url1)

        showlist(self.names, self['list'])

    """
    def openTest(self):
        self.names = []
        self.urls = []
        BASEURL = 'https://www.skylinewebcams.com/'
        # from . import client
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
            name = Utils.getEncodedString(name)
            self.names.append(Utils.decodeHtml(name))
            self.urls.append(url1)
        showlist(self.names, self['list'])
    """

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
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.list = []
        self['list'] = webcamList([])
        self['info'] = Label(name)
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('')
        self['key_blue'] = Button('')
        self['key_yellow'].hide()
        self['key_blue'].hide()
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
        # from . import client
        headers = {'User-Agent': client.agent(), 'Referer': BASEURL}
        content = six.ensure_text(client.request(self.url, headers=headers), encoding='utf-8')

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
            item = name + "###" + url1
            items.append(item)

        items.sort()
        for item in items:
            name = item.split('###')[0]
            url1 = item.split('###')[1]
            name = Utils.getEncodedString(name) if not isinstance(name, unicode) else name
            name = Utils.decodeHtml(name)
            self.names.append(name)
            self.urls.append(url1)

        showlist(self.names, self['list'])

    """
    def openTest(self):
        self.names = []
        self.urls = []
        BASEURL = 'https://www.skylinewebcams.com/'
        # from . import client
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
            item = name + "###" + url1
            items.append(item)
        items.sort()
        for item in items:
            name = item.split('###')[0]
            url1 = item.split('###')[1]
            name = Utils.getEncodedString(name)
            self.names.append(Utils.decodeHtml(name))
            self.urls.append(url1)
        showlist(self.names, self['list'])
    """

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
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.list = []
        self.name = name
        self.url = url
        self.xxxname = '/tmp/' + str(name) + '_conv.m3u'
        self.srefInit = self.session.nav.getCurrentlyPlayingServiceReference()
        self['list'] = webcamList([])
        self['info'] = Label(name)
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('Export')
        self['key_blue'] = Button('Remove')
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ButtonSetupActions',
                                     'ColorActions'], {'red': self.close,
                                                       'green': self.okClicked,
                                                       'cancel': self.cancel,
                                                       'yellow': self.crea_bouquet,
                                                       'blue': self.removeb,
                                                       'back': self.cancel,
                                                       'ok': self.okClicked}, -2)
        self.onFirstExecBegin.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        payp = paypal()
        self["paypal"].setText(payp)

    def removeb(self):
        conv = Webcam3(self.session, self.name)
        conv.remove()

    def openTest(self):
        self.names = []
        self.urls = []
        BASEURL = 'https://www.skylinewebcams.com/'
        # from . import client
        headers = {'User-Agent': client.agent(), 'Referer': BASEURL}
        content = six.ensure_text(client.request(self.url, headers=headers), encoding='utf-8')
        stext = self.url.replace('https://www.skylinewebcams.com/', '')
        stext = stext.replace('.html', '')
        stext = stext + '/'

        regexvideo = '><a href="' + stext + '(.+?)".*?alt="(.+?)"'
        match = re.compile(regexvideo, re.DOTALL).findall(content)

        items = []
        for url, name in match:
            url1 = '{}/{}{}'.format('https://www.skylinewebcams.com', stext, url)
            item = name + "###" + url1 + '\n'
            items.append(item)

        items.sort()
        self.xxxname = '/tmp/' + str(self.name) + '_conv.m3u'

        with open(self.xxxname, 'w', encoding='utf-8') as e:
            for item in items:
                e.write(item)

        for item in items:
            name = item.split('###')[0]
            url1 = item.split('###')[1]
            name = Utils.getEncodedString(name) if not isinstance(name, unicode) else name
            name = Utils.decodeHtml(name)
            self.names.append(name)
            self.urls.append(url1)

        showlist(self.names, self['list'])

    """
    def openTest(self):
        self.names = []
        self.urls = []
        BASEURL = 'https://www.skylinewebcams.com/'
        # from . import client
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
            item = name + "###" + url1 + '\n'
            items.append(item)
        items.sort()
        self.xxxname = '/tmp/' + str(self.name) + '_conv.m3u'
        with open(self.xxxname, 'w') as e:
            for item in items:
                e.write(item)

        for item in items:
            name = item.split('###')[0]
            url1 = item.split('###')[1]
            name = Utils.getEncodedString(name)
            self.names.append(Utils.decodeHtml(name))
            self.urls.append(url1)
        showlist(self.names, self['list'])
    """

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
                    video_url = "https://hd-auth.skylinewebcams.com/live.m3u8?a=" + id
                    title = name
                    stream = eServiceReference(4097, 0, video_url)
                    stream.setName(str(title))
                    self.session.open(MoviePlayer, stream)

            elif "videoId:" in content:
                regexvideo = "videoId.*?'(.*?)'"
                match = re.compile(regexvideo, re.DOTALL).findall(content)
                id = match[0]
                nid = len(str(id))
                print(nid)
                print('name: %s\nid: %s\nLenYTL: %s' % (str(name), str(id), nid))
                if str(nid) == '11':
                    video_url = 'https://www.youtube.com/watch?v=' + id
                    self.playYTID(video_url, str(name))
            else:
                return 'http://patbuweb.com/iptv/e2liste/startend.avi'
        except Exception as e:
            print(e)

    def openYTID(self, video_url):
        video_url = 'streamlink://' + video_url
        print('reference Youtube 1:   ', )
        stream = eServiceReference(4097, 0, video_url)
        return stream

    def getYTID(self, title, id):
        yttitle = title
        video_url = 'https://www.youtube.com/watch?v=' + id
        print('video_url: %s ' % (video_url))
        self.playYTID(video_url, yttitle)

    def playYTID(self, video_url, yttitle):
        title = yttitle
        stream = eServiceReference(4097, 0, video_url)
        if os.path.exists('/usr/lib/enigma2/python/Plugins/Extensions/YTDLWrapper/plugin.pyo') or os.path.exists('/usr/lib/enigma2/python/Plugins/Extensions/YTDLWrapper/plugin.pyc'):
            video_url = 'streamlink://' + video_url
        else:
            from .youtube_dl import YoutubeDL
            '''
            ydl_opts = {'format': 'best'}
            ydl_opts = {'format': 'bestaudio/best'}
            ydl_opts = {'format': 'best',
                        'no_check_certificate': True,
                        }
            '''
            ydl_opts = {'format': 'best'}
            ydl = YoutubeDL(ydl_opts)
            ydl.add_default_info_extractors()
            result = ydl.extract_info(video_url, download=False)
            video_url = result["url"]
            print("Here in Test url =", video_url)

        stream = eServiceReference(4097, 0, video_url)
        stream.setName(str(title))
        self.session.open(MoviePlayer, stream)

    def crea_bouquet(self, answer=None):
        if answer is None:
            self.session.openWithCallback(self.crea_bouquet, MessageBox, _("Do you want to Convert to Favorite Bouquet ?\n\nAttention!! Wait while converting !!!"))
        elif answer:
            if os.path.exists(self.xxxname) and os.stat(self.xxxname).st_size > 0:
                name_clean = Utils.cleanName(self.name)
                name_file = name_clean.replace('.m3u', '')
                bouquetname = 'userbouquet.wrd_%s.tv' % (name_file.lower())
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
                    if 'youtube' in ref:
                        ref = 'streamlink://' + ref.replace(":", "%3a").replace("\\", "/")
                    else:
                        ref = ref.replace(":", "%3a").replace("\\", "/")
                    descriptiona = ('#DESCRIPTION %s' % name).splitlines()
                    descriptionz = ''.join(descriptiona)
                    servicea = ('#SERVICE 4097:0:%s:0:0:0:0:0:0:0:%s' % (tag, ref))
                    servicex = (servicea + ':' + name).splitlines()
                    servicez = ''.join(servicex)
                    print(descriptionz)
                    print(servicez)
                    self.tmplist.append(servicez)
                    self.tmplist.append(descriptionz)
                with open(path1, 'w+') as s:
                    for item in self.tmplist:
                        s.write("%s\n" % item)
                        print('item  -> ', item)
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

                message = self.session.open(MessageBox, _('bouquets reloaded..'), MessageBox.TYPE_INFO, timeout=5)
                message.setTitle(_("Reload Bouquet"))
            return

    def cancel(self):
        self.close()


class Webcam7(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(SKIN_PATH, 'Webcam1.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.list = []
        self['list'] = webcamList([])
        self['info'] = Label('Skyline Top')
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('')
        self['key_blue'] = Button('')
        self['key_yellow'].hide()
        self['key_blue'].hide()
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
        # from . import client
        headers = {'User-Agent': client.agent(), 'Referer': BASEURL}
        content = six.ensure_text(client.request(BASEURL, headers=headers), encoding='utf-8')
        n1 = content.find('dropdown-menu mega-dropdown-menu cat', 0)
        n2 = content.find('</div></div>', n1)
        content2 = content[n1:n2]

        regexvideo = 'href="(.+?)".*?tcam">(.+?)</p>'
        match = re.compile(regexvideo, re.DOTALL).findall(content2)

        for url, name in match:
            url1 = 'https://www.skylinewebcams.com' + url
            name = Utils.getEncodedString(name) if not isinstance(name, unicode) else name
            name = Utils.decodeHtml(name)
            self.names.append(name)
            self.urls.append(url1)

        showlist(self.names, self['list'])

    """
    def openTest(self):
        self.names = []
        self.urls = []
        BASEURL = 'https://www.skylinewebcams.com/'
        # from . import client
        headers = {'User-Agent': client.agent(), 'Referer': BASEURL}
        content = six.ensure_str(client.request(BASEURL, headers=headers))
        n1 = content.find('dropdown-menu mega-dropdown-menu cat', 0)
        n2 = content.find('</div></div>', n1)
        content2 = content[n1:n2]
        regexvideo = 'href="(.+?)".*?tcam">(.+?)</p>'
        match = re.compile(regexvideo, re.DOTALL).findall(content2)
        for url, name, in match:
            url1 = 'https://www.skylinewebcams.com' + url
            name = Utils.getEncodedString(name)
            self.names.append(Utils.decodeHtml(name))
            self.urls.append(url1)
        showlist(self.names, self['list'])
    """

    def okClicked(self):
        i = len(self.names)
        if i < 0:
            return
        idx = self['list'].getSelectionIndex()
        name = self.names[idx]
        url = self.urls[idx]
        self.session.open(Webcam8, name, url)

    def cancel(self):
        self.close()


class Webcam8(Screen):
    def __init__(self, session, name, url):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(SKIN_PATH, 'Webcam1.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.list = []
        self.name = name
        self.url = url
        self.xxxname = '/tmp/' + str(name) + '_conv.m3u'
        self.srefInit = self.session.nav.getCurrentlyPlayingServiceReference()
        self['list'] = webcamList([])
        self['info'] = Label(name)
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('Export')
        self['key_blue'] = Button('Remove')
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ButtonSetupActions',
                                     'ColorActions'], {'red': self.close,
                                                       'green': self.okClicked,
                                                       'yellow': self.export,
                                                       'blue': self.removeb,
                                                       'cancel': self.cancel,
                                                       'back': self.cancel,
                                                       'ok': self.okClicked}, -2)
        self.onFirstExecBegin.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        payp = paypal()
        self["paypal"].setText(payp)

    def removeb(self):
        conv = Webcam3(self.session, self.name)
        conv.remove()

    def export(self):
        conv = Webcam6(self.session, self.name, None)
        conv.crea_bouquet()

    def openTest(self):
        self.names = []
        self.urls = []
        items = []
        BASEURL = 'https://www.skylinewebcams.com/{0}/webcam.html'
        from .lib import client, dom_parser as dom
        headers = {'User-Agent': client.agent(), 'Referer': BASEURL}
        content = six.ensure_text(client.request(self.url, headers=headers), encoding='utf-8')

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
            if not PY3:
                link = link.encode('utf-8')
                name = name.encode('utf-8')

            base_url = 'https://www.skylinewebcams.com'
            url = '{}/{}'.format(base_url, link)
            name = html_conv.html_unescape(name)
            item = name + "###" + url + '\n'
            items.append(item)
        items.sort()

        self.xxxname = '/tmp/' + str(self.name) + '_conv.m3u'
        with open(self.xxxname, 'w', encoding='utf-8') as e:
            for item in items:
                e.write(item)
        for item in items:
            name = item.split('###')[0]
            url = item.split('###')[1]
            name = Utils.getEncodedString(name) if not isinstance(name, unicode) else name
            name = Utils.decodeHtml(name)
            self.names.append(name)
            self.urls.append(url)

        showlist(self.names, self['list'])

    """
    def openTest(self):
        self.names = []
        self.urls = []
        items = []
        BASEURL = 'https://www.skylinewebcams.com/{0}/webcam.html'
        from .lib import client, dom_parser as dom   # ,control
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
            if not PY3:
                link = link.encode('utf-8')
                name = name.encode('utf-8')
            base_url = 'https://www.skylinewebcams.com'
            url = '{}/{}'.format(base_url, link)
            name = html_conv.html_unescape(name)
            item = name + "###" + url + '\n'
            items.append(item)
        items.sort()
        self.xxxname = '/tmp/' + str(self.name) + '_conv.m3u'
        with open(self.xxxname, 'w') as e:
            for item in items:
                e.write(item)
        for item in items:
            name = item.split('###')[0]
            url = item.split('###')[1]
            name = Utils.getEncodedString(name)
            self.names.append(Utils.decodeHtml(name))
            self.urls.append(url)
        showlist(self.names, self['list'])
    """

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
                    video_url = "https://hd-auth.skylinewebcams.com/live.m3u8?a=" + id
                    title = name

                    stream = eServiceReference(4097, 0, video_url)
                    stream.setName(str(title))
                    self.session.open(MoviePlayer, stream)

            elif "videoId:" in content:
                regexvideo = "videoId.*?'(.*?)'"
                match = re.compile(regexvideo, re.DOTALL).findall(content)
                id = match[0]
                nid = len(str(id))
                print(nid)
                print('name: %s\nid: %s\nLenYTL: %s' % (str(name), str(id), nid))
                if str(nid) == '11':
                    video_url = 'https://www.youtube.com/watch?v=' + id
                    self.playYTID(video_url, str(name))
            else:
                return 'http://patbuweb.com/iptv/e2liste/startend.avi'
        except Exception as e:
            print(e)

    def getYTID(self, title, id):
        yttitle = title  # .encode('ascii', 'replace')
        video_url = 'https://www.youtube.com/watch?v=' + id
        print('video_url: %s ' % (video_url))
        self.playYTID(video_url, yttitle)

    def playYTID(self, video_url, yttitle):
        title = yttitle
        stream = eServiceReference(4097, 0, video_url)
        if os.path.exists('/usr/lib/enigma2/python/Plugins/Extensions/YTDLWrapper/plugin.pyo') or os.path.exists('/usr/lib/enigma2/python/Plugins/Extensions/YTDLWrapper/plugin.pyc'):
            video_url = 'streamlink://' + video_url
        else:
            from .youtube_dl import YoutubeDL
            '''
            ydl_opts = {'format': 'best'}
            ydl_opts = {'format': 'bestaudio/best'}
            ydl_opts = {'format': 'best',
                        'no_check_certificate': True,
                        }
            '''
            ydl_opts = {'format': 'best'}
            ydl = YoutubeDL(ydl_opts)
            ydl.add_default_info_extractors()
            result = ydl.extract_info(video_url, download=False)
            video_url = result["url"]
            print("Here in Test url =", video_url)

        stream = eServiceReference(4097, 0, video_url)
        stream.setName(str(title))
        self.session.open(MoviePlayer, stream)

    def cancel(self):
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


class MoviePlayer(
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

    def __init__(self, session, stream):
        global streaml
        Screen.__init__(self, session)
        self.session = session
        self.skinName = 'MoviePlayer'
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
        self.stream = stream
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
                                                             'leavePlayer': self.cancel,
                                                             'playpauseService': self.playpauseService,
                                                             'yellow': self.subtitles,
                                                             'cancel': self.cancel,
                                                             'back': self.leavePlayer,
                                                             'down': self.av}, -1)
        self.onFirstExecBegin.append(self.openPlay)
        self.onClose.append(self.cancel)

    def getAspect(self):
        return AVSwitch().getAspectRatioSetting()

    def getAspectString(self, aspectnum):
        return {0: '4:3 Letterbox',
                1: '4:3 PanScan',
                2: '16:9',
                3: '16:9 always',
                4: '16:10 Letterbox',
                5: '16:10 PanScan',
                6: '16:9 Letterbox'}[aspectnum]

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

    def openPlay(self):
        try:
            self.session.nav.stopService()
            self.session.nav.playService(self.stream)
        except Exception as e:
            print('error player ', e)

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
        # streaml = False
        self.leavePlayer()

    def leavePlayer(self):
        self.close()


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
    result = [PluginDescriptor(name='WorldCam', description='Webcams from around the world V. ' + str(currversion), where=PluginDescriptor.WHERE_PLUGINMENU, icon='plugin.png', fnc=main)]
    return result
