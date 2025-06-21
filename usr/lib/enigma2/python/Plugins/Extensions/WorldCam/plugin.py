#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

"""
#########################################################
#                                                       #
#  Worldcam Cam from Web Plugin                         #
#  Completely rewritten and optimized in version *5.0*  #
#  Version: 5.0                                         #
#  Created by Lululla (https://github.com/Belfagor2005) #
#  License: CC BY-NC-SA 4.0                             #
#  https://creativecommons.org/licenses/by-nc-sa/4.0    #
#  Last Modified: "10:10 - 20250606"                    #
#                                                       #
#  Credits:                                             #
#  - Original concept Lululla                           #
#  Usage of this code without proper attribution        #
#  is strictly prohibited.                              #
#  For modifications and redistribution,                #
#  please maintain this credit header.                  #
#########################################################
"""
__author__ = "Lululla"

# Standard library
import codecs
import tempfile
import zipfile
from os import makedirs
from os.path import abspath, dirname, exists, join, splitext
from shutil import copyfile, copyfileobj, rmtree

# Third-party libraries
import requests

# Enigma2 core
from enigma import (
	RT_HALIGN_LEFT,
	RT_VALIGN_CENTER,
	eListboxPythonMultiContent,
	eTimer,
	gFont,
	getDesktop,
	loadPNG,
)

# Enigma2 components
from Components.ActionMap import HelpableActionMap
from Components.Button import Button
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryPixmapAlphaTest, MultiContentEntryText
from Components.Pixmap import Pixmap

# Enigma2 screens
from Screens.ChoiceBox import ChoiceBox
from Screens.Console import Console
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

# Internal imports
from . import (
	_,
	AgentRequest,
	installer_url,
	paypal,
)
from .player import WorldCamPlayer
from .scraper import SkylineScraper
from .utils import (
	CATEGORY_ICONS,
	Logger,
	Request,
	b64decoder,
	disable_summary,
	get_category_icon,
	get_country_code,
	get_current_language,
	get_flag_path,
	get_system_language,
	language_flag_mapping,
	set_current_language,
	urlopen,
	FavoritesManager
)
# Python 3 compatibility fallback for unicode
try:
	unicode
except NameError:
	unicode = str


# Global constants
PLUGIN_VERSION = "5.3"
PLUGIN_PATH = dirname(__file__)
DEFAULT_ICON = join(PLUGIN_PATH, "pics/webcam.png")

# Initialize logger
logger = Logger()

# System language detection
language = "en"
current_language = get_system_language()
set_current_language(current_language)

# Screen resolution
screen_width = getDesktop(0).size().width()


class WebcamList(MenuList):

	def __init__(self, items):
		"""
		Initialize the webcam list with appropriate font size and item height based on screen width.
		"""
		MenuList.__init__(self, items, True, eListboxPythonMultiContent)
		self.currsel = -1
		self.currpos = 0
		if screen_width == 2560:
			self.l.setFont(0, gFont("Regular", 42))
			self.l.setItemHeight(60)
		elif screen_width == 1920:
			self.l.setFont(0, gFont("Regular", 36))
			self.l.setItemHeight(60)
		else:
			self.l.setFont(0, gFont("Regular", 24))
			self.l.setItemHeight(50)

	def getCurrentIndex(self):
		# Return the actual current index from the listbox instance
		return self.instance.getCurrentIndex()

	def getSelectionIndex(self):
		# Return the stored current selection
		return self.currsel

	def setCurrentIndex(self, idx):
		if idx < 0 or idx >= len(self.list):
			return
		self.currsel = idx
		self.currpos = idx
		self.instance.moveSelectionTo(idx)

	def setCurrentPosition(self, pos):
		self.currpos = pos
		self.instance.moveSelectionTo(pos)

	def getCurrentPosition(self):
		return self.currpos

	def destroy(self):
		self.lang = None
		if hasattr(self, "cams"):
			del self.cams
		if hasattr(self, "items"):
			del self.items


def wcListEntry(name, idx, is_category=False, is_country=False):
	"""
	Create an entry for the webcam list with text and icon based on screen width.
	:param name: Name of the webcam.
	:return: List representing the entry.
	"""
	res = [name]
	lname = name.lower()
	print("wcListEntry called with:", name, "is_category =", is_category)
	if is_category:
		if "youtube" in lname:
			pngx = get_category_icon("youtube.png")
		elif "hasbahca" in lname:
			pngx = get_category_icon("hasbahca.png")
		elif "userlist" in lname:
			pngx = get_category_icon("user_lists.png")
		elif "americas" in lname:
			pngx = get_category_icon("americas.png")
		elif "europe" in lname:
			pngx = get_category_icon("europe.png")
		elif "africa" in lname:
			pngx = get_category_icon("africa.png")
		elif "favorite" in lname:
			pngx = get_category_icon("favorite.png")
		else:
			"""
			for k, v in CATEGORY_ICONS.items():
				if lname == k.lower():
					pngx = get_category_icon(v)
					break
			"""
			for k, v in CATEGORY_ICONS.items():
				if k.lower() in lname.lower():
					pngx = get_category_icon(v)
					break
			else:
				pngx = DEFAULT_ICON
	else:
		country_code = get_country_code(name)
		pngx = get_flag_path(country_code) if country_code else DEFAULT_ICON

	if not exists(pngx):
		print("Icon file %s not found for name %s" % (pngx, name))
	print("Icon path:", pngx)

	if screen_width == 2560:
		res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(60, 50), png=loadPNG(pngx)))
		res.append(
			MultiContentEntryText(
				pos=(90, 0),
				size=(1200, 60),
				font=0,
				text=name,
				color=0xA6D1FE,
				flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
			)
		)
	elif screen_width == 1920:
		res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(70, 50), png=loadPNG(pngx)))
		res.append(
			MultiContentEntryText(
				pos=(100, 0),
				size=(950, 50),
				font=0,
				text=name,
				color=0xA6D1FE,
				flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
			)
		)
	else:
		res.append(MultiContentEntryPixmapAlphaTest(pos=(3, 2), size=(50, 40), png=loadPNG(pngx)))
		res.append(
			MultiContentEntryText(
				pos=(70, 0),
				size=(500, 45),
				font=0,
				text=name,
				color=0xA6D1FE,
				flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
			)
		)
	return res


def showlist(data, list_widget, is_category=False, is_country=False):
	plist = []
	for idx, name in enumerate(data):
		plist.append(wcListEntry(name, idx, is_category, is_country))

	try:
		list_widget.setList(plist)
	except Exception as e:
		if hasattr(list_widget, "l") and hasattr(list_widget.l, "setList"):
			list_widget.l.setList(plist)
		print("error showlist:", str(e))


class WebcamBaseScreen(Screen):
	"""Base class for all screens with integrated language management"""

	def __init__(self, session, lang=None):
		Screen.__init__(self, session)
		self.logger = Logger()
		self.logger.info("Initializing WebcamBaseScreen")
		self.session = session
		self.lang = lang if lang else get_current_language()
		self.skin_path = self.get_skin_path()
		self.skin = self.load_skin()

	def get_skin_path(self):
		if screen_width == 2560:
			return join(PLUGIN_PATH, "skin/uhd")
		elif screen_width == 1920:
			return join(PLUGIN_PATH, "skin/fhd")
		else:
			return join(PLUGIN_PATH, "skin/hd")

	def load_skin(self):
		# skin_file = self.__class__.__name__ + ".xml"
		skin_file = "WorldCamMainScreen.xml"
		skin_path = join(self.skin_path, skin_file)
		try:
			with codecs.open(skin_path, "r", encoding="utf-8") as f:
				return f.read()
		except Exception as e:
			self.logger.error("Skin loading error: %s" % str(e))
			return ""

	def set_flag_icon(self):
		"""Set the flag icon for the current language"""
		if "flag_icon" in self:
			try:
				flag_path = get_flag_path(self.lang)
				self.logger.info(f"Attempting to load flag from: {flag_path}")
				if exists(flag_path):
					self.logger.info("Flag file exists")
					pixmap = loadPNG(flag_path)
					if pixmap:
						self.logger.info("PNG loaded successfully")
						self["flag_icon"].instance.setPixmap(pixmap)
					else:
						self.logger.warning("Failed to load PNG")
				else:
					self.logger.warning("Flag file not found")
			except Exception as e:
				self.logger.error(f"Error setting flag icon: {str(e)}")

	def get_flag_icon(self):
		"""Return the flag icon path for the current language"""
		return get_flag_path(self.lang)


class WorldCamMainScreen(WebcamBaseScreen):
	"""
	Main screen for the WorldCam plugin displaying categories of webcams.
	"""

	def __init__(self, session, lang=None):
		super().__init__(session, lang)
		disable_summary(self)
		self.logger.info("Initializing WorldCamMainScreen")
		self["list"] = WebcamList([])
		self["flag_icon"] = Pixmap()
		self["language_label"] = Label(self.lang.upper())
		self["title"] = Label(_("WorldCam v{}").format(PLUGIN_VERSION))
		self["paypal"] = Label(paypal())
		self["key_red"] = Button(_("Exit"))
		self["key_green"] = Button(_("Select"))
		self["key_yellow"] = Button(_("Update"))
		self["key_blue"] = Button(_("Menu"))
		self.Update = False
		self.new_version = ""
		self.new_changelog = ""

		self.categories = [
			{"key": "user_lists", "name": _("User Lists"), "screen": WorldCamLocalScreen},
			{"key": "favorites", "name": _("Favorites"), "screen": WorldCamFavoritesScreen},
			{"key": "continents", "name": _("Continents"), "screen": WorldCamContinentScreen},
			{"key": "countries", "name": _("Countries"), "screen": WorldCamCountryScreen},
			{"key": "categories", "name": _("Categories"), "screen": WorldCamCategoryScreen},
			{"key": "top_webcams", "name": _("Top Webcams"), "screen": WorldCamTopScreen},
		]

		self["actions"] = HelpableActionMap(self, "WorldCamActions", {
			"ok": self.on_item_selected,
			"cancel": self.close,
			"red": self.close,
			"green": self.on_item_selected,
			"yellow": self.update_plugin,
			"blue": self.open_menu,
			"menu": self.open_menu,
			"about": self.open_about_direct
		})
		self.timer = eTimer()
		self.timer.callback.append(self.check_update_silent)
		self.timer.start(500, 1)
		self.onLayoutFinish.append(self.initialize)
		self.onLayoutFinish.append(self.set_flag_icon)

	def initialize(self):
		self.logger.info("Initializing UI elements in WorldCamMainScreen")
		try:
			category_names = [cat["name"] for cat in self.categories]
			showlist(category_names, self["list"], is_category=True)

			# Set initial selection and focus
			if category_names:
				self["list"].setCurrentIndex(0)
				self.setCurrentSelection(0)
		except Exception as e:
			self.logger.error("Error during initialize: %s" % str(e))

	def setCurrentSelection(self, index):
		"""Properly set the current selection in the list"""
		if index < 0 or index >= len(self["list"].list):
			return

		self["list"].setCurrentIndex(index)
		self["list"].instance.moveSelectionTo(index)
		self.currsel = index

	def on_item_selected(self):
		self.logger.info("Item selected in WorldCamMainScreen")
		try:
			# Get the actual current index from the list instance
			index = self["list"].getCurrentIndex()
			self.logger.info(f"Current index: {index}")

			if index is None or index < 0 or index >= len(self.categories):
				# Fallback to stored current selection
				index = getattr(self, "currsel", 0)
				self.logger.info(f"Using fallback index: {index}")

			if 0 <= index < len(self.categories):
				category = self.categories[index]
				self.logger.info(f"Opening screen for category: {category['name']}")
				self.session.open(category["screen"])
			else:
				self.logger.warning("Invalid selection index")
				self.logger.info(f"Index: {index}, Category count: {len(self.categories)}")
		except Exception as e:
			self.logger.error("Error in on_item_selected: %s" % str(e))

	def get_categories(self):
		self.logger.info("Retrieving categories for language: %s" % self.lang)
		categories = {
			"en": ["User Lists", "Favorites", "Continents", "Countries", "Categories", "Top Webcams"],
			"it": ["Liste Utente", "Preferiti", "Continenti", "Paesi", "Categorie", "Webcam Top"],
			"es": ["Listas de Usuario", "Favoritos", "Continentes", "Países", "Categorías", "Cámaras Top"],
			"de": ["Benutzerlisten", "Favoriten", "Kontinente", "Länder", "Kategorien", "Top-Webcams"],
			"fr": ["Listes Utilisateur", "Favoris", "Continents", "Pays", "Catégories", "Meilleures Webcams"],
			"pl": ["Listy użytkowników", "Ulubione", "Kontynenty", "Kraje", "Kategorie", "Najlepsze kamery"],
			"el": ["Λίστες χρηστών", "Αγαπημένα", "Ήπειροι", "Χώρες", "Κατηγορίες", "Κορυφαίες κάμερες"],
			"hr": ["Korisničke liste", "Favoriti", "Kontinenti", "Zemlje", "Kategorije", "Top web kamere"],
			"sl": ["Uporabniški seznami", "Priljubljene", "Celine", "Države", "Kategorije", "Vrhunske spletne kamere"],
			"ru": ["Пользовательские списки", "Избранное", "Континенты", "Страны", "Категории", "Лучшие веб-камеры"],
			"zh": ["用户列表", "收藏夹", "大洲", "国家", "类别", "热门摄像头"],
			"sq": ["Lista e përdoruesit", "Të preferuarat", "Kontinentet", "Vendet", "Kategoritë", "Kamerat më të mira"],
		}

		return categories.get(self.lang, categories["en"])

	def open_menu(self, result=None):
		self.logger.info("Opening menu")
		try:
			self.menu_items = [
				(_("Change language"), self.change_language),
				(_("Update plugin"), self.update_plugin),
				(_("Update yt-dlp"), self.update_yt_dlp_from_github),
				(_("Settings"), self.open_settings),
				(_("About"), self.open_about),
			]
			choices = [(label, index) for index, (label, _) in enumerate(self.menu_items)]

			self.current_menu = self.session.openWithCallback(
				self.menu_callback,
				ChoiceBox,
				title=_("Select an option"),
				list=choices
			)
		except Exception as e:
			self.logger.error("Error opening menu: %s" % str(e))

	def menu_callback(self, selection):
		try:
			if selection is not None:
				index = selection[1]
				label, callback = self.menu_items[index]
				self.logger.info("Selected menu item: %s" % label)
				if callable(callback):
					if hasattr(self, 'current_menu') and self.current_menu:
						self.current_menu.close()

					callback()
				else:
					self.logger.warning("Callback for '%s' is not callable" % label)
			else:
				self.logger.info("Menu cancelled")
		except Exception as e:
			self.logger.error("Exception during menu callback: %s" % str(e))

	def change_language(self):
		"""Opens the language selection screen"""
		try:
			from .LanguageScreen import LanguageScreen
			self.session.openWithCallback(
				self.on_language_selected,
				LanguageScreen,
				self.lang,
				language_flag_mapping
			)
		except Exception as e:
			self.logger.error(f"Error opening language screen: {str(e)}")
			import traceback
			self.logger.error(traceback.format_exc())
			self.show_message(_("Error opening language selection"), MessageBox.TYPE_ERROR)
			self.open_menu()

	def on_language_selected(self, new_lang):
		"""Manages the language selection result"""
		if new_lang is None:
			self.logger.info("Language selection cancelled")
			# self.open_menu()
			return

		self.logger.info(f"User selected language: {new_lang}")

		if new_lang == self.lang:
			self.logger.info("Selected language is same as current")
			# self.open_menu()
			return

		try:
			set_current_language(new_lang)
			self.lang = new_lang
			self.logger.info(f"New language set: {self.lang}")

			self.initialize()
			self["language_label"].setText(self.get_english_name(self.lang))
			self.set_flag_icon()

			self.logger.info(f"Language changed to {new_lang}")
			self.show_message(_("Language changed to %s") % self.get_english_name(new_lang), timeout=3)
		except Exception as e:
			self.logger.error(f"Error changing language: {str(e)}")
			self.show_message(_("Error changing language"), MessageBox.TYPE_ERROR)
		finally:
			# self.open_menu()
			pass

	def get_english_name(self, code):
		english_names = {
			"en": "English", "it": "Italian", "ar": "Arabic", "bg": "Bulgarian",
			"cs": "Czech", "de": "German", "el": "Greek", "es": "Spanish",
			"fa": "Persian", "fr": "French", "he": "Hebrew", "hr": "Croatian",
			"hu": "Hungarian", "ja": "Japanese", "ko": "Korean", "mk": "Macedonian",
			"nl": "Dutch", "pl": "Polish", "pt": "Portuguese", "ro": "Romanian",
			"ru": "Russian", "sk": "Slovak", "sl": "Slovenian", "sq": "Albanian",
			"sr": "Serbian", "th": "Thai", "tr": "Turkish", "vi": "Vietnamese",
			"zh": "Chinese"
		}
		return english_names.get(code, code.upper())

	def show_message(self, message, type=MessageBox.TYPE_INFO, timeout=0):
		self.session.openWithCallback(None, MessageBox, message, type, timeout=timeout)

	def open_settings(self):
		self.logger.info("Opening settings (placeholder)")
		try:
			# Placeholder for future Settings screen
			# Replace this block with: self.session.openWithCallback(self.settings_closed, SettingsScreen)
			self.defer_message(_("Settings functionality coming soon!"))
		except Exception as e:
			self.logger.error("Error in open_settings: %s" % str(e))
			self.defer_message(_("Error opening settings:\n%s") % str(e), MessageBox.TYPE_ERROR)
		finally:
			self.open_menu()

	def settings_closed(self, result=None):
		self.logger.info("Settings screen closed with result: %s" % str(result))
		# Optional: re-initialize plugin or refresh something here

	def check_update_silent(self):
		self.update_plugin(silent=True)

	def update_plugin(self, silent=False):
		remote_version = "0.0"
		remote_changelog = ""

		try:
			req = Request(b64decoder(installer_url), headers={"User-Agent": AgentRequest})
			page = urlopen(req).read().decode("utf-8")
		except Exception as e:
			if not silent:
				self.defer_message(_("Unable to fetch version info:\n{}").format(str(e)), MessageBox.TYPE_ERROR)
			return

		for line in page.split("\n"):
			line = line.strip()
			if line.startswith("version"):
				remote_version = line.split("=")[-1].strip().strip("'").strip('"')
			elif line.startswith("changelog"):
				remote_changelog = line.split("=")[-1].strip().strip("'").strip('"')
				break

		self.new_version = str(remote_version)
		self.new_changelog = str(remote_changelog)

		if PLUGIN_VERSION < self.new_version:
			self.ask_update()
		else:
			if not silent:
				self.defer_message(_("You are already running the latest version: {}").format(PLUGIN_VERSION), MessageBox.TYPE_INFO)

	def ask_update(self):
		def ask():
			self.session.openWithCallback(
				self.install_update,
				MessageBox,
				_("New version %s available\n\nChangelog: %s\n\nDo you want to install it now?") % (
					self.new_version, self.new_changelog),
				MessageBox.TYPE_YESNO
			)
		self._defer_timer = eTimer()
		self._defer_timer.callback.append(ask)
		self._defer_timer.start(100, True)

	def install_update(self, answer=False):
		if answer:
			try:
				self.session.open(
					Console,
					_("Upgrading..."),
					cmdlist=["wget -q --no-check-certificate " + b64decoder(installer_url) + " -O - | /bin/sh"],
					finishedCallback=self.myCallback,
					closeOnSuccess=False
				)
			except Exception as e:
				self.logger.error("Error starting update: %s" % str(e))
				self.defer_message(_("Update failed:\n%s") % str(e), MessageBox.TYPE_ERROR)
		else:
			self.defer_message(_("Update Aborted!"), MessageBox.TYPE_INFO)

	def myCallback(self, result=None):
		self.logger.info("Update finished with result: %s" % str(result))
		if result == 0:
			self.session.open(
				MessageBox,
				_("Update completed successfully!\n\nThe plugin will now close."),
				type=MessageBox.TYPE_INFO,
				timeout=4
			).addCallback(lambda _: self.close())
		else:
			self.defer_message(
				_("Update encountered an error (code: %s)") % str(result),
				MessageBox.TYPE_ERROR
			)

	def update_yt_dlp_from_github(self):
		"""
		Download and update only the 'yt_dlp' folder from the GitHub repository
		directly into the plugin folder, replacing the old one.
		"""
		self.logger.info("Starting yt-dlp update...")
		repo_zip_url = "https://github.com/yt-dlp/yt-dlp/archive/refs/heads/master.zip"
		try:
			tmp_dir = tempfile.mkdtemp(prefix="worldcam_yt_dlp_update_")
			zip_path = join(tmp_dir, "yt_dlp.zip")

			self.logger.info(f"Downloading yt-dlp from {repo_zip_url}")
			response = requests.get(repo_zip_url, stream=True, timeout=30)
			response.raise_for_status()
			with open(zip_path, "wb") as f:
				for chunk in response.iter_content(chunk_size=8192):
					f.write(chunk)

			with zipfile.ZipFile(zip_path, "r") as zip_ref:
				root_folder = zip_ref.namelist()[0].split("/")[0]
				self.logger.info(f"Extracting 'yt_dlp' folder from {root_folder}")

				plugin_folder = dirname(abspath(__file__))
				dest_yt_dlp_folder = join(plugin_folder, "yt_dlp")

				# Remove old yt_dlp folder if exists
				if exists(dest_yt_dlp_folder):
					self.logger.info("Removing old yt_dlp folder")
					rmtree(dest_yt_dlp_folder)

				# Extract only yt_dlp folder contents
				for member in zip_ref.namelist():
					if member.startswith(root_folder + "/yt_dlp/"):
						relative_path = member[len(root_folder) + 1:]
						target_path = join(plugin_folder, relative_path)
						if member.endswith("/"):
							makedirs(target_path, exist_ok=True)
						else:
							with zip_ref.open(member) as source, open(target_path, "wb") as target:
								copyfileobj(source, target)

			rmtree(tmp_dir)
			init_mod = join(PLUGIN_PATH, "__init__-mod-ytl-extractor.py")
			init_extract = join(PLUGIN_PATH, "yt_dlp/extractor/__init__.py")
			copyfile(init_mod, init_extract)
			self.logger.info("yt-dlp update completed successfully")
			self.defer_message(_("yt-dlp updated successfully!"), MessageBox.TYPE_INFO)

		except Exception as e:
			self.logger.error(f"Failed to update yt-dlp: {str(e)}")
			self.defer_message(_("Failed to update yt-dlp:\n%s") % str(e), MessageBox.TYPE_ERROR)

	def defer_message(self, text, mtype=MessageBox.TYPE_INFO):
		"""Show message with a short delay to avoid UI modal conflicts"""
		self._defer_timer = eTimer()
		self._defer_timer.callback.append(lambda: self.session.open(MessageBox, text, type=mtype))
		self._defer_timer.start(100, True)

	def get_about_text(self):
		"""Display information about the plugin with included playlists info"""
		about_text = _("WorldCam v%s") % PLUGIN_VERSION + "\n\n"
		about_text += _("Live webcam viewer featuring global locations.") + "\n\n"
		about_text += _("Developed by Lululla") + "\n\n"
		about_text += _("Powered by Enigma2 and Python") + "\n\n"
		about_text += _("GitHub: https://github.com/Belfagor2005/") + "\n"
		about_text += _("Forum support: www.corvoboys.org") + "\n\n"
		about_text += _("Included playlists and sources:\n")
		about_text += _("- Local webcam list\n")
		about_text += _("- Local YouTube playlist (test)\n")
		about_text += _("- Online webcam list\n")
		about_text += _("- Online Direct and YouTube webcams playlist (test)\n")
		about_text += _("- Other sources\n")
		return about_text

	def open_about(self):
		self.session.openWithCallback(self.open_menu, MessageBox, self.get_about_text(), MessageBox.TYPE_INFO)

	def open_about_direct(self):
		self.session.open(MessageBox, self.get_about_text(), MessageBox.TYPE_INFO)


class WorldCamFavoritesScreen(WebcamBaseScreen):
	def __init__(self, session, lang=None):
		super().__init__(session, lang)
		disable_summary(self)
		self.logger.info("Initializing WorldCamFavoritesScreen")
		self["title"] = Label(_("Your Favorites"))
		self["list"] = WebcamList([])
		self["flag_icon"] = Pixmap()
		self["language_label"] = Label(self.lang.upper())
		self["paypal"] = Label(paypal())
		self["key_red"] = Button(_("Exit"))
		self["key_green"] = Button(_("Play"))
		self["key_yellow"] = Button(_("Remove"))
		self["key_blue"] = Button()

		self["actions"] = HelpableActionMap(self, "WorldCamActions", {
			"ok": self.on_item_selected,
			"cancel": self.close,
			"red": self.close,
			"green": self.on_item_selected,
			"yellow": self.remove_favorite,
		})

		self.onLayoutFinish.append(self.load_favorites)
		self.onLayoutFinish.append(self.set_flag_icon)

	def load_favorites(self):
		"""Carica e mostra i preferiti"""
		try:
			self.favorites = FavoritesManager.load_favorites()
			if not self.favorites:
				self["title"].setText(_("No favorites yet"))
				self["key_yellow"].setText("")
				return

			webcam_names = [fav["name"] for fav in self.favorites]
			showlist(webcam_names, self["list"], is_category=True)
			self["list"].setCurrentIndex(0)
			self["key_yellow"].setText(_("Remove"))
		except Exception as e:
			self.logger.error("Error loading favorites: %s" % str(e))
			self["title"].setText(_("Error loading favorites"))

	def on_item_selected(self):
		"""Riproduce il webcam selezionato"""
		index = self["list"].getCurrentIndex()
		if index is None or index < 0 or index >= len(self.favorites):
			return

		webcam = self.favorites[index]
		self.session.open(WorldCamPlayer, webcam["name"], webcam["url"])

	def remove_favorite(self):
		"""Rimuove il webcam selezionato dai preferiti"""
		index = self["list"].getCurrentIndex()
		if index is None or index < 0 or index >= len(self.favorites):
			return

		webcam = self.favorites[index]
		if FavoritesManager.remove_favorite(webcam["url"]):
			# Ricarica la lista
			self.load_favorites()
			self.session.open(
				MessageBox,
				_("Removed from favorites: %s") % webcam["name"],
				MessageBox.TYPE_INFO,
				timeout=3
			)


class WorldCamLocalScreen(WebcamBaseScreen):
	"""
	Screen to display and select user playlists.
	"""

	def __init__(self, session, lang=None):
		super().__init__(session, lang)
		disable_summary(self)
		self.logger.info("Initializing WorldCamLocalScreen")
		self.scraper = SkylineScraper(lang if lang else "en")
		self["title"] = Label(_("User Lists"))
		self["list"] = WebcamList([])
		self["flag_icon"] = Pixmap()
		self["language_label"] = Label(self.lang.upper())
		self["paypal"] = Label(paypal())
		self["key_red"] = Button(_("Exit"))
		self["key_green"] = Button()
		self["key_yellow"] = Button()
		self["key_blue"] = Button()
		self["actions"] = HelpableActionMap(self, "WorldCamActions", {
			"ok": self.on_item_selected,
			"cancel": self.close,
		})
		self.onLayoutFinish.append(self.load_user_lists)
		self.onLayoutFinish.append(self.set_flag_icon)

	def load_user_lists(self):
		"""Load user playlists from the playlists directory."""
		try:
			playlists_path = join(PLUGIN_PATH, "Playlists")
			self.logger.info("Loading user playlists from: %s" % playlists_path)
			self.user_lists = self.scraper.get_local_playlists(playlists_path)

			if not exists(playlists_path):
				try:
					makedirs(playlists_path)
					self.logger.info(f"Created playlists directory: {playlists_path}")
				except Exception as e:
					self.logger.error(f"Error creating directory: {str(e)}")

			if not self.user_lists:
				self.logger.warning("No user playlists found.")
				self["title"].setText(_("No playlists found"))
				return

			# Remove file extensions from playlist names before showing
			clean_lists = [splitext(name)[0] for name in self.user_lists]

			showlist(clean_lists, self["list"], is_category=True)

			# Set initial selection
			if clean_lists:
				self["list"].setCurrentIndex(0)

		except Exception as e:
			self.logger.error("Error loading user playlists: %s" % str(e))
			self["title"].setText(_("Error loading playlists"))

	def on_item_selected(self):
		"""Open the selected user playlist or show an error if invalid."""
		try:
			idx = self["list"].getCurrentIndex()
			self.logger.info("Selected playlist index: %d" % idx)

			if not self.user_lists:
				self.logger.warning("No playlists available")
				self["title"].setText(_("No playlists available"))
				return

			if idx < 0 or idx >= len(self.user_lists):
				self.logger.warning("Invalid selection index: %d" % idx)
				self["title"].setText(_("Select a valid playlist"))
				return

			playlists = self.user_lists[idx]
			self.logger.info("Opening user playlist: %s" % playlists)
			self.session.open(WorldCamLocal, playlists)
		except Exception as e:
			self.logger.error("Error on item selected: %s" % str(e))
			self["title"].setText(_("Error opening playlist"))


class WorldCamLocal(WebcamBaseScreen):
	"""
	Screen to display and select webcams from a user playlist file.
	"""

	def __init__(self, session, playlists, lang=None):
		super().__init__(session, lang)
		disable_summary(self)
		self.logger.info("Initializing WorldCamLocal with category: %s" % playlists)
		self.category = playlists
		self.scraper = SkylineScraper(lang if lang else "en")
		self["title"] = Label(splitext(playlists)[0])
		self["list"] = WebcamList([])
		self["flag_icon"] = Pixmap()
		self["language_label"] = Label(self.lang.upper())
		self["paypal"] = Label(paypal())
		self["key_red"] = Button(_("Exit"))
		self["key_green"] = Button()
		self["key_yellow"] = Button()
		self["key_blue"] = Button()
		self["actions"] = HelpableActionMap(self, "WorldCamActions", {
			"ok": self.on_item_selected,
			"cancel": self.close,
		})
		self.onLayoutFinish.append(self.load_webcams)
		self.onLayoutFinish.append(self.set_flag_icon)

	def load_webcams(self):
		path = join(PLUGIN_PATH, "Playlists", self.category)
		self.webcams = []
		try:
			self.logger.info("Loading webcams from playlist file: %s" % path)
			self.webcams = self.scraper.parse_local_playlist_file(path)
			if not self.webcams:
				self.logger.warning("Playlist file not found or empty: %s" % path)
				self["title"].setText(_("Playlist file not found or empty"))
			else:
				showlist([w["name"] for w in self.webcams], self["list"], is_category=True)
				self["list"].setCurrentIndex(0)
		except FileNotFoundError:
			self.logger.error("Playlist file not found: %s" % path)
			self["title"].setText(_("Playlist file not found"))
		except Exception as e:
			self.logger.error("Error loading playlist: %s" % str(e))
			self["title"].setText(_("Error loading playlist"))

	def on_item_selected(self):
		"""Handle selection of a webcam and open the player."""
		index = self["list"].getCurrentIndex()
		if index is None or index < 0 or index >= len(self.webcams):
			self.logger.warning("Invalid webcam selection index: %s" % str(index))
			self["title"].setText(_("Select a valid webcam"))
			return

		webcam = self.webcams[index]
		self.logger.info("Selected webcam: %s URL: %s" % (webcam["name"], webcam["url"]))
		self.session.open(WorldCamPlayer, webcam["name"], webcam["url"])


class WorldCamContinentScreen(WebcamBaseScreen):
	"""Screen to display continents"""
	def __init__(self, session, lang=None):
		super().__init__(session, lang)
		disable_summary(self)
		self.logger.info("Initializing WorldCamContinentScreen")
		self.scraper = SkylineScraper(lang if lang else "en")
		self["title"] = Label(_("Continents"))
		self["list"] = WebcamList([])
		self["flag_icon"] = Pixmap()
		self["language_label"] = Label(self.lang.upper())
		self["paypal"] = Label(paypal())
		self["key_red"] = Button(_("Exit"))
		self["key_green"] = Button()
		self["key_yellow"] = Button()
		self["key_blue"] = Button()
		self["actions"] = HelpableActionMap(self, "WorldCamActions", {
			"ok": self.on_item_selected,
			"cancel": self.close,
		})
		self.continents = []
		self.onLayoutFinish.append(self.load_continents)
		self.onLayoutFinish.append(self.set_flag_icon)

	def load_continents(self):
		"""Load continents from scraper"""
		try:
			self.continents = self.scraper.get_continents()
			continent_names = [continent["name"] for continent in self.continents]
			self.logger.info(f"Loaded {len(continent_names)} continents")
			if continent_names:
				showlist(continent_names, self["list"], is_category=True)
				self["list"].setCurrentIndex(0)

		except Exception as e:
			self.logger.error("Error loading continents: " + str(e))
			self["title"].setText(_("Error loading continents"))

	def on_item_selected(self):
		"""Handle continent selection"""
		index = self["list"].getCurrentIndex()
		if index is None or index < 0 or index >= len(self.continents):
			self.logger.warning("Invalid continent selection index")
			return
		continent = self.continents[index]
		self.logger.info(f"Selected continent: {continent['name']}")
		self.session.open(WorldCamContinentCountryScreen, continent)


class WorldCamContinentCountryScreen(WebcamBaseScreen):
	"""Screen to display countries within a continent"""
	def __init__(self, session, continent, lang=None):
		super().__init__(session, lang)
		disable_summary(self)
		self.logger.info(f"Initializing WorldCamContinentCountryScreen for {continent['name']}")
		self.continent = continent
		# self.scraper = SkylineScraper(lang if lang else "en")
		self["title"] = Label(continent["name"])
		self["list"] = WebcamList([])
		self["flag_icon"] = Pixmap()
		self["language_label"] = Label(self.lang.upper())
		self["paypal"] = Label(paypal())
		self["key_red"] = Button(_("Exit"))
		self["key_green"] = Button()
		self["key_yellow"] = Button()
		self["key_blue"] = Button()
		self["actions"] = HelpableActionMap(self, "WorldCamActions", {
			"ok": self.on_item_selected,
			"cancel": self.close,
		})
		self.countries = []
		self.onLayoutFinish.append(self.load_countries)
		self.onLayoutFinish.append(self.set_flag_icon)

	def load_countries(self):
		try:
			countries = self.continent["countries"]
			self.countries = sorted(countries, key=lambda c: c["name"].lower())
			country_names = [country["name"] for country in self.countries]
			self.logger.info(f"Loaded {len(country_names)} countries for {self.continent['name']}")
			if country_names:
				showlist(country_names, self["list"], is_country=True)
				self["list"].setCurrentIndex(0)
		except Exception as e:
			self.logger.error(f"Error loading countries: {str(e)}")
			self["title"].setText(_("Error loading countries"))

	def on_item_selected(self):
		"""Handle country selection"""
		index = self["list"].getCurrentIndex()
		if index is None or index < 0 or index >= len(self.countries):
			return

		country = self.countries[index]
		self.logger.info(f"Selected country: {country['name']}")
		self.session.open(WorldCamLocationScreen, country)


class WorldCamCountryScreen(WebcamBaseScreen):
	"""
	Screen to display and select countries from which webcams are available.
	"""

	def __init__(self, session, category=None, lang=None):
		super().__init__(session, lang)
		disable_summary(self)
		self.logger.info("Initializing WorldCamCountryScreen")
		self.scraper = SkylineScraper(lang if lang else "en")
		self["title"] = Label(_("Country"))  # Fixed typo
		self["list"] = WebcamList([])
		self["flag_icon"] = Pixmap()
		self["language_label"] = Label(self.lang.upper())
		self["paypal"] = Label(paypal())
		self["key_red"] = Button(_("Exit"))
		self["key_green"] = Button()
		self["key_yellow"] = Button()
		self["key_blue"] = Button()
		self["actions"] = HelpableActionMap(self, "WorldCamActions", {
			"ok": self.on_item_selected,
			"cancel": self.close,
		})
		self.onLayoutFinish.append(self.load_countries)
		self.onLayoutFinish.append(self.set_flag_icon)

	def load_countries(self):
		"""Load and sort countries from scraper, then show in list."""
		try:
			countries = self.scraper.get_countries()
			self.countries = sorted(countries, key=lambda c: c["name"].lower())
			country_names = [country["name"] for country in self.countries]
			self.logger.info("Loaded and sorted countries: %s" % country_names)
			if country_names:
				showlist(country_names, self["list"])
				self["list"].setCurrentIndex(0)
		except Exception as e:
			self.logger.error("Error loading countries: %s" % str(e))
			self["title"].setText(_("Error loading countries"))

	def on_item_selected(self):
		"""Handle country selection and open corresponding location screen."""
		index = self["list"].getCurrentIndex()
		self.logger.info("Selected country index: %s" % str(index))

		if index is None or index < 0 or index >= len(self.countries):
			self.logger.warning("Invalid country selection index: %s" % str(index))
			return

		country = self.countries[index]
		self.logger.info("Selected country: %s" % country)
		self.session.open(WorldCamLocationScreen, country)


class WorldCamCategoryScreen(WebcamBaseScreen):
	"""
	Screen to display categories of webcams.
	"""

	def __init__(self, session, lang=None):
		super().__init__(session, lang)
		disable_summary(self)
		self.logger.info("Initializing WorldCamCategoryScreen")
		self.scraper = SkylineScraper(lang if lang else "en")
		self["title"] = Label(_("Categories"))
		self["list"] = WebcamList([])
		self["flag_icon"] = Pixmap()
		self["paypal"] = Label(paypal())
		self["language_label"] = Label(self.lang.upper())
		self["key_red"] = Button(_("Exit"))
		self["key_green"] = Button()
		self["key_yellow"] = Button()
		self["key_blue"] = Button()
		self["actions"] = HelpableActionMap(self, "WorldCamActions", {
			"ok": self.on_item_selected,
			"cancel": self.close,
		})
		self.categories = []
		self.onLayoutFinish.append(self.load_categories)
		self.onLayoutFinish.append(self.set_flag_icon)

	def load_categories(self):
		"""Load categories from scraper and display them sorted."""
		try:
			categories = self.scraper.get_categories()
			self.categories = sorted(categories, key=lambda c: c["name"].lower())
			category_names = [cat["name"] for cat in self.categories]
			self.logger.info("Loaded and sorted categories: %s" % category_names)
			if category_names:
				showlist(category_names, self["list"], is_country=True)
				self["list"].setCurrentIndex(0)
		except Exception as e:
			self.logger.error("Error loading categories: %s" % str(e))
			self["title"].setText(_("Error loading categories"))

	def on_item_selected(self):
		"""Handle user selecting a category."""
		index = self["list"].getCurrentIndex()
		self.logger.info("Selected category index: %s" % str(index))

		if index is None or index < 0 or index >= len(self.categories):
			self.logger.warning("Invalid category selection index: %s" % str(index))
			self["title"].setText(_("Select a valid category"))
			return

		category = self.categories[index]
		self.logger.info("Selected category: %s" % category)
		self.session.open(WorldCamWebcamScreen, category)


class WorldCamTopScreen(WebcamBaseScreen):
	"""
	Screen to display and select from the top webcams.
	"""

	def __init__(self, session, lang=None):
		super().__init__(session, lang)
		disable_summary(self)
		self.logger.info("Initializing WorldCamTopScreen")
		self.scraper = SkylineScraper(lang if lang else "en")
		self["title"] = Label(_("Top Webcams"))
		self["list"] = WebcamList([])
		self["flag_icon"] = Pixmap()
		self["language_label"] = Label(self.lang.upper())
		self["paypal"] = Label(paypal())
		self["key_red"] = Button(_("Exit"))
		self["key_green"] = Button()
		self["key_yellow"] = Button()
		self["key_blue"] = Button()
		self["actions"] = HelpableActionMap(self, "WorldCamActions", {
			"ok": self.on_item_selected,
			"cancel": self.close,
		})
		self.top_webcams = []
		self.onLayoutFinish.append(self.load_top_webcams)
		self.onLayoutFinish.append(self.set_flag_icon)

	def load_top_webcams(self):
		"""
		Load the list of top webcams, sort them by name and display in the list.
		"""
		try:
			top_webcams = self.scraper.get_top_webcams()
			self.top_webcams = sorted(top_webcams, key=lambda c: c["name"].lower())
			webcam_names = [
				w["name"] for w in self.top_webcams
				if w["name"].strip().lower() != "top live cams"
			]
			self.logger.info("Loaded and sorted top webcams: %s" % webcam_names)
			if webcam_names:
				showlist(webcam_names, self["list"], is_country=True)
				self["list"].setCurrentIndex(0)
		except Exception as e:
			self.logger.error("Error loading top webcams: %s" % str(e))
			self["title"].setText(_("Error loading top webcams"))

	def on_item_selected(self):
		"""
		Handle selection of a webcam from the list. Open player with selected webcam.
		"""
		index = self["list"].getCurrentIndex()
		self.logger.info("Selected top webcam index: %s" % str(index))

		if index is None or index < 0 or index >= len(self.top_webcams):
			self.logger.warning("Invalid top webcam selection index: %s" % str(index))
			self["title"].setText(_("Select a valid webcam"))
			return

		webcam = self.top_webcams[index]
		self.logger.info("Selected top webcam: %s" % webcam)
		self.session.open(WorldCamPlayer, webcam["name"], webcam["url"])


class WorldCamLocationScreen(WebcamBaseScreen):
	"""
	Screen to display and select locations within a country.
	"""

	def __init__(self, session, country, lang=None):
		super().__init__(session, lang)
		disable_summary(self)
		self.logger.info("Initializing WorldCamLocationScreen")
		self.country = country
		self.scraper = SkylineScraper(lang if lang else "en")
		self["title"] = Label(country["name"])
		self["list"] = WebcamList([])
		self["flag_icon"] = Pixmap()
		self["language_label"] = Label(self.lang.upper())
		self["paypal"] = Label(paypal())
		self["key_red"] = Button(_("Exit"))
		self["key_green"] = Button()
		self["key_yellow"] = Button()
		self["key_blue"] = Button()
		self["actions"] = HelpableActionMap(self, "WorldCamActions", {
			"ok": self.on_item_selected,
			"cancel": self.close,
		})
		self.locations = []
		self.onLayoutFinish.append(self.load_locations)
		self.onLayoutFinish.append(self.set_flag_icon)

	def load_locations(self):
		"""
		Load and display the list of locations for the current country.
		"""
		try:
			self.locations = self.scraper.get_locations(self.country["url"])
			location_names = sorted([loc["name"] for loc in self.locations], key=lambda s: s.lower())
			self.logger.info("Loaded locations for country %s: %s" % (self.country["name"], location_names))
			if location_names:
				showlist(location_names, self["list"], is_category=True)
				self["list"].setCurrentIndex(0)
		except Exception as e:
			self.logger.error("Error loading locations for country %s: %s" % (self.country["name"], str(e)))
			self["title"].setText(_("Error loading locations"))

	def on_item_selected(self):
		"""
		Handle the selection of a location from the list and open corresponding webcams screen.
		"""
		index = self["list"].getCurrentIndex()
		self.logger.info("Selected location index: %s" % str(index))

		if index is None or index < 0 or index >= len(self.locations):
			self.logger.warning("Invalid location selection index: %s" % str(index))
			self["title"].setText(_("Select a valid location"))
			return

		selected_item = self["list"].list[index]
		self.logger.debug("Selected item from list: %s" % str(selected_item))

		if selected_item and isinstance(selected_item, list):
			selected_name = selected_item[0]
			self.logger.info("Selected location name: %s" % selected_name)
			location = self.locations[index]
			self.logger.info("Selected location dict: %s" % str(location))
			self.session.open(WorldCamWebcamScreen, location)
		else:
			self.logger.warning("Selected item is None or not a list: %s" % str(selected_item))


class WorldCamWebcamScreen(WebcamBaseScreen):
	"""
	Screen to display and select webcams for a specific location.
	"""

	def __init__(self, session, location, lang=None):
		super().__init__(session, lang)
		self.logger.info("Initializing WorldCamWebcamScreen")
		disable_summary(self)
		self.location = location
		self.scraper = SkylineScraper(lang if lang else "en")
		self["title"] = Label(location["name"])
		self["list"] = WebcamList([])
		self["flag_icon"] = Pixmap()
		self["language_label"] = Label(self.lang.upper())
		self["paypal"] = Label(paypal())
		self["key_red"] = Button(_("Exit"))
		self["key_green"] = Button()
		self["key_yellow"] = Button()
		self["key_blue"] = Button(_("Menu"))
		self["actions"] = HelpableActionMap(self, "WorldCamActions", {
			"ok": self.on_item_selected,
			"cancel": self.close,
			"blue": self.open_context_menu,
		})
		self.webcams = []
		self.currsel = 0
		self.currpos = 0
		self.onLayoutFinish.append(self.load_webcams)
		self.onLayoutFinish.append(self.set_flag_icon)

	def open_context_menu(self):
		"""Apre il menu contestuale per il webcam selezionato"""
		index = self["list"].getCurrentIndex()
		if index is None or index < 0 or index >= len(self.webcams):
			return

		webcam = self.webcams[index]
		is_fav = FavoritesManager.is_favorite(webcam["url"])

		menu_items = [
			(_("Add to favorites"), "add_fav") if not is_fav else (_("Remove from favorites"), "remove_fav"),
			(_("Play"), "play"),
		]

		self.session.openWithCallback(
			lambda choice: self.context_menu_callback(choice, webcam),
			ChoiceBox,
			title=webcam["name"],
			list=menu_items
		)

	def context_menu_callback(self, choice, webcam):
		"""Gestisce la selezione del menu contestuale"""
		if choice is None:
			return

		if choice[1] == "add_fav":
			FavoritesManager.add_favorite(webcam["name"], webcam["url"])
			self.session.open(
				MessageBox,
				_("Added to favorites!"),
				MessageBox.TYPE_INFO,
				timeout=3
			)
		elif choice[1] == "remove_fav":
			FavoritesManager.remove_favorite(webcam["url"])
			self.session.open(
				MessageBox,
				_("Removed from favorites"),
				MessageBox.TYPE_INFO,
				timeout=3
			)
		elif choice[1] == "play":
			self.session.open(WorldCamPlayer, webcam["name"], webcam["url"])

	def load_webcams(self):
		"""
		Load and display the list of webcams for the current location.
		"""
		try:
			webcams = self.scraper.get_webcams(self.location["url"])
			self.webcams = sorted(webcams, key=lambda w: w["name"].lower())
			webcam_names = [webcam["name"] for webcam in self.webcams]
			self.logger.info("Loaded webcams for location %s: %s" % (self.location["name"], webcam_names))
			if webcam_names:
				showlist(webcam_names, self["list"], is_category=True)
				self["list"].setCurrentIndex(0)
		except Exception as e:
			self.logger.error("Error loading webcams for location %s: %s" % (self.location["name"], str(e)))
			self["title"].setText(_("Error loading webcams"))

	def on_item_selected(self):
		"""
		Handle the selection of a webcam and open the player screen.
		"""
		index = self["list"].getCurrentIndex()
		self.logger.info("Selected webcam index: %s" % str(index))

		if index is None or index < 0 or index >= len(self.webcams):
			self.logger.warning("Invalid webcam selection index: %s" % str(index))
			self["title"].setText(_("Select a valid webcam"))
			return

		selected_item = self["list"].list[index]
		self.logger.debug("Selected item from list: %s" % str(selected_item))

		if selected_item and isinstance(selected_item, list):
			selected_name = selected_item[0]
			self.logger.info("Selected webcam name: %s" % selected_name)

			webcam = self.webcams[index]
			self.logger.info("Selected webcam dict: %s" % str(webcam))
			self.session.open(WorldCamPlayer, webcam["name"], webcam["url"])
		else:
			self.logger.warning("Selected item is None or not a list: %s" % str(selected_item))


def main(session, **kwargs):
	session.open(WorldCamMainScreen)


def Plugins(**kwargs):
	from Plugins.Plugin import PluginDescriptor
	return PluginDescriptor(
		name=f"WorldCam {PLUGIN_VERSION}",
		description=_("Live webcams from around the world"),
		where=PluginDescriptor.WHERE_PLUGINMENU,
		icon=join(PLUGIN_PATH, "plugin.png"),
		fnc=main
	)
