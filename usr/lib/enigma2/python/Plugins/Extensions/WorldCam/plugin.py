#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

"""
#########################################################
#                                                       #
#  Worldcam Cam from Web Plugin                         #
#  Version: 5.0                                         #
#  Created by Lululla (https://github.com/Belfagor2005) #
#  License: CC BY-NC-SA 4.0                             #
#  https://creativecommons.org/licenses/by-nc-sa/4.0    #
#  Last Modified: "21:50 - 20250606"                    #
#                                                       #
#  Credits:                                             #
#  - Original concept by Pcd - Lululla                  #
#  Usage of this code without proper attribution        #
#  is strictly prohibited.                              #
#  For modifications and redistribution,                #
#  please maintain this credit header.                  #
#########################################################
"""
__author__ = "Lululla"
import sys
import json
import codecs
from datetime import datetime
from os import path as os_path
from six import ensure_str, ensure_text
from sys import version_info

from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.config import config
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryPixmapAlphaTest, MultiContentEntryText
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from enigma import (
    RT_HALIGN_LEFT,
    RT_VALIGN_CENTER,
    eListboxPythonMultiContent,
    eServiceReference,
    eTimer,
    gFont,
    getDesktop,
    iPlayableService,
    loadPNG,
)
from os import walk, listdir, remove, rename
from Plugins.Plugin import PluginDescriptor
from re import compile, DOTALL, findall, search
from Screens.InfoBarGenerics import (
    InfoBarSeek,
    InfoBarAudioSelection,
    InfoBarSubtitleSupport,
    InfoBarMenu,
    InfoBarNotifications,
)
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN
import ssl

from . import (
    _,
    paypal,
    log_to_file,
    # log_exception,
    disable_summary,
    safe_cleanup
)
from .lib import Utils
from .lib import html_conv
from .lib import client
from .lib.AspectManager import AspectManager
from .lib.Console import Console as xConsole

global worldcam_path

currversion = '5.0'
setup_title = f'Worldcam V.{currversion}'
THISPLUG = '/usr/lib/enigma2/python/Plugins/Extensions/WorldCam'
ico_path1 = os_path.join(THISPLUG, 'pics/webcam.png')
iconpic = 'plugin.png'
enigma_path = '/etc/enigma2'
refer = 'https://www.skylinewebcams.com/'
json_path = os_path.join(THISPLUG, 'cowntry_code.json')
worldcam_path = os_path.join(THISPLUG, 'skin/hd/')
installer_url = 'aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0JlbGZhZ29yMjAwNS9Xb3JsZENhbS9tYWluL2luc3RhbGxlci5zaA=='
developer_url = 'aHR0cHM6Ly9hcGkuZ2l0aHViLmNvbS9yZXBvcy9CZWxmYWdvcjIwMDUvV29ybGRDYW0='
language = "en"

aspect_manager = AspectManager()

screen_width = getDesktop(0).size().width()
if screen_width == 2560:
    worldcam_path = os_path.join(THISPLUG, 'skin/uhd')
elif screen_width == 1920:
    worldcam_path = os_path.join(THISPLUG, 'skin/fhd')
else:
    worldcam_path = os_path.join(THISPLUG, 'skin/hd')


PY3 = version_info.major >= 3
if PY3:
    unicode = str
    unichr = chr
    long = int
else:
    sys.setdefaultencoding('utf-8')


if version_info >= (2, 7, 9):
    try:
        sslContext = ssl._create_unverified_context()

    except BaseException:
        sslContext = None


with open("/etc/enigma2/settings", "r") as settings_file:
    for line in settings_file:
        if "config.osd.language=" in line:
            language = line.split("=")[1].strip().split("_")[0]
            break


current_language = language


def set_current_language(lang):
    global current_language
    current_language = lang


def get_current_language():
    return current_language


with open(json_path, "r") as file:
    country_codes = json.load(file)


language_flag_mapping = {
    "en": "gb",  # English - Great Britain
    "it": "it",  # Italian - Italy
    "de": "de",  # German - Germany
    "es": "es",  # Spanish - Spain
    "pl": "pl",  # Polish - Poland
    "el": "gr",  # Greek - Greece
    "fr": "fr",  # French - France
    "hr": "hr",  # Croatian - Croatia
    "sl": "si",  # Slovenian - Slovenia
    "ru": "ru",  # Russian - Russia
    "zh": "cn",  # Chinese - China
}


def get_flag_path(country_code):
    if not country_code:
        return ico_path1

    skin_path = resolveFilename(SCOPE_CURRENT_SKIN)
    flag_path = os_path.join(skin_path, f"countries/{country_code}.png")
    if os_path.isfile(flag_path):
        return flag_path

    plugin_flag_path = os_path.join(THISPLUG, f"countries/{country_code}.png")
    if os_path.isfile(plugin_flag_path):
        return plugin_flag_path

    return ico_path1


class webcamList(MenuList):
    def __init__(self, items):
        """
        Initialize the webcam list with appropriate font size and item height based on screen width.
        """
        MenuList.__init__(self, items, True, eListboxPythonMultiContent)

        self.currsel = -1
        self.currpos = 0

        if screen_width == 2560:
            self.l.setFont(0, gFont('Regular', 44))
            self.l.setItemHeight(55)
        elif screen_width == 1920:
            self.l.setFont(0, gFont('Regular', 32))
            self.l.setItemHeight(50)
        else:
            self.l.setFont(0, gFont('Regular', 24))
            self.l.setItemHeight(45)

    def getCurrentIndex(self):
        return self.currsel

    def getCurrentPosition(self):
        return self.currpos

    def setCurrentIndex(self, idx):
        self.currsel = idx
        self.currpos = idx
        self.instance.moveSelectionTo(idx)

    def setCurrentPosition(self, pos):
        self.currpos = pos
        self.instance.moveSelectionTo(pos)

    def destroy(self):
        log_to_file("Destroying SkylineWebcams", "SkylineWebcams")
        self.lang = None
        if hasattr(self, 'cams'):
            del self.cams
        if hasattr(self, 'items'):
            del self.items


def wcListEntry(name, idx):
    """
    Create an entry for the webcam list with text and icon based on screen width.
    :param name: Name of the webcam.
    :return: List representing the entry.
    """
    res = [name]

    country_code = country_codes.get(name, None)

    # Se non trovato, prova a cercare nel nome pulito
    if not country_code and ":" in name:
        country_part = name.split(":")[-1].strip()
        country_code = country_codes.get(country_part, None)

    # Usa il percorso corretto per la bandiera
    pngx = get_flag_path(country_code)
    if screen_width == 2560:
        res.append(
            MultiContentEntryPixmapAlphaTest(
                pos=(
                    5, 5), size=(
                    60, 50), png=loadPNG(pngx)))
        res.append(
            MultiContentEntryText(
                pos=(
                    90,
                    0),
                size=(
                    1200,
                    60),
                font=0,
                text=name,
                color=0xa6d1fe,
                flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    elif screen_width == 1920:
        res.append(
            MultiContentEntryPixmapAlphaTest(
                pos=(
                    5, 5), size=(
                    50, 40), png=loadPNG(pngx)))
        res.append(
            MultiContentEntryText(
                pos=(
                    80,
                    0),
                size=(
                    950,
                    50),
                font=0,
                text=name,
                color=0xa6d1fe,
                flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    else:
        res.append(
            MultiContentEntryPixmapAlphaTest(
                pos=(
                    3, 2), size=(
                    50, 40), png=loadPNG(pngx)))
        res.append(
            MultiContentEntryText(
                pos=(
                    70,
                    0),
                size=(
                    500,
                    45),
                font=0,
                text=name,
                color=0xa6d1fe,
                flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    return res


def showlist(data, list_widget):
    plist = []
    for idx, name in enumerate(data):
        plist.append(wcListEntry(name, idx))
    try:
        list_widget.setList(plist)
    except Exception as e:
        log_to_file(f"Error setting list: {e}", "CRITICAL")
        if hasattr(list_widget, 'l') and hasattr(list_widget.l, 'setList'):
            list_widget.l.setList(plist)


class SkylineWebcams:

    MAIN_URL = "https://www.skylinewebcams.com/"

    def __init__(self, language="en"):
        self.lang = language

    def get_full_url(self, url):
        full_url = url if url.startswith(
            "http") else self.MAIN_URL + url.lstrip("/")
        log_to_file(
            "Input: %s -> Full URL: %s" %
            (url, full_url), "get_full_url")
        return full_url

    def get_menu(self):
        log_to_file(
            "Fetching main menu for language: %s" %
            self.lang, "get_main_menu")
        return [
            {
                "title": "LANGUAGE",
                "url": self.MAIN_URL,
                "cat": "get_languages"
            }
        ]

    def get_main_menu(self):
        log_to_file(
            "Fetching main menu for language: %s" %
            self.lang, "get_main_menu")
        menu = self.get_menu()
        headers = {"User-Agent": client.agent(), "Referer": self.MAIN_URL}
        content = ensure_text(
            client.request(
                self.MAIN_URL,
                headers=headers),
            encoding='utf-8')

        if not content:
            log_to_file("Failed to load main page content.", "get_main_menu")
            return menu

        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="ignore")

        content = client.request(
            self.get_full_url(f"/{self.lang}.html"),
            headers=headers)
        if not content:
            log_to_file("Failed to load main page content.", "get_main_menu")
            return menu

        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="ignore")

        # Continenti
        continent_part = search(
            r'class="dropdown-menu mega-dropdown-menu"(.*?)<div class="collapse navbar',
            content,
            DOTALL)
        if continent_part:
            log_to_file("Extracting continents...", "get_main_menu")
            continents = findall(
                r'class="continent(.*?)(?=<div class="col|</div>)',
                continent_part.group(1),
                DOTALL)
            log_to_file(
                "Found continents: %d" %
                len(continents), "get_main_menu")
            for continent in continents:
                continent_name = search(r"<strong>(.*?)</strong>", continent)
                if continent_name:
                    continent_name = continent_name.group(1).strip()
                    links = findall(
                        r'<a href="([^"]+)"[^>]*>([^<]+)</a>', continent)
                    for url, name in links:
                        title = f"{continent_name}: {name.strip()}"
                        menu.append({
                            "title": title,
                            "url": self.get_full_url(url),
                            "cat": "list_cams"
                        })

            # Categorie
            categories = findall(
                r'<a href="([^"]+)"[^>]*>.*?class="tcam">([^<]+)<', content)
            log_to_file(
                "Found categories: %d" %
                len(categories), "get_main_menu")
            for url, name in categories:
                menu.append({
                    "title": f"Category: {name.strip()}",
                    "url": self.get_full_url(url),
                    "cat": "list_cams"
                })
        return menu

    def list_cams(self, url, cat_type):
        log_to_file("URL: %s" % url, "list_cams")
        log_to_file("Category type: %s" % cat_type, "list_cams")
        results = []

        headers = {"User-Agent": client.agent(), "Referer": self.MAIN_URL}
        content = client.request(url, headers=headers)
        if not content:
            log_to_file("Failed to fetch content.", "list_cams")
            return results

        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="ignore")

        if cat_type == "list_cams2":
            log_to_file("Parsing for NEW webcams...", "list_cams")
            pattern = r'<a href="(%s/webcam/[^"]+)"[^>]*>.*?<img src="([^"]+)"[^>]*alt="([^"]+)"' % self.lang
            matches = findall(pattern, content, DOTALL)
        else:
            log_to_file(
                "Parsing for CATEGORIES or TOP webcams...",
                "list_cams")
            pattern = r'<a href="([^"]+)"[^>]*>.*?<img src="([^"]+)"[^>]*alt="([^"]+)"'
            matches = findall(pattern, content, DOTALL)

        log_to_file("Found matches: %d" % len(matches), "list_cams")
        for url, icon, title in matches:
            if cat_type != "list_cams2" and "/webcam/" not in url:
                continue
            log_to_file(" + %s" % title.strip(), "list_cams")
            results.append({
                "title": title.strip(),
                "url": self.get_full_url(url),
                "icon": self.get_full_url(icon)
            })

        log_to_file(f"Found {len(results)} cams", "list_cams")
        return results

    def get_languages(self, url, cat_type):
        log_to_file("URL: %s" % url, "get_languages")
        log_to_file("Category type: %s" % cat_type, "get_languages")
        results = []

        headers = {"User-Agent": client.agent(), "Referer": self.MAIN_URL}
        content = client.request(url, headers=headers)
        if not content:
            log_to_file("Failed to fetch content.", "get_languages")
            return results

        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="ignore")

        pattern_block = r'<ul class="dropdown-menu">(.*?)</ul>'
        block = search(pattern_block, content, DOTALL)

        if not block:
            log_to_file("No language menu found.", "get_languages")
            return results

        pattern_lang = r'<a href="([^"]+\.html)"><img[^>]+class="ln_css ln-([^"]+)"[^>]+alt="([^"]+)"[^>]*>\s*([^<]+)</a>'
        matches = findall(pattern_lang, block.group(1), DOTALL)

        log_to_file("Found languages: %d" % len(matches), "get_languages")

        for href, code, alt, name in matches:
            log_to_file(" + %s [%s]" % (alt.strip(), code), "get_languages")
            results.append({
                "title": alt.strip(),
                "url": self.get_full_url(href)
            })

        return results

    def get_video_url(self, url):
        log_to_file("Fetching video URL for: %s" % url, "get_video_url")
        headers = {"User-Agent": client.agent(), "Referer": self.MAIN_URL}
        content = client.request(url, headers=headers)
        if not content:
            log_to_file("Failed to get content.", "get_video_url")
            return None

        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="ignore")

        hls_match = search(r"source:\s*'livee\.m3u8\?a=([^']+)'", content)
        if hls_match:
            video_id = hls_match.group(1)
            final_url = f"https://hd-auth.skylinewebcams.com/live.m3u8?a={video_id}"
            log_to_file("Found HLS: %s" % final_url, "get_video_url")
            return final_url

        yt_match = search(r"videoId:\s*'([^']+)'", content)
        if yt_match:
            video_id = yt_match.group(1)
            yt_url = f"https://www.youtube.com/watch?v=%s{video_id}"
            log_to_file("Found YouTube video: %s" % yt_url, "get_video_url")
            return yt_url

        log_to_file("No video URL found.", "get_video_url")
        return None

    def destroy(self):
        """Pulizia esplicita dell'oggetto"""
        log_to_file("Destroying SkylineWebcams", "SkylineWebcams")
        self.lang = None
        if hasattr(self, 'cams'):
            del self.cams
        if hasattr(self, 'items'):
            del self.items


class Webcam1(Screen):
    def __init__(self, session, lang=None):
        Screen.__init__(self, session)
        self.session = session

        disable_summary(self)

        self.lang = lang['code'] if lang else get_current_language()
        skin = os_path.join(worldcam_path, 'Webcam1.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()

        self.srefInit = self.session.nav.getCurrentlyPlayingServiceReference()
        self["webcam"] = webcamList([])
        self["info"] = Label('HOME VIEW')
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('Update')
        self['key_blue'] = Button('Remove')
        self['key_green'].hide()
        self.Update = False
        self['actions'] = ActionMap(
            [
                'OkCancelActions',
                'ColorActions',
            ],
            {
                "ok": self.okClicked,
                "cancel": self.cancel,
                "red": self.cancel,
                "green": self.okClicked,
                "yellow": self.update_me,
                "blue": self.removeb,
                # 'yellow_long': self.update_dev,
                # 'info_long': self.update_dev,
                # 'infolong': self.update_dev,
                # 'showEventInfoPlugin': self.update_dev
            },
            -1
        )
        self.timer = eTimer()
        if os_path.exists("/usr/bin/apt-get"):
            self.timer_conn = self.timer.timeout.connect(self.check_vers)
        else:
            self.timer.callback.append(self.check_vers)
        self.timer.start(500, 1)

        self.onFirstExecBegin.append(self.startup)
        self.onClose.append(lambda: safe_cleanup(self))

    def cleanup(self):
        log_to_file("Webcam1 cleanup", "Webcam1")
        if hasattr(self, 'timer'):
            self.timer.stop()
            self.timer = None

        if hasattr(self, 'names'):
            del self.names
        if hasattr(self, 'urls'):
            del self.urls

    def startup(self):
        log_to_file("Webcam1 startup", "Webcam1")
        self.names = [
            'User Lists',
            'Skyline Webcams',
            'Skyline Top',
            'Language']
        self.urls = [
            "http://worldcam.eu/",
            "https://www.skylinewebcams.com/",
            "https://www.skylinewebcams.com/%s/new-livecams.html" % self.lang,
            "https://www.skylinewebcams.com/%s/top-live-cams.html" % self.lang,
            # "https://www.skylinewebcams.com/",
            # "https://www.skylinewebcams.com/",
            # "https://www.skylinewebcams.com/",
        ]
        showlist(self.names, self['webcam'])

    def okClicked(self):
        idx = self['webcam'].getSelectionIndex()
        name = self.names[idx]
        log_to_file(f"Webcam1 okClicked idx={idx}, name={name}")

        if 'user' in name.lower():
            self.session.openWithCallback(self.onWebcam2Closed, Webcam2)
        elif 'webcams' in name.lower().replace(' ', ''):
            self.session.openWithCallback(self.onWebcam4Closed, Webcam4)
        elif 'top' in name.lower().replace(' ', ''):
            self.session.openWithCallback(self.onWebcam4Closed, Webcam4)
        elif 'language' in name.lower().replace(' ', ''):
            self.session.open(WebcamLanguage)

    def onWebcam2Closed(self, result=None):
        log_to_file("Returned from Webcam2 to Webcam1", "Webcam1")
        self.startup()

    def onWebcam4Closed(self, result=None):
        log_to_file("Returned from Webcam4 to Webcam1", "Webcam1")
        self.startup()

    def __onClose(self):
        """Handle cleanup when screen is closed"""
        if hasattr(self, 'timer'):
            self.timer.stop()
            self.timer = None
        try:
            if os_path.exists('/tmp/worldcam_debug.log'):
                remove('/tmp/worldcam_debug.log')
        except Exception as e:
            print(f"Error removing temp file: {e}")

    def check_vers(self):
        remote_version = '0.0'
        remote_changelog = ''
        try:
            req = Utils.Request(
                Utils.b64decoder(installer_url), headers={
                    'User-Agent': 'Mozilla/5.0'})
            page = Utils.urlopen(req).read()
            data = page.decode("utf-8") if PY3 else page.encode("utf-8")
            if data:
                lines = data.split("\n")
                for line in lines:
                    if line.startswith("version"):
                        remote_version = line.split(
                            "'")[1] if "'" in line else '0.0'
                    elif line.startswith("changelog"):
                        remote_changelog = line.split(
                            "'")[1] if "'" in line else ''
                        break
        except Exception as e:
            self.session.open(
                MessageBox, _('Error checking version: %s') %
                str(e), MessageBox.TYPE_ERROR, timeout=5)
            return
        self.new_version = remote_version
        self.new_changelog = remote_changelog
        if currversion < remote_version:
            self.Update = True
            self['key_green'].show()
            self.session.open(
                MessageBox,
                _('New version %s is available\n\nChangelog: %s\n\nPress info_long or yellow_long button to start force updating.') %
                (self.new_version,
                 self.new_changelog),
                MessageBox.TYPE_INFO,
                timeout=5)

    def update_me(self):
        if self.Update is True:
            self.session.openWithCallback(
                self.install_update,
                MessageBox,
                _("New version %s is available.\n\nChangelog: %s \n\nDo you want to install it now?") %
                (self.new_version,
                 self.new_changelog),
                MessageBox.TYPE_YESNO)
        else:
            self.session.open(
                MessageBox,
                _("Congrats! You already have the latest version..."),
                MessageBox.TYPE_INFO,
                timeout=4)

    def update_dev(self):
        try:
            req = Utils.Request(
                Utils.b64decoder(developer_url), headers={
                    'User-Agent': 'Mozilla/5.0'})
            page = Utils.urlopen(req).read()
            data = json.loads(page)
            remote_date = data['pushed_at']
            strp_remote_date = datetime.strptime(
                remote_date, '%Y-%m-%dT%H:%M:%SZ')
            remote_date = strp_remote_date.strftime('%Y-%m-%d')
            self.session.openWithCallback(
                self.install_update,
                MessageBox,
                _("Do you want to install update ( %s ) now?") %
                (remote_date),
                MessageBox.TYPE_YESNO)
        except Exception as e:
            print('error xcons:', e)

    def install_update(self, answer=False):
        if answer:
            cmd1 = 'wget -q "--no-check-certificate" ' + \
                Utils.b64decoder(installer_url) + ' -O - | /bin/sh'
            self.session.open(
                xConsole,
                'Upgrading...',
                cmdlist=[cmd1],
                finishedCallback=self.myCallback,
                closeOnSuccess=False)
        else:
            self.session.open(
                MessageBox,
                _("Update Aborted!"),
                MessageBox.TYPE_INFO,
                timeout=3)

    def myCallback(self, result=None):
        print('result:', result)
        return

    def removeb(self):
        conv = Webcam3(self.session, None)
        conv.removeb()

    def layoutFinished(self):
        self["paypal"].setText(paypal())
        self.setTitle(setup_title)

    def cancel(self):
        try:
            log_to_file("Cancel called, closing screen", "Webcam1")
            self.close()
        except Exception as e:
            log_to_file(f"Exception in cancel: {e}", "Webcam1")


class WebcamLanguage(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        disable_summary(self)

        skin = os_path.join(worldcam_path, 'Webcam1.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()

        self["webcam"] = webcamList([])
        self["info"] = Label(_('Select Language'))
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('')
        self['key_blue'] = Button('')
        self['key_yellow'].hide()
        self['key_blue'].hide()

        self['actions'] = ActionMap(
            ["OkCancelActions", "ColorActions"],
            {
                "ok": self.okClicked,
                "cancel": self.cancel,
                "red": self.cancel,
                "green": self.okClicked,
            },
            -1
        )

        self.onFirstExecBegin.append(self.startup)
        self.onClose.append(lambda: safe_cleanup(self))

    def cleanup(self):
        if hasattr(self, 'languages'):
            del self.languages

    def startup(self):
        self.languages = self.get_languages()
        names = [lang['name'] for lang in self.languages]
        showlist(names, self["webcam"])

    def get_languages(self):
        BASEURL = 'https://www.skylinewebcams.com/'
        headers = {'User-Agent': client.agent(), 'Referer': BASEURL}
        content = ensure_text(
            client.request(
                BASEURL,
                headers=headers),
            encoding='utf-8')

        languages = []
        # Extract available languages from HTML
        pattern_block = r'<ul class="dropdown-menu">(.*?)</ul>'
        block_match = search(pattern_block, content, DOTALL)

        if block_match:
            block = block_match.group(1)
            # Estrae ogni voce di lingua
            pattern_lang = r'<a href="/([a-z]{2})\.html"><img[^>]+class="ln_css ln-([a-z]{2})"[^>]+alt="([^"]+)"[^>]*>\s*([^<]+)</a>'
            matches = findall(pattern_lang, block, DOTALL)

            for href_code, class_code, alt_name, visible_name in matches:
                # Usa il mapping speciale per le bandiere delle lingue
                flag_code = language_flag_mapping.get(href_code, href_code)
                languages.append({
                    'code': href_code,
                    'name': visible_name.strip(),
                    'flag': flag_code,
                    'url': f'https://www.skylinewebcams.com/{href_code}.html'
                })

        # Lingue predefinite se non ne troviamo
        if not languages:
            default_langs = [
                {'code': 'en', 'name': 'English', 'flag': 'gb'},
                {'code': 'it', 'name': 'Italiano', 'flag': 'it'},
                {'code': 'de', 'name': 'Deutsch', 'flag': 'de'},
                {'code': 'es', 'name': 'Español', 'flag': 'es'},
                {'code': 'fr', 'name': 'Français', 'flag': 'fr'},
            ]
            languages = default_langs

        return languages

    def okClicked(self):
        idx = self["webcam"].getSelectionIndex()
        if 0 <= idx < len(self.languages):
            lang = self.languages[idx]
            set_current_language(lang['code'])
            self.session.open(Webcam4, lang)
            self.close()

    def cancel(self):
        self.close()


class Webcam2(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session

        disable_summary(self)

        skin = os_path.join(worldcam_path, 'Webcam1.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()

        self["webcam"] = webcamList([])
        self["info"] = Label('UserList')
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('')
        self['key_blue'] = Button('')
        self['key_yellow'].hide()
        self['key_blue'].hide()
        self['actions'] = ActionMap(
            [
                'OkCancelActions',
                'DirectionActions',
                'HotkeyActions',
                'InfobarEPGActions',
                'ChannelSelectBaseActions'
            ],
            {
                'ok': self.okClicked,
                'back': self.cancel,
                'cancel': self.cancel,
                'red': self.cancel,
                'green': self.okClicked,
            },
            -2
        )
        self.onFirstExecBegin.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)
        self.onClose.append(lambda: safe_cleanup(self))

    def close(self):
        return Screen.close(self)

    def layoutFinished(self):
        self["paypal"].setText(paypal())

    def openTest(self):
        log_to_file("Webcam2 openTest called")
        uLists = os_path.join(THISPLUG, 'Playlists')
        self.names = []
        for root, dirs, files in walk(uLists):
            for name in files:
                self.names.append(str(name))
        showlist(self.names, self["webcam"])

    def okClicked(self):
        idx = self["webcam"].getSelectionIndex()
        name = self.names[idx]
        log_to_file(f"Webcam2 okClicked idx={idx}, name={name}")
        self.session.open(Webcam3, name)

    def cancel(self):
        try:
            log_to_file("Cancel called, closing screen", "Webcam2")
            self.close()
        except Exception as e:
            log_to_file(f"Exception in cancel: {e}", "Webcam2")


class Webcam3(Screen):
    def __init__(self, session, name):
        Screen.__init__(self, session)
        self.session = session

        # Defensive fix against summary being a list
        disable_summary(self)

        skin = os_path.join(worldcam_path, "Webcam1.xml")
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()

        self.name = name
        self.xxxname = "/tmp/" + str(name) + "_conv.m3u"
        self.srefInit = self.session.nav.getCurrentlyPlayingServiceReference()
        self["webcam"] = webcamList([])
        self["info"] = Label("UserList")
        self["paypal"] = Label()
        self["key_red"] = Button("Exit")
        self["key_green"] = Button("Select")
        self["key_yellow"] = Button("Export")
        self["key_blue"] = Button("Remove")
        self['key_blue'].hide()
        self['actions'] = ActionMap(
            [
                'OkCancelActions',
                'DirectionActions',
                'HotkeyActions',
                'InfobarEPGActions',
                'ChannelSelectBaseActions'
            ],
            {
                'ok': self.okClicked,
                'back': self.cancel,
                'cancel': self.cancel,
                'red': self.cancel,
                "green": self.okClicked,
                "yellow": self.export,
                "blue": self.removeb,
            },
            -2
        )

        self.onFirstExecBegin.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)
        self.onClose.append(lambda: safe_cleanup(self))

    def close(self):
        try:
            if os_path.exists(self.xxxname):
                remove(self.xxxname)
        except Exception as e:
            print(f"Error removing temp file: {e}")
        return Screen.close(self)

    def layoutFinished(self):
        self["paypal"].setText(paypal())

    def export(self):
        log_to_file("export() called")
        # Creazione bouquet
        name_clean = Utils.cleanName(self.name)
        name_file = name_clean.replace(".m3u", "")
        bouquetname = f"userbouquet.wrd_{name_file.lower()}.tv"
        path1 = os_path.join(enigma_path, bouquetname)
        path2 = os_path.join(enigma_path, "bouquets.tv")
        tmplist = [
            "#NAME {} Worldcam by Lululla\n".format(
                name_file if name_file else bouquetname),
            f"#SERVICE 1:64:0:0:0:0:0:0:0:0::{name_file} CHANNELS",
            f"#DESCRIPTION --- {name_file} ---"]

        for idx in range(len(self.names)):
            title = self.names[idx]
            url = self.urls[idx]
            ref = url.replace(":", "%3a").replace("\\", "/")
            if "youtube" in url:
                ref = "streamlink://" + ref
            tmplist.append(f"#SERVICE 4097:0:1:0:0:0:0:0:0:0:{ref}")
            tmplist.append(f"#DESCRIPTION {title}")

        with open(path1, "w") as s:
            for item in tmplist:
                s.write(f"{item}\n")
        log_to_file(f"Bouquet file written: {path1}")

        bouquet_found = False
        if os_path.exists(path2):
            with open(path2, "r") as f:
                for line in f:
                    if bouquetname in line:
                        bouquet_found = True
                        break

        if not bouquet_found:
            with open(path2, "a") as f:
                f.write(
                    f'#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "{bouquetname}" ORDER BY bouquet\n')
            log_to_file(f"Appended to bouquets.tv: {bouquetname}")

        Utils.ReloadBouquets()
        self.session.open(
            MessageBox,
            _("Bouquet created successfully!"),
            MessageBox.TYPE_INFO,
            timeout=5)

    def openTest(self):
        log_to_file(f"openTest() reading playlist {self.name}")
        uLists = os_path.join(THISPLUG, "Playlists")
        file1 = os_path.join(uLists, self.name)
        self.names = []
        self.urls = []
        items = []
        try:
            with open(file1, "r", encoding="utf-8" if PY3 else None) as f1:
                for line in f1:
                    if "###" not in line:
                        continue
                    name_part, url = line.strip().split("###", 1)
                    name_clean = html_conv.html_unescape(
                        name_part.replace(".txt", ""))
                    self.names.append(name_clean)
                    self.urls.append(url)
                    items.append(f"{name_clean}###{url}\n")
            items.sort()
            with open(self.xxxname, "w") as e:
                for item in items:
                    e.write(item)
            log_to_file(
                f"Loaded {len(self.names)} entries, playlist converted to {self.xxxname}")
            showlist(self.names, self["webcam"])
        except Exception as e:
            log_to_file(f"Error in openTest: {e}")
            self.session.open(
                MessageBox,
                f"Error loading playlist: {e}",
                MessageBox.TYPE_ERROR)

    def okClicked(self):
        if not getattr(self, "names", []):
            log_to_file("okClicked() called but no names loaded")
            return
        idx = self["webcam"].getSelectionIndex()
        title = self.names[idx]
        video_url = self.urls[idx]
        log_to_file(f"okClicked() idx={idx}, title={title}, url={video_url}")
        stream = eServiceReference(4097, 0, video_url)
        stream.setName(str(title))
        self.session.open(MoviePlayer, stream)

    def removeb(self):
        log_to_file("removeb() called")
        self.session.openWithCallback(
            self.deleteBouquets,
            MessageBox,
            _("Remove all Worldcam Favorite Bouquet ?"),
            MessageBox.TYPE_YESNO,
            timeout=5,
            default=True)

    def deleteBouquets(self, result):
        log_to_file(f"deleteBouquets() result={result}")
        if result:
            try:
                for fname in listdir(enigma_path):
                    if "userbouquet.wrd_" in fname:
                        remove(os_path.join(enigma_path, fname))
                        log_to_file(f"Removed bouquet file: {fname}")
                orig = os_path.join(enigma_path, "bouquets.tv")
                bak = orig + ".bak"
                if os_path.exists(orig):
                    rename(orig, bak)
                    with open(bak, "r") as bakfile, open(orig, "w") as tvfile:
                        for line in bakfile:
                            if "userbouquet.wrd_" not in line:
                                tvfile.write(line)
                    log_to_file("Updated bouquets.tv from backup")
                Utils.ReloadBouquets()
                self.session.open(
                    MessageBox,
                    _('WorldCam Favorites List have been removed'),
                    MessageBox.TYPE_INFO,
                    timeout=5)
            except Exception as ex:
                log_to_file(f"Error in deleteBouquets: {ex}")
                self.session.open(
                    MessageBox,
                    f"Error removing bouquets: {ex}",
                    MessageBox.TYPE_ERROR)

    def cancel(self):
        try:
            log_to_file("Cancel called, closing screen", "Webcam3")
            self.close()
        except Exception as e:
            log_to_file(f"Exception in cancel: {e}", "Webcam3")


class Webcam4(Screen):
    def __init__(self, session, lang=None):
        Screen.__init__(self, session)
        self.session = session
        self.skinName = "Webcam4"
        disable_summary(self)

        skin = os_path.join(worldcam_path, 'Webcam1.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()

        self.lang = lang['code'] if lang else get_current_language()
        self.skyline = SkylineWebcams(self.lang)
        self['webcam'] = webcamList([])
        self['info'] = Label('Skyline Webcams')
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('')
        self['key_blue'] = Button('')
        self['key_yellow'].hide()
        self['key_blue'].hide()

        self['actions'] = ActionMap(
            ["OkCancelActions", "ColorActions"],
            {
                "ok": self.okClicked,
                "cancel": self.cancel,
                "red": self.cancel,
                "green": self.okClicked,
            },
            -1
        )

        self.onFirstExecBegin.append(self.startup)
        self.onClose.append(lambda: safe_cleanup(self))

    def startup(self):
        log_to_file(f"Webcam4 starting with language: {self.lang}", "Webcam4")
        self.names = []
        self.items = self.skyline.get_main_menu()
        for item in self.items:
            log_to_file(
                f"Menu item: {item['title']} - {item['url']}",
                "Webcam4")
            self.names.append(item['title'])
        showlist(self.names, self['webcam'])

    def cleanup(self):
        log_to_file("Webcam4 cleanup", "Webcam4")
        if hasattr(self, 'skyline'):
            self.skyline.destroy()
            self.skyline = None

        if hasattr(self, 'names'):
            del self.names
        if hasattr(self, 'items'):
            del self.items

    def okClicked(self):
        idx = self['webcam'].getSelectionIndex()
        if 0 <= idx < len(self.items):
            item = self.items[idx]
            log_to_file(f"Opening item: {item['title']}", "Webcam4")
            self.session.openWithCallback(
                self.onWebcam5ListClosed, Webcam5List, item)

    def onWebcam5ListClosed(self, result=None):
        log_to_file("Returned from Webcam5List to Webcam4", "Webcam4")
        self.startup()

    def layoutFinished(self):
        self["paypal"].setText(paypal())
        self.setTitle("Skyline Webcams")

    def openTest(self):
        log_to_file("openTest called", "Webcam4")
        self.names = []
        self.items = self.skyline.get_main_menu()
        for item in self.items:
            self.names.append(item['title'])
        showlist(self.names, self["webcam"])
        log_to_file(f"Loaded {len(self.names)} items in Webcam4", "Webcam4")

    def cancel(self):
        try:
            log_to_file("Cancel called, closing screen", "Webcam4")
            self.close()
        except Exception as e:
            log_to_file(f"Exception in cancel: {e}", "Webcam4")


class Webcam5List(Screen):
    def __init__(self, session, item):
        Screen.__init__(self, session)
        self.session = session

        disable_summary(self)

        skin = os_path.join(worldcam_path, 'Webcam1.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()

        self.skyline = SkylineWebcams()
        self.item = item
        self["webcam"] = webcamList([])
        self["info"] = Label(item['title'])
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('Export')
        self['key_blue'] = Button('Remove')
        self['actions'] = ActionMap(
            [
                'OkCancelActions',
                'DirectionActions',
                'HotkeyActions',
                'InfobarEPGActions',
                'ChannelSelectBaseActions'
            ],
            {
                'ok': self.okClicked,
                'back': self.cancel,
                'cancel': self.cancel,
                'red': self.cancel,
                'green': self.okClicked,
                'yellow': self.export,
                'blue': self.removeb,
            }, -2
        )
        self.onFirstExecBegin.append(self.startup)
        self.onClose.append(lambda: safe_cleanup(self))

    def cleanup(self):
        log_to_file("Webcam5List cleanup", "Webcam5List")
        # Distruggi esplicitamente gli oggetti
        if hasattr(self, 'skyline'):
            self.skyline.destroy()  # Ora il metodo esiste
            self.skyline = None

        if hasattr(self, 'cams'):
            del self.cams
        if hasattr(self, 'display_names'):
            del self.display_names
        if hasattr(self, 'item'):
            del self.item

    def startup(self):
        log_to_file("Webcam5List startup", "Webcam5List")
        self.names = []
        self.cams = self.skyline.list_cams(self.item['url'], self.item['cat'])

        log_to_file(
            f"Loaded {len(self.cams)} cameras for category: {self.item['title']}",
            "Webcam5List")

        self.display_names = []
        for cam in self.cams:
            # Try to extract country from URL
            country_code = None
            if "/webcam/" in cam['url']:
                parts = cam['url'].split("/")
                if len(parts) > 3:
                    country_code = parts[3].upper()
                    if country_code in country_codes.values():
                        cam['title'] += f" :{country_code}"

            self.display_names.append(cam['title'])

        showlist(self.display_names, self['webcam'])

    def close(self):
        return Screen.close(self)

    def layoutFinished(self):
        self["paypal"].setText(paypal())

    def removeb(self):
        self.session.openWithCallback(
            self.deleteBouquet,
            MessageBox,
            _("Remove this bouquet?"),
            MessageBox.TYPE_YESNO)

    def deleteBouquet(self, result):
        if result:
            name_clean = Utils.cleanName(self.item['title'])
            name_file = name_clean.replace('.m3u', '')
            bouquetname = f'userbouquet.wrd_{name_file.lower()}.tv'
            path1 = os_path.join(enigma_path, bouquetname)

            try:
                if os_path.exists(path1):
                    remove(path1)
                    log_to_file(f"Removed file: {path1}", "Webcam5List")

                path2 = os_path.join(enigma_path, 'bouquets.tv')
                if os_path.exists(path2):
                    bak_file = os_path.join(enigma_path, 'bouquets.tv.bak')
                    rename(path2, bak_file)
                    log_to_file(f"Created backup: {bak_file}", "Webcam5List")
                    with open(bak_file, 'r') as bakfile:
                        with open(path2, 'w') as tvfile:
                            for line in bakfile:
                                if bouquetname not in line:
                                    tvfile.write(line)

                Utils.ReloadBouquets()
                self.session.open(
                    MessageBox,
                    _('Bouquet removed successfully!'),
                    MessageBox.TYPE_INFO,
                    timeout=5)
            except Exception as e:
                log_to_file(f"Error removing bouquet: {str(e)}", "Webcam5List")
                self.session.open(
                    MessageBox,
                    f"Error removing bouquet: {str(e)}",
                    MessageBox.TYPE_ERROR)

    def openTest(self):
        self.names = []
        self.cams = self.skyline.list_cams(self.item['url'], self.item['cat'])
        log_to_file(
            f"Loaded {len(self.cams)} cameras for category: {self.item['title']}",
            "Webcam5List")

        # Create display names with country codes when available
        self.display_names = []
        for cam in self.cams:
            # Try to extract country from URL
            country_code = None
            if "/webcam/" in cam['url']:
                parts = cam['url'].split("/")
                if len(parts) > 3:
                    country_code = parts[3].upper()
                    if country_code in country_codes.values():
                        cam['title'] += f" :{country_code}"

            self.display_names.append(cam['title'])

        showlist(self.display_names, self["webcam"])

    def okClicked(self):
        idx = self["webcam"].getSelectionIndex()
        if 0 <= idx < len(self.cams):
            cam = self.cams[idx]
            log_to_file(
                f"Selected camera title: {cam['title']}",
                "Webcam5List")
            video_url = self.skyline.get_video_url(cam['url'])

            if video_url:
                log_to_file(f"Video URL: {video_url}", "Webcam5List")
                if 'youtube.com' in video_url:
                    self.play_youtube(video_url, cam['title'])
                else:
                    self.play_hls(video_url, cam['title'])
            else:
                log_to_file("Video URL not found", "Webcam5List")
                self.session.open(
                    MessageBox,
                    _('Video URL not found!'),
                    MessageBox.TYPE_ERROR)

    def play_hls(self, url, title):
        log_to_file(f"Playing HLS: {url} [{title}]", "Webcam5List")
        stream = eServiceReference(4097, 0, url)
        stream.setName(title)
        self.session.open(MoviePlayer, stream)

    def play_youtube(self, url, title):
        if os_path.exists(
                '/usr/lib/enigma2/python/Plugins/Extensions/YTDLWrapper'):
            url = 'streamlink://' + url
            stream = eServiceReference(4097, 0, url)
        else:
            try:
                from .youtube_dl import YoutubeDL
                ydl_opts = {'format': 'best'}
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if 'url' in info:
                        url = info['url']
                stream = eServiceReference(4097, 0, url)
            except Exception as e:
                log_to_file(f"YouTube-DL error: {e}", "Webcam5List")
                self.session.open(
                    MessageBox,
                    _('Error playing YouTube video!'),
                    MessageBox.TYPE_ERROR)
                return

        log_to_file(f"Playing YouTube stream: {url} [{title}]", "Webcam5List")
        stream.setName(title)
        self.session.open(MoviePlayer, stream)

    def export(self):
        name_clean = Utils.cleanName(self.item['title'])
        name_file = name_clean.replace('.m3u', '')
        bouquetname = f'userbouquet.wrd_{name_file.lower()}.tv'
        path1 = os_path.join(enigma_path, bouquetname)
        path2 = os_path.join(enigma_path, 'bouquets.tv')

        tmplist = [
            f'#NAME {name_file} Worldcam by Lululla',
            f'#SERVICE 1:64:0:0:0:0:0:0:0:0::{name_file} CHANNELS',
            f'#DESCRIPTION --- {name_file} ---'
        ]

        count_exported = 0
        for cam in self.cams:
            title = cam['title']
            video_url = self.skyline.get_video_url(cam['url'])
            if not video_url:
                continue

            ref = video_url.replace(":", "%3a").replace("\\", "/")
            if 'youtube' in video_url:
                ref = 'streamlink://' + ref

            tmplist.append(f'#SERVICE 4097:0:1:0:0:0:0:0:0:0:{ref}')
            tmplist.append(f'#DESCRIPTION {title}')
            count_exported += 1

        with open(path1, 'w') as s:
            for item in tmplist:
                s.write(f"{item}\n")
        log_to_file(
            f"Wrote bouquet to {path1} with {count_exported} items",
            "Webcam5List")

        bouquet_found = False
        if os_path.exists(path2):
            with open(path2, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if bouquetname in line:
                        bouquet_found = True
                        break

        if not bouquet_found:
            with open(path2, 'a') as f:
                f.write(
                    f'#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "{bouquetname}" ORDER BY bouquet\n')
            log_to_file(
                f"Appended new bouquet entry to bouquets.tv: {bouquetname}",
                "Webcam5List")

        Utils.ReloadBouquets()
        self.session.open(
            MessageBox,
            _('Bouquet created successfully!'),
            MessageBox.TYPE_INFO,
            timeout=5)

    def cancel(self):
        try:
            log_to_file("Cancel called, closing screen", "Webcam5List")
            self.close()
        except Exception as e:
            log_to_file(f"Exception in cancel: {e}", "Webcam5List")


class Webcam7(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session

        # Defensive fix against summary being a list
        disable_summary(self)

        skin = os_path.join(worldcam_path, 'Webcam1.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()

        self["webcam"] = webcamList([])
        self["info"] = Label('Skyline Top')
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('')
        self['key_blue'] = Button('')
        self['key_yellow'].hide()
        self['key_blue'].hide()
        self['actions'] = ActionMap(
            [
                'OkCancelActions',
                'DirectionActions',
                'HotkeyActions',
                'InfobarEPGActions',
                'ChannelSelectBaseActions'
            ],
            {
                'ok': self.okClicked,
                'back': self.cancel,
                'cancel': self.cancel,
                'red': self.cancel,
                'green': self.okClicked,
            },
            -2
        )
        self.onLayoutFinish.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)
        self.onClose.append(lambda: safe_cleanup(self))

    def close(self):
        return Screen.close(self)

    def layoutFinished(self):
        self["paypal"].setText(paypal())

    def openTest(self):
        self.names = []
        self.urls = []
        BASEURL = 'https://www.skylinewebcams.com/'
        headers = {'User-Agent': client.agent(), 'Referer': BASEURL}
        content = ensure_text(
            client.request(
                BASEURL,
                headers=headers),
            encoding='utf-8')

        n1 = content.find('dropdown-menu mega-dropdown-menu cat', 0)
        n2 = content.find('</div></div>', n1)

        if n1 == -1 or n2 == -1:
            log_to_file(
                "[Webcam7] HTML parsing error: dropdown menu block not found")
            return

        content2 = content[n1:n2]
        log_to_file("[Webcam7] Extracted content length: %d" % len(content2))

        regexvideo = 'href="(.+?)".*?tcam">(.+?)</p>'
        match = compile(regexvideo, DOTALL).findall(content2)
        log_to_file("[Webcam7] Found %d menu items" % len(match))

        for url, name in match:
            url1 = 'https://www.skylinewebcams.com' + url
            if not isinstance(name, unicode):
                name = Utils.getEncodedString(name)
            name = Utils.decodeHtml(name)
            self.names.append(name)
            self.urls.append(url1)
            log_to_file("[Webcam7] Added: %s -> %s" % (name, url1))

        showlist(self.names, self["webcam"])

    def okClicked(self):
        idx = self["webcam"].getSelectionIndex()
        if 0 <= idx < len(self.names):
            name = self.names[idx]
            url = self.urls[idx]
            log_to_file("[Webcam7] Selected: %s -> %s" % (name, url))
            self.session.open(Webcam8, name, url)
        else:
            log_to_file("[Webcam7] Invalid selection index: %d" % idx)

    def cancel(self):
        try:
            log_to_file("Cancel called, closing screen", "Webcam7")
            self.close()
        except Exception as e:
            log_to_file(f"Exception in cancel: {e}", "Webcam7")


class Webcam8(Screen):
    def __init__(self, session, name, url):
        Screen.__init__(self, session)
        self.session = session

        disable_summary(self)

        skin = os_path.join(worldcam_path, 'Webcam1.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()

        self.name = name
        self.url = url
        self.xxxname = '/tmp/' + str(name) + '_conv.m3u'
        self.srefInit = self.session.nav.getCurrentlyPlayingServiceReference()
        self["webcam"] = webcamList([])
        self["info"] = Label(name)
        self["paypal"] = Label()
        self['key_red'] = Button('Exit')
        self['key_green'] = Button('Select')
        self['key_yellow'] = Button('Export')
        self['key_blue'] = Button('Remove')
        self['actions'] = ActionMap(
            [
                'OkCancelActions',
                'DirectionActions',
                'HotkeyActions',
                'InfobarEPGActions',
                'ChannelSelectBaseActions'
            ],
            {
                'ok': self.okClicked,
                'back': self.cancel,
                'cancel': self.cancel,
                'red': self.cancel,
                'green': self.okClicked,
                'yellow': self.export,
                'blue': self.removeb,
            },
            -2
        )
        # self.onFirstExecBegin.append(self.openTest)
        self.onLayoutFinish.append(self.openTest)
        self.onLayoutFinish.append(self.layoutFinished)
        self.onClose.append(lambda: safe_cleanup(self))

    def close(self):
        try:
            if os_path.exists(self.xxxname):
                remove(self.xxxname)
        except Exception as e:
            print(f"Error removing temp file: {e}")
        return Screen.close(self)

    def layoutFinished(self):
        self["paypal"].setText(paypal())

    def removeb(self):
        self.session.openWithCallback(
            self.deleteBouquet,
            MessageBox,
            _("Remove this bouquet?"),
            MessageBox.TYPE_YESNO)

    def deleteBouquet(self, result):
        if result:
            log_to_file("Deleting bouquet for: {}".format(self.name))
            name_clean = Utils.cleanName(self.name)
            name_file = name_clean.replace('.m3u', '')
            bouquetname = f'userbouquet.wrd_{name_file.lower()}.tv'
            path1 = os_path.join(enigma_path, bouquetname)

            try:
                if os_path.exists(path1):
                    remove(path1)

                path2 = os_path.join(enigma_path, 'bouquets.tv')
                if os_path.exists(path2):
                    bak_file = os_path.join(enigma_path, 'bouquets.tv.bak')
                    rename(path2, bak_file)
                    with open(bak_file, 'r') as bakfile:
                        with open(path2, 'w') as tvfile:
                            for line in bakfile:
                                if bouquetname not in line:
                                    tvfile.write(line)

                Utils.ReloadBouquets()
                self.session.open(
                    MessageBox,
                    _('Bouquet removed successfully!'),
                    MessageBox.TYPE_INFO,
                    timeout=5)
            except Exception as e:
                self.session.open(
                    MessageBox,
                    f"Error removing bouquet: {str(e)}",
                    MessageBox.TYPE_ERROR)
                log_to_file("Error removing bouquet: {}".format(e))

    def export(self):
        log_to_file("Exporting bouquet for: {}".format(self.name))
        name_clean = Utils.cleanName(self.name)
        name_file = name_clean.replace('.m3u', '')
        bouquetname = f'userbouquet.wrd_{name_file.lower()}.tv'
        path1 = os_path.join(enigma_path, bouquetname)
        path2 = os_path.join(enigma_path, 'bouquets.tv')

        tmplist = []
        tmplist.append(f'#NAME {name_file} Worldcam by Lululla')
        tmplist.append(f'#SERVICE 1:64:0:0:0:0:0:0:0:0::{name_file} CHANNELS')
        tmplist.append(f'#DESCRIPTION --- {name_file} ---')

        for idx in range(len(self.names)):
            title = self.names[idx]
            url = self.urls[idx]
            video_url = self.get_video_url(url)
            if not video_url:
                continue

            ref = video_url.replace(":", "%3a").replace("\\", "/")
            if 'youtube' in video_url:
                ref = 'streamlink://' + ref

            tmplist.append(f'#SERVICE 4097:0:1:0:0:0:0:0:0:0:{ref}')
            tmplist.append(f'#DESCRIPTION {title}')

        with open(path1, 'w') as s:
            for item in tmplist:
                s.write(f"{item}\n")

        bouquet_found = False
        if os_path.exists(path2):
            with open(path2, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if bouquetname in line:
                        bouquet_found = True
                        break

        if not bouquet_found:
            with open(path2, 'a') as f:
                f.write(
                    f'#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "{bouquetname}" ORDER BY bouquet\n')

        Utils.ReloadBouquets()
        self.session.open(
            MessageBox,
            _('Bouquet created successfully!'),
            MessageBox.TYPE_INFO,
            timeout=5)

    def openTest(self):
        log_to_file("Opening test for: {}".format(self.name))
        self.names = []
        self.urls = []
        items = []
        BASEURL = 'https://www.skylinewebcams.com/{0}/webcam.html'
        from .lib import client, dom_parser as dom
        headers = {'User-Agent': client.agent(), 'Referer': BASEURL}
        content = ensure_text(
            client.request(
                self.url,
                headers=headers),
            encoding='utf-8')

        data = client.parseDOM(content, 'div', attrs={'class': 'container'})[0]
        data = dom.parse_dom(data, 'a', req='href')
        data = [i for i in data if 'subt' in i.content]

        for item in data:
            link = item.attrs['href']
            if link == '#':
                continue

            link = html_conv.html_unescape(link)
            name = html_conv.html_unescape(
                client.parseDOM(
                    item.content, 'img', ret='alt')[0])

            link = ensure_str(link)
            name = ensure_str(name)

            country_code = None
            if "/webcam/" in link:
                parts = link.split("/")
                if len(parts) > 3:
                    country_code = parts[3].upper()
                    if country_code in country_codes.values():
                        name += f" :{country_code}"

            url = 'https://www.skylinewebcams.com/{}'.format(link)
            items.append("{}###{}\n".format(name, url))

        items.sort()

        self.xxxname = '/tmp/{}_conv.m3u'.format(self.name)
        with open(self.xxxname, 'w', encoding='utf-8') as e:
            e.writelines(items)

        for item in items:
            name, url = item.split('###')
            name = Utils.decodeHtml(name)
            self.names.append(name)
            self.urls.append(url)

        showlist(self.names, self["webcam"])

    def okClicked(self):
        idx = self["webcam"].getSelectionIndex()
        url1 = self.urls[idx]
        name = self.names[idx]
        log_to_file("Selected: {} => {}".format(name, url1))
        self.getVid(name, url1)

    def get_video_url(self, url):
        headers = {'User-Agent': client.agent(), 'Referer': self.MAIN_URL}
        content = client.request(url, headers=headers)
        if not content:
            return None

        hls_match = search(r"source:\s*'livee\.m3u8\?a=([^']+)'", content)
        if hls_match:
            video_id = hls_match.group(1)
            return f"https://hd-auth.skylinewebcams.com/live.m3u8?a={video_id}"
        yt_match = search(r"videoId:\s*'([^']+)'", content)
        if yt_match:
            video_id = yt_match.group(1)
            return f"https://www.youtube.com/watch?v={video_id}"
        return None

    def getVid(self, name, url):
        try:
            video_url = self.get_video_url(url)
            log_to_file("Video URL: {}".format(video_url))
            if not video_url:
                return

            if 'm3u8' in video_url:
                stream = eServiceReference(4097, 0, video_url)
            elif 'youtube.com' in video_url:
                self.play_youtube(video_url, name)
            else:
                return

            stream.setName(str(name))
            self.session.open(MoviePlayer, stream)
        except Exception as e:
            log_to_file("Error in getVid: {}".format(e))
            self.session.open(
                MessageBox,
                f"Error playing video: {str(e)}",
                MessageBox.TYPE_ERROR)

    def play_youtube(self, url, title):
        try:
            if os_path.exists(
                    '/usr/lib/enigma2/python/Plugins/Extensions/YTDLWrapper'):
                url = 'streamlink://' + url
                stream = eServiceReference(4097, 0, url)
            else:
                from .youtube_dl import YoutubeDL
                ydl_opts = {'format': 'best'}
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if 'url' in info:
                        url = info['url']
                stream = eServiceReference(4097, 0, url)

            stream.setName(title)
            self.session.open(MoviePlayer, stream)
        except Exception as e:
            log_to_file("YouTube error: {}".format(e))
            self.session.open(
                MessageBox,
                _('Error playing YouTube video!'),
                MessageBox.TYPE_ERROR)

    def cancel(self):
        try:
            log_to_file("Cancel called, closing screen", "Webcam8")
            self.close()
        except Exception as e:
            log_to_file(f"Exception in cancel: {e}", "Webcam8")


class TvInfoBarShowHide():
    """ InfoBar show/hide control, accepts toggleShow and hide actions, might start
    fancy animations. """
    STATE_HIDDEN = 0
    STATE_HIDING = 1
    STATE_SHOWING = 2
    STATE_SHOWN = 3
    skipToggleShow = False

    def __init__(self):
        self["ShowHideActions"] = ActionMap(
            ["InfobarShowHideActions"], {
                "toggleShow": self.OkPressed, "hide": self.hide}, 0)
        self.__event_tracker = ServiceEventTracker(
            screen=self, eventmap={
                iPlayableService.evStart: self.serviceStarted})
        self.__state = self.STATE_SHOWN
        self.__locked = 0
        self.hideTimer = eTimer()
        try:
            self.hideTimer_conn = self.hideTimer.timeout.connect(
                self.doTimerHide)
        except BaseException:
            self.hideTimer.callback.append(self.doTimerHide)
        self.hideTimer.start(5000, True)
        self.onShow.append(self.__onShow)
        self.onHide.append(self.__onHide)

    def OkPressed(self):
        self.toggleShow()

    def __onShow(self):
        self.__state = self.STATE_SHOWN
        self.startHideTimer()

    def __onHide(self):
        self.__state = self.STATE_HIDDEN

    def serviceStarted(self):
        if self.execing:
            if config.usage.show_infobar_on_zap.value:
                self.doShow()

    def startHideTimer(self):
        if self.__state == self.STATE_SHOWN and not self.__locked:
            self.hideTimer.stop()
            idx = config.usage.infobar_timeout.index
            if idx:
                self.hideTimer.start(idx * 1500, True)

    def doShow(self):
        self.hideTimer.stop()
        self.show()
        self.startHideTimer()

    def doTimerHide(self):
        self.hideTimer.stop()
        if self.__state == self.STATE_SHOWN:
            self.hide()

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

    def lockShow(self):
        try:
            self.__locked += 1
        except BaseException:
            self.__locked = 0
        if self.execing:
            self.show()
            self.hideTimer.stop()
            self.skipToggleShow = False

    def unlockShow(self):
        try:
            self.__locked -= 1
        except BaseException:
            self.__locked = 0
        if self.__locked < 0:
            self.__locked = 0
        if self.execing:
            self.startHideTimer()

    def debug(self, obj, text=""):
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

    def __init__(self, session, stream):
        Screen.__init__(self, session)
        self.session = session
        self.skinName = "MoviePlayer"
        self.stream = stream
        self.state = self.STATE_PLAYING
        self.srefInit = self.session.nav.getCurrentlyPlayingServiceReference()
        for base_class in (
            InfoBarBase,
            InfoBarMenu,
            InfoBarSeek,
            InfoBarAudioSelection,
            InfoBarSubtitleSupport,
            InfoBarNotifications,
            TvInfoBarShowHide
        ):
            base_class.__init__(self)

        self['actions'] = ActionMap(
            [
                'MoviePlayerActions',
                'MovieSelectionActions',
                'MediaPlayerActions',
                'ColorActions',
                'OkCancelActions',
            ],
            {
                'leavePlayer': self.cancel,
                'stop': self.leavePlayer,
                'playpauseService': self.playpauseService,
                'cancel': self.cancel,
                'exit': self.leavePlayer,
                'yellow': self.cancel,
                'back': self.cancel,
            },
            -1
        )
        self.onFirstExecBegin.append(self.openPlay)
        self.onClose.append(self.cleanup)

    def openPlay(self):
        try:
            self.session.nav.stopService()
            self.session.nav.playService(self.stream)
        except Exception as e:
            log_to_file("Player error: {}".format(e))
            self.session.open(
                MessageBox,
                f"Player error: {str(e)}",
                MessageBox.TYPE_ERROR)

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

    def showAfterSeek(self):
        if isinstance(self, TvInfoBarShowHide):
            self.doShow()

    def leavePlayer(self):
        self.cancel()

    def cleanup(self):
        if os_path.exists('/tmp/hls.avi'):
            try:
                remove('/tmp/hls.avi')
            except BaseException:
                pass
        self.session.nav.stopService()
        if self.srefInit:
            self.session.nav.playService(self.srefInit)
        aspect_manager.restore_aspect()

    def cancel(self):
        self.close()


def main(session, **kwargs):
    try:
        session.open(Webcam1)
    except AttributeError as ae:
        import traceback
        traceback.print_exc()
        log_to_file("Main open error: {}".format(ae))


def Plugins(path, **kwargs):
    return [PluginDescriptor(
        name='WorldCam',
        description=f'Webcams from around the world V. {currversion}',
        where=PluginDescriptor.WHERE_PLUGINMENU,
        icon=os_path.join(path, 'plugin.png'),
        fnc=main
    )]
