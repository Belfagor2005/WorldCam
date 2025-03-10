#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
****************************************
*        coded by Lululla              *
*             08/03/2025               *
*       skin by MMark                  *
****************************************
Info http://t.me/tivustream
'''
# 03/06/2023 init
# ######################################################################
# Plugin Worldcam is developed by Linuxsat-Support Team                #
# edited and rewite by Lululla: updated to 20250308                    #
# ######################################################################
from __future__ import print_function

from . import _, paypal
from .lib import Utils
from .lib import html_conv
from .lib import client
from .lib.AspectManager import AspectManager
from .lib.Console import Console as xConsole

from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.config import config
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryPixmapAlphaTest, MultiContentEntryText
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from datetime import datetime
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
from os import walk, listdir, stat, system, remove, rename, path as os_path
from Plugins.Plugin import PluginDescriptor
from re import compile, DOTALL
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
from six import ensure_str, ensure_text
from sys import version_info
import codecs
import json
import ssl


global worldcam_path

currversion = '4.9'
setup_title = ('Worldcam V.' + currversion)
THISPLUG = '/usr/lib/enigma2/python/Plugins/Extensions/WorldCam'
ico_path1 = os_path.join(THISPLUG, 'pics/webcam.png')
iconpic = 'plugin.png'
enigma_path = '/etc/enigma2'
refer = 'https://www.skylinewebcams.com/'
json_path = os_path.join(THISPLUG, 'cowntry_code.json')
worldcam_path = os_path.join(THISPLUG, 'skin/hd/')
installer_url = 'aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0JlbGZhZ29yMjAwNS9Xb3JsZENhbS9tYWluL2luc3RhbGxlci5zaA=='
developer_url = 'aHR0cHM6Ly9hcGkuZ2l0aHViLmNvbS9yZXBvcy9CZWxmYWdvcjIwMDUvV29ybGRDYW0='
aspect_manager = AspectManager()

screen_width = getDesktop(0).size()
if screen_width.width() == 2560:
	worldcam_path = os_path.join(THISPLUG, 'skin/uhd')
elif screen_width.width() == 1920:
	worldcam_path = os_path.join(THISPLUG, 'skin/fhd')
else:
	worldcam_path = os_path.join(THISPLUG, 'skin/hd')


PY3 = version_info.major >= 3

if PY3:
	unicode = str
	unichr = chr
	long = int


if version_info >= (2, 7, 9):
	try:
		sslContext = ssl._create_unverified_context()

	except:
		sslContext = None


with open('/etc/enigma2/settings', 'r') as settings_file:
	for line in settings_file:
		if 'config.osd.language=' in line:
			language = line.split('=')[1].strip().replace('_', '-')
			break


def load_country_codes():
	with open(json_path, "r") as file:
		return json.load(file)


country_codes = load_country_codes()


class webcamList(MenuList):
	def __init__(self, items):
		"""
		Initialize the webcam list with appropriate font size and item height based on screen width.
		"""
		MenuList.__init__(self, items, True, eListboxPythonMultiContent)
		self.configureList()

	def configureList(self):
		"""
		Configure font size and item height based on the screen width.
		"""
		if screen_width == 2560:
			self.l.setFont(0, gFont('Regular', 44))
			self.l.setItemHeight(55)

		elif screen_width == 1920:
			self.l.setFont(0, gFont('Regular', 32))
			self.l.setItemHeight(50)
		else:
			self.l.setFont(0, gFont('Regular', 24))
			self.l.setItemHeight(45)


def wcListEntry(name, idx):
	"""
	Create an entry for the webcam list with text and icon based on screen width.
	:param name: Name of the webcam.
	:return: List representing the entry.
	"""
	res = [name]

	country_code = country_codes.get(name, None)
	print('Name - Cowntrycode=', name, country_code)
	if country_code:
		pngx = os_path.join(resolveFilename(SCOPE_CURRENT_SKIN, "countries/" + country_code + ".png"))
		if not os_path.isfile(pngx):
			pngx = os_path.join(pluginpath, "countries/" + country_code + ".png")
	else:
		pngx = ico_path1

	if not os_path.isfile(pngx):
		pngx = ico_path1

	if screen_width == 2560:
		res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(60, 50), png=loadPNG(pngx)))
		res.append(MultiContentEntryText(pos=(90, 0), size=(1200, 60), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
	elif screen_width == 1920:
		res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(50, 40), png=loadPNG(pngx)))
		res.append(MultiContentEntryText(pos=(80, 0), size=(950, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
	else:
		res.append(MultiContentEntryPixmapAlphaTest(pos=(3, 2), size=(50, 40), png=loadPNG(pngx)))
		res.append(MultiContentEntryText(pos=(70, 0), size=(500, 45), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
	return res


def showlist(data, list_widget):
	idx = 0
	plist = []
	for line in data:
		name = data[idx]
		plist.append(wcListEntry(name, idx))
		idx += 1
	list_widget.setList(plist)


def apListEntry(name, idx):

	res = [name]
	default_icon = os_path.join(resolveFilename(SCOPE_CURRENT_SKIN, "countries/missing.png"))

	icon_pos = (5, 5)
	icon_size = (50, 40)
	text_pos = (70, 0)
	text_size = (300, 100)

	country_code = country_codes.get(name, None)
	print('Name - Cowntrycode=', name, country_code)
	if country_code:
		pngx = os_path.join(resolveFilename(SCOPE_CURRENT_SKIN, "countries/" + country_code + ".png"))
		if not os_path.isfile(pngx):
			pngx = os_path.join(pluginpath, "countries/" + country_code + ".png")
	else:
		pngx = default_icon

	if not os_path.isfile(pngx):
		pngx = default_icon

	res.append(MultiContentEntryPixmapAlphaTest(pos=icon_pos, size=icon_size, png=loadPNG(pngx)))
	res.append(MultiContentEntryText(pos=text_pos, size=text_size, font=0, text=name, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))

	return res


def showlist2(data, list_widget):
	"""
	Populate the list widget with webcam entries.

	:param data: List of webcam names.
	:param list_widget: The MenuList widget to populate.
	"""
	idx = 0
	plist = []
	for line in data:
		name = data[idx]
		plist.append(apListEntry(name, idx))
		idx += 1
	list_widget.setList(plist)


class Webcam1(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		skin = os_path.join(worldcam_path, 'Webcam1.xml')
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
				'back': self.close,
				'cancel': self.close,
				'yellow': self.update_me,
				'green': self.okClicked,
				'blue': self.removeb,
				'yellow_long': self.update_dev,
				'info_long': self.update_dev,
				'infolong': self.update_dev,
				'showEventInfoPlugin': self.update_dev,
				'red': self.close
			},
			-1
		)
		self.timer = eTimer()
		if os_path.exists("/usr/bin/apt-get"):
			self.timer_conn = self.timer.timeout.connect(self.check_vers)
		else:
			self.timer.callback.append(self.check_vers)
		self.timer.start(500, 1)
		self.onFirstExecBegin.append(self.openTest)
		self.onLayoutFinish.append(self.layoutFinished)

	def check_vers(self):
		"""
		Check the latest version and changelog from the remote installer URL.
		If a new version is available, notify the user.
		"""
		remote_version = '0.0'
		remote_changelog = ''
		try:
			req = Utils.Request(Utils.b64decoder(installer_url), headers={'User-Agent': 'Mozilla/5.0'})
			page = Utils.urlopen(req).read()
			data = page.decode("utf-8") if PY3 else page.encode("utf-8")
			if data:
				lines = data.split("\n")
				for line in lines:
					if line.startswith("version"):
						remote_version = line.split("'")[1] if "'" in line else '0.0'
					elif line.startswith("changelog"):
						remote_changelog = line.split("'")[1] if "'" in line else ''
						break
		except Exception as e:
			self.session.open(MessageBox, _('Error checking version: %s') % str(e), MessageBox.TYPE_ERROR, timeout=5)
			return
		self.new_version = remote_version
		self.new_changelog = remote_changelog
		# if float(currversion) < float(remote_version):
		if currversion < remote_version:
			self.Update = True
			self['key_green'].show()
			self.session.open(
				MessageBox,
				_('New version %s is available\n\nChangelog: %s\n\nPress info_long or yellow_long button to start force updating.') % (self.new_version, self.new_changelog),
				MessageBox.TYPE_INFO,
				timeout=5
			)

	def update_me(self):
		if self.Update is True:
			self.session.openWithCallback(self.install_update, MessageBox, _("New version %s is available.\n\nChangelog: %s \n\nDo you want to install it now?") % (self.new_version, self.new_changelog), MessageBox.TYPE_YESNO)
		else:
			self.session.open(MessageBox, _("Congrats! You already have the latest version..."),  MessageBox.TYPE_INFO, timeout=4)

	def update_dev(self):
		"""
		Check for updates from the developer's URL and prompt the user to install the latest update.
		"""
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
		"""
		Populate the list with predefined names and URLs, and display them using the 'showlist' function.
		"""
		self.names = []
		self.urls = []

		predefined_entries = [
			('User Lists', 'http://worldcam.eu/'),
			('skylinewebcams', 'https://www.skylinewebcams.com/'),
			('skylinetop', 'https://www.skylinewebcams.com/')
		]

		for name, url in predefined_entries:
			self.names.append(name)
			self.urls.append(url)
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
		skin = os_path.join(worldcam_path, 'Webcam1.xml')
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
		self['actions'] = ActionMap(
			[
				'OkCancelActions',
				'ButtonSetupActions',
				'ColorActions'
			],
			{
				'red': self.close,
				'green': self.okClicked,
				'cancel': self.cancel,
				'back': self.cancel,
				'ok': self.okClicked
			},
			-2
		)
		self.onFirstExecBegin.append(self.openTest)
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		payp = paypal()
		self["paypal"].setText(payp)

	def openTest(self):
		uLists = os_path.join(THISPLUG, 'Playlists')
		self.names = []
		for root, dirs, files in walk(uLists):
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
		skin = os_path.join(worldcam_path, 'Webcam1.xml')
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
		self['actions'] = ActionMap(
			[
				'OkCancelActions',
				'ButtonSetupActions',
				'ColorActions'
			],
			{
				'red': self.close,
				'green': self.okClicked,
				'cancel': self.cancel,
				'yellow': self.export,
				'blue': self.removeb,
				'back': self.cancel,
				'ok': self.okClicked
			},
			-2
		)

		self.onFirstExecBegin.append(self.openTest)
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		payp = paypal()
		self["paypal"].setText(payp)

	def export(self):
		conv = Webcam6(self.session, self.name, None)
		conv.crea_bouquet()

	def openTest(self):
		uLists = os_path.join(THISPLUG, 'Playlists')
		file1 = os_path.join(uLists, self.name)
		self.names = []
		self.urls = []
		items = []
		f1 = ''
		if version_info[0] == 3:
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
			self.xxxname = os_path.join('/tmp', str(self.name) + '_conv.m3u')
			with open(self.xxxname, 'w') as e:
				for item in items:
					e.write(item)
			showlist(self.names, self['list'])
		except Exception as e:
			print("Error occurred:", e)

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
				for fname in listdir(enigma_path):
					if 'userbouquet.wrd_' in fname or 'bouquets.tv.bak' in fname:
						Utils.purge(enigma_path, fname)
				rename(os_path.join(enigma_path, 'bouquets.tv'), os_path.join(enigma_path, 'bouquets.tv.bak'))
				with open(os_path.join(enigma_path, 'bouquets.tv.bak'), 'r') as bakfile:
					with open(os_path.join(enigma_path, 'bouquets.tv'), 'w+') as tvfile:
						for line in bakfile:
							if '.wrd_' not in line:
								tvfile.write(line)
				self.session.open(MessageBox, _('WorldCam Favorites List have been removed'), MessageBox.TYPE_INFO, timeout=5)
				Utils.ReloadBouquets()
			except Exception as ex:
				print(str(ex))
				raise
		return


class Webcam4(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		skin = os_path.join(worldcam_path, 'Webcam1.xml')
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
		self['actions'] = ActionMap(
			[
				'OkCancelActions',
				'ButtonSetupActions',
				'ColorActions'],
			{
				'red': self.close,
				'green': self.okClicked,
				'cancel': self.cancel,
				'back': self.cancel,
				'ok': self.okClicked
			},
			-2
		)
		self.onFirstExecBegin.append(self.openTest)
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		payp = paypal()
		self["paypal"].setText(payp)

	def openTest(self):
		self.names = []
		self.urls = []
		BASEURL = 'https://www.skylinewebcams.com/'
		headers = {'User-Agent': client.agent(), 'Referer': BASEURL}
		content = ensure_text(client.request(BASEURL, headers=headers), encoding='utf-8')
		regexvideo = 'class="ln_css ln-(.+?)" alt="(.+?)"'
		match = compile(regexvideo, DOTALL).findall(content)
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
		skin = os_path.join(worldcam_path, 'Webcam1.xml')
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

		self['actions'] = ActionMap(
			[
				'OkCancelActions',
				'ButtonSetupActions',
				'ColorActions'
			],
			{
				'red': self.close,
				'green': self.okClicked,
				'cancel': self.cancel,
				'back': self.cancel,
				'ok': self.okClicked
			},
			-2
		)
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
		headers = {'User-Agent': client.agent(), 'Referer': BASEURL}
		content = ensure_text(client.request(self.url, headers=headers), encoding='utf-8')

		n1 = content.find('div class="dropdown-menu mega-dropdown-menu')
		n2 = content.find('div class="collapse navbar-collapse', n1)
		content2 = content[n1:n2]

		ctry = self.url.replace(BASEURL, "").replace(".html", "")
		regexvideo = '<a href="/' + ctry + '/webcam(.+?)">(.+?)</a>'
		match = compile(regexvideo, DOTALL).findall(content2)

		items = sorted(['{}###https://www.skylinewebcams.com/{}/webcam{}'.format(name, ctry, url) for url, name in match])

		for item in items:
			name, url1 = item.split('###')
			name = Utils.decodeHtml(Utils.getEncodedString(name) if not isinstance(name, unicode) else name)
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
		skin = os_path.join(worldcam_path, 'Webcam1.xml')
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
		self['actions'] = ActionMap(
			[
				'OkCancelActions',
				'ButtonSetupActions',
				'ColorActions'
			],
			{
				'red': self.close,
				'green': self.okClicked,
				'cancel': self.cancel,
				'back': self.cancel,
				'ok': self.okClicked
			},
			-2
		)
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
		headers = {'User-Agent': client.agent(), 'Referer': BASEURL}
		content = ensure_text(client.request(self.url, headers=headers), encoding='utf-8')

		n1 = content.find('col-xs-12"><h1>', 0)
		n2 = content.find('</div>', n1)
		content2 = content[n1:n2]

		ctry = self.url.replace('https://www.skylinewebcams.com/', '').replace('.html', '')

		regexvideo = '<a href="/' + ctry + '/(.+?)".*?tag">(.+?)</a>'
		match = compile(regexvideo, DOTALL).findall(content2)

		items = sorted(['{}###{}'.format(name, 'https://www.skylinewebcams.com/{}/{}'.format(ctry, url)) for url, name in match])

		for item in items:
			name, url1 = item.split('###')
			name = Utils.decodeHtml(Utils.getEncodedString(name) if not isinstance(name, str) else name)
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
		skin = os_path.join(worldcam_path, 'Webcam1.xml')
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
		self['actions'] = ActionMap(
			[
				'OkCancelActions',
				'ButtonSetupActions',
				'ColorActions'
			],
			{
				'red': self.close,
				'green': self.okClicked,
				'cancel': self.cancel,
				'yellow': self.crea_bouquet,
				'blue': self.removeb,
				'back': self.cancel,
				'ok': self.okClicked
			},
			-2
		)
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
		headers = {'User-Agent': client.agent(), 'Referer': BASEURL}
		content = ensure_text(client.request(self.url, headers=headers), encoding='utf-8')

		stext = self.url.replace(BASEURL, '').replace('.html', '') + '/'

		regexvideo = '><a href="' + stext + '(.+?)".*?alt="(.+?)"'
		match = compile(regexvideo, DOTALL).findall(content)

		items = []
		for url, name in match:
			url1 = '{}/{}{}'.format('https://www.skylinewebcams.com', stext, url)
			item = "{}###{}{}".format(name, url1, '\n')
			items.append(item)

		items.sort()

		self.xxxname = '/tmp/' + str(self.name) + '_conv.m3u'
		with open(self.xxxname, 'w', encoding='utf-8') as e:
			for item in items:
				e.write(item)

		for item in items:
			name, url1 = item.split('###')
			name = Utils.decodeHtml(Utils.getEncodedString(name) if not isinstance(name, str) else name)
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
			content = ensure_str(content)

			if "source:'livee.m3u8" in content:
				regexvideo = "source:'livee.m3u8(.+?)'"
				match = compile(regexvideo, DOTALL).findall(content)
				id = match[0].replace('?a=', '')
				if id:
					video_url = "https://hd-auth.skylinewebcams.com/live.m3u8?a={}".format(id)
					title = name
					stream = eServiceReference(4097, 0, video_url)
					stream.setName(str(title))
					self.session.open(MoviePlayer, stream)

			elif "videoId:" in content:
				regexvideo = "videoId.*?'(.*?)'"
				match = compile(regexvideo, DOTALL).findall(content)
				id = match[0]
				nid = len(str(id))
				print(nid)
				print('name: {0}\nid: {1}\nLenYTL: {2}'.format(str(name), str(id), nid))
				if str(nid) == '11':
					video_url = 'https://www.youtube.com/watch?v={}'.format(id)
					self.playYTID(video_url, str(name))

			else:
				return 'http://patbuweb.com/iptv/e2liste/startend.avi'

		except Exception as e:
			print("Error occurred:", e)

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
		stream = eServiceReference(4097, 0, video_url)
		if os_path.exists('/usr/lib/enigma2/python/Plugins/Extensions/YTDLWrapper/plugin.pyo') or os_path.exists('/usr/lib/enigma2/python/Plugins/Extensions/YTDLWrapper/plugin.pyc'):
			video_url = 'streamlink://' + video_url
		else:
			from .youtube_dl import YoutubeDL
			ydl_opts = {'format': 'best'}
			ydl = YoutubeDL(ydl_opts)
			ydl.add_default_info_extractors()
			result = ydl.extract_info(video_url, download=False)
			if result and hasattr(result, "url"):
				video_url = result['url']
				print("Here in Test url = %s" % video_url)

		stream = eServiceReference(4097, 0, video_url)
		stream.setName(str(yttitle))
		self.session.open(MoviePlayer, stream)

	def crea_bouquet(self, answer=None):
		if answer is None:
			self.session.openWithCallback(self.crea_bouquet, MessageBox, _("Do you want to Convert to Favorite Bouquet ?\n\nAttention!! Wait while converting !!!"))
		elif answer:
			if os_path.exists(self.xxxname) and stat(self.xxxname).st_size > 0:
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
					self.tmplist.append(servicez)
					self.tmplist.append(descriptionz)

				with open(path1, 'w+') as s:
					for item in self.tmplist:
						s.write("%s\n" % item)

				in_bouquets = 0
				for line in open('/etc/enigma2/bouquets.tv'):
					if bouquetname in line:
						in_bouquets = 1
				if in_bouquets == 0:
					with open(path2, 'a+') as f:
						bouquetTvString = '#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "%s" ORDER BY bouquet\n' % str(bouquetname)
						f.write(str(bouquetTvString))

				try:
					from enigma import eDVBDB
					eDVBDB.getInstance().reloadServicelist()
					eDVBDB.getInstance().reloadBouquets()
				except:
					eDVBDB = None
					system('wget -qO - http://127.0.0.1/web/servicelistreload?mode=2 > /dev/null 2>&1 &')

				message = self.session.open(MessageBox, _('bouquets reloaded..'), MessageBox.TYPE_INFO, timeout=5)
				message.setTitle(_("Reload Bouquet"))
			return

	def cancel(self):
		self.close()


class Webcam7(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		skin = os_path.join(worldcam_path, 'Webcam1.xml')
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
		self['actions'] = ActionMap(
			[
				'OkCancelActions',
				'ButtonSetupActions',
				'ColorActions'
			],
			{
				'red': self.close,
				'green': self.okClicked,
				'cancel': self.cancel,
				'back': self.cancel,
				'ok': self.okClicked
			},
			-2
		)
		self.onFirstExecBegin.append(self.openTest)
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		payp = paypal()
		self["paypal"].setText(payp)

	def openTest(self):
		self.names = []
		self.urls = []
		BASEURL = 'https://www.skylinewebcams.com/'
		headers = {'User-Agent': client.agent(), 'Referer': BASEURL}
		content = ensure_text(client.request(BASEURL, headers=headers), encoding='utf-8')

		n1 = content.find('dropdown-menu mega-dropdown-menu cat', 0)
		n2 = content.find('</div></div>', n1)

		content2 = content[n1:n2]
		regexvideo = 'href="(.+?)".*?tcam">(.+?)</p>'
		match = compile(regexvideo, DOTALL).findall(content2)

		for url, name in match:
			url1 = 'https://www.skylinewebcams.com' + url
			if not isinstance(name, unicode):
				name = Utils.getEncodedString(name)
			name = Utils.decodeHtml(name)
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
		self.session.open(Webcam8, name, url)

	def cancel(self):
		self.close()


class Webcam8(Screen):
	def __init__(self, session, name, url):
		Screen.__init__(self, session)
		self.session = session
		skin = os_path.join(worldcam_path, 'Webcam1.xml')
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
		self['actions'] = ActionMap(
			[
				'OkCancelActions',
				'ButtonSetupActions',
				'ColorActions'
			],
			{
				'red': self.close,
				'green': self.okClicked,
				'yellow': self.export,
				'blue': self.removeb,
				'cancel': self.cancel,
				'back': self.cancel,
				'ok': self.okClicked
			},
			-2
		)
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
		content = ensure_text(client.request(self.url, headers=headers), encoding='utf-8')

		data = client.parseDOM(content, 'div', attrs={'class': 'container'})[0]
		data = dom.parse_dom(data, 'a', req='href')
		data = [i for i in data if 'subt' in i.content]

		for item in data:
			link = item.attrs['href']
			if link == '#':
				continue

			link = html_conv.html_unescape(link)
			name = html_conv.html_unescape(client.parseDOM(item.content, 'img', ret='alt')[0])

			link = ensure_str(link)
			name = ensure_str(name)

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
				content = ensure_str(content)

			if "source:'livee.m3u8" in content:
				regexvideo = "source:'livee.m3u8(.+?)'"
				id = compile(regexvideo, DOTALL).findall(content)[0].replace('?a=', '')
				if id:
					video_url = "https://hd-auth.skylinewebcams.com/live.m3u8?a=" + id
					stream = eServiceReference(4097, 0, video_url)
					stream.setName(str(name))
					self.session.open(MoviePlayer, stream)

			elif "videoId:" in content:
				regexvideo = "videoId.*?'(.*?)'"
				id = compile(regexvideo, DOTALL).findall(content)[0]
				if len(id) == 11:
					video_url = 'https://www.youtube.com/watch?v=' + id
					self.playYTID(video_url, str(name))

			else:
				return 'http://patbuweb.com/iptv/e2liste/startend.avi'

		except Exception as e:
			print("Error occurred:", e)

	def getYTID(self, title, id):
		video_url = 'https://www.youtube.com/watch?v=' + id
		print('video_url: %s ' % (video_url))
		self.playYTID(video_url, title)

	def playYTID(self, video_url, yttitle):
		stream = eServiceReference(4097, 0, video_url)
		if os_path.exists('/usr/lib/enigma2/python/Plugins/Extensions/YTDLWrapper/plugin.pyo') or os_path.exists('/usr/lib/enigma2/python/Plugins/Extensions/YTDLWrapper/plugin.pyc'):
			video_url = 'streamlink://' + video_url
		else:
			from .youtube_dl import YoutubeDL
			ydl_opts = {'format': 'best'}
			ydl = YoutubeDL(ydl_opts)
			ydl.add_default_info_extractors()
			result = ydl.extract_info(video_url, download=False)
			if result and hasattr(result, "url"):
				video_url = result['url']
				print("Here in Test url = %s" % video_url)

		stream = eServiceReference(4097, 0, video_url)
		stream.setName(str(yttitle))
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
	screen_timeout = 5000

	def __init__(self, session, stream):
		Screen.__init__(self, session)
		self.session = session
		self.skinName = "MoviePlayer"
		self.service = None
		self.stream = stream
		self.state = self.STATE_PLAYING

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

		self.srefInit = self.session.nav.getCurrentlyPlayingServiceReference()

		self['actions'] = ActionMap(
			[
				'MoviePlayerActions',
				'MovieSelectionActions',
				'MediaPlayerActions',
				'EPGSelectActions',
				'MediaPlayerSeekActions',
				'ColorActions',
				'ButtonSetupActions',
				'OkCancelActions',
				'InfobarShowHideActions',
				'InfobarActions',
				'InfobarSeekActions'
			],
			{
				'leavePlayer': self.cancel,
				'stop': self.leavePlayer,
				'playpauseService': self.playpauseService,
				# 'red': self.cicleStreamType,
				'cancel': self.cancel,
				'exit': self.leavePlayer,
				'yellow': self.cancel,
				'back': self.cancel,
			},
			-1
		)
		self.onFirstExecBegin.append(self.openPlay)
		self.onClose.append(self.cancel)

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

	def showAfterSeek(self):
		if isinstance(self, TvInfoBarShowHide):
			self.doShow()

	def cancel(self):
		if os_path.exists('/tmp/hls.avi'):
			remove('/tmp/hls.avi')
		self.session.nav.stopService()
		self.session.nav.playService(self.srefInit)
		aspect_manager.restore_aspect()
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


def Plugins(path, **kwargs):
	global pluginpath
	pluginpath = path
	return [PluginDescriptor(
		name='WorldCam',
		description=f'Webcams from around the world V. {currversion}',
		where=PluginDescriptor.WHERE_PLUGINMENU,
		icon='plugin.png',
		fnc=main
	)]
