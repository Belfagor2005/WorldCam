#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

"""
#########################################################
#                                                       #
#  Worldcam Player from Web Plugin                      #
#  Completely rewritten and optimized in version *5.0*  #
#  Version: 5.8                                         #
#  Created by Lululla (https://github.com/Belfagor2005) #
#  License: CC BY-NC-SA 4.0                             #
#  https://creativecommons.org/licenses/by-nc-sa/4.0    #
#  Last Modified: "18:30 - 20250703"                    #
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
import tempfile
import zipfile
from os import makedirs
from os.path import abspath, dirname, exists, join, splitext, getsize
from shutil import copyfile, copyfileobj, rmtree
# from logging.handlers import RotatingFileHandler
# from twisted.internet.threads import deferToThread

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


try:
    unicode
except NameError:
    unicode = str


# Global constants
PLUGIN_VERSION = "6.1"
PLUGIN_PATH = dirname(__file__)
DEFAULT_ICON = join(PLUGIN_PATH, "pics/webcam.png")
BASE_URL = "https://www.skylinewebcams.com"

# Initialize logger
logger = Logger()

# System language
current_language = get_system_language()
set_current_language(current_language)
screen_width = getDesktop(0).size().width()


class WebcamList(MenuList):
    """Custom list component for webcam display"""

    def __init__(self, items):
        MenuList.__init__(self, items, True, eListboxPythonMultiContent)
        self.currsel = -1
        self.currpos = 0
        # Set font size based on screen resolution
        if screen_width == 2560:
            font_size, item_height = 42, 60

        elif screen_width == 1920:
            font_size, item_height = 36, 60

        else:
            font_size, item_height = 24, 50

        self.l.setFont(0, gFont("Regular", font_size))
        self.l.setItemHeight(item_height)

    def setCurrentIndex(self, idx):
        if 0 <= idx < len(self.list):
            self.currsel = idx
            self.currpos = idx
            self.instance.moveSelectionTo(idx)

    def getCurrentIndex(self):
        # Return the actual current index from the listbox instance
        return self.instance.getCurrentIndex()

    def getSelectionIndex(self):
        # Return the stored current selection
        return self.currsel

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


def wcListEntry(name, idx, is_category=False, is_country=False, icon=None):
    """
    Create a list entry with icon and text
    Returns: List of MultiContent components
    """
    res = [name]
    lname = name.lower()
    print("NAME Category:", lname)

    # Determine appropriate icon
    if is_category:
        if icon is not None:
            pngx = get_category_icon(icon)
        else:
            # Old logic (string matching) preserved for backward compatibility
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
            # elif "webcam.pl" in lname:
                # pngx = get_category_icon("user_lists.png")
            else:
                for k, v in CATEGORY_ICONS.items():
                    if k.lower() in lname:
                        pngx = get_category_icon(v)
                        break
                else:
                    pngx = DEFAULT_ICON
    # else:
        # country_code = get_country_code(name)
        # pngx = get_flag_path(country_code) if country_code else DEFAULT_ICON

    else:
        country_code = get_country_code(name)
        print(
            "DEBUG: Country name = '%s', country_code = '%s'" %
            (name, country_code))
        if country_code:
            pngx = get_flag_path(country_code)
            print("DEBUG: Flag path for code '%s' = %s" % (country_code, pngx))
        else:
            pngx = DEFAULT_ICON
            print("DEBUG: Using default icon for '%s'" % name)

    if not exists(pngx):
        print("Icon file %s not found for name %s" % (pngx, name))

    icon_size = (60, 40)

    if screen_width == 2560:
        row_height = 60
        text_pos, text_size = (90, 0), (1200, 60)
    elif screen_width == 1920:
        row_height = 60
        text_pos, text_size = (100, 0), (950, 50)
    else:
        row_height = 50
        text_pos, text_size = (70, 0), (500, 45)

    icon_pos = (5, (row_height - icon_size[1]) // 2)
    res.append(
        MultiContentEntryPixmapAlphaTest(
            pos=icon_pos, size=icon_size, png=loadPNG(pngx)
        )
    )
    res.append(
        MultiContentEntryText(
            pos=text_pos,
            size=text_size,
            font=0,
            text=name,
            color=0xA6D1FE,
            flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
        )
    )
    return res


def showlist(data, list_widget, is_category=False, is_country=False):
    plist = []
    for idx, item in enumerate(data):
        if isinstance(item, dict):
            name = item.get("name", "")
            icon = item.get("icon")
        else:
            name = item
            icon = None
        plist.append(
            wcListEntry(
                name,
                idx,
                is_category,
                is_country,
                icon=icon))
    try:
        list_widget.setList(plist)
    except Exception:
        if hasattr(list_widget, "l") and hasattr(list_widget.l, "setList"):
            list_widget.l.setList(plist)


class WebcamBaseScreen(Screen):
    """Base class for all screens with language support"""

    def __init__(self, session, lang=None):
        Screen.__init__(self, session)
        self.logger = Logger()
        self.session = session
        self.lang = lang or get_current_language()
        self.skin_path = self.get_skin_path()
        self.skin = self.load_skin()
        self["list"] = WebcamList([])

    def get_skin_path(self):
        """Determine skin path based on screen resolution"""
        if screen_width == 2560:
            return join(PLUGIN_PATH, "skin/uhd")
        elif screen_width == 1920:
            return join(PLUGIN_PATH, "skin/fhd")
        return join(PLUGIN_PATH, "skin/hd")

    def load_skin(self):
        """Load skin XML file"""
        # skin_file = self.__class__.__name__ + ".xml"
        skin_file = "WorldCamMainScreen.xml"
        skin_path = join(self.skin_path, skin_file)
        try:
            with open(skin_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Skin loading error: {str(e)}")
            return ""

    def set_flag_icon(self):
        """Set flag icon for current language"""
        if "flag_icon" in self:
            flag_path = get_flag_path(self.lang)
            if exists(flag_path):
                pixmap = loadPNG(flag_path)
                if pixmap:
                    self["flag_icon"].instance.setPixmap(pixmap)

    def get_flag_icon(self):
        """Return the flag icon path for the current language"""
        return get_flag_path(self.lang)


class WorldCamMainScreen(WebcamBaseScreen):
    """Main screen for WorldCam plugin"""

    def __init__(self, session, lang=None):
        super().__init__(session, lang)
        disable_summary(self)
        self.logger.info("Initializing WorldCamMainScreen")
        self["flag_icon"] = Pixmap()
        self["language_label"] = Label(self.lang.upper())
        self["paypal"] = Label(paypal())
        self["title"] = Label(_("WorldCam v{}").format(PLUGIN_VERSION))
        self["key_red"] = Button(_("Exit"))
        self["key_green"] = Button(_("Select"))
        self["key_yellow"] = Button(_("Update"))
        self["key_blue"] = Button(_("Menu"))
        self.Update = False
        self.new_version = ""
        self.new_changelog = ""
        self.categories = [
            {"key": "user_lists",
             "name": _("User Lists"),
             "icon": "user_lists.png",
             "screen": WorldCamLocalScreen},
            {"key": "favorites",
             "name": _("Favorites"),
             "icon": "favorite.png",
             "screen": WorldCamFavoritesScreen},
            {"key": "continents",
             "name": _("Continents"),
             "icon": "americas.png",
             "screen": WorldCamContinentScreen},
            {"key": "countries",
             "name": _("Countries"),
             "icon": "europe.png",
             "screen": WorldCamCountryScreen},
            {"key": "categories",
             "name": _("Categories"),
             "icon": "categories.png",
             "screen": WorldCamCategoryScreen},
            {"key": "top_webcams",
             "name": _("Top Webcams"),
             "icon": "top_webcams.png",
             "screen": WorldCamTopScreen},
            # {"key": "webcam_pl", "name": _("Webcam.pl"), "icon": "webcampl.png", "screen": WorldCamPlScreen},  # New entry
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
        """Initialize UI elements"""
        self.logger.info("Initializing UI elements in WorldCamMainScreen")
        try:
            showlist(self.categories, self["list"], is_category=True)
            if self.categories:
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
            index = self["list"].getCurrentIndex()
            self.logger.info(f"Current index: {index}")
            self.logger.debug("Attempting to open Webcam.pl screen")

            if index is None or index < 0 or index >= len(self.categories):
                index = getattr(self, "currsel", 0)
                self.logger.info(f"Using fallback index: {index}")

            if 0 <= index < len(self.categories):
                category = self.categories[index]
                self.logger.info(
                    f"Opening screen for category: {category['name']}")
                self.session.open(category["screen"])
            else:
                self.logger.warning("Invalid selection index")
                self.logger.info(
                    f"Index: {index}, Category count: {len(self.categories)}")
        except Exception as e:
            import traceback
            self.logger.error(
                f"CRITICAL ERROR: {str(e)}\n{traceback.format_exc()}")
            self.session.open(
                MessageBox,
                _("Technical error in Webcam.pl"),
                MessageBox.TYPE_ERROR)

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
            choices = [(label, index)
                       for index, (label, _) in enumerate(self.menu_items)]

            self.current_menu = self.session.openWithCallback(
                self.menu_callback,
                ChoiceBox,
                title=_("Select an option"),
                list=choices
            )
        except Exception as e:
            self.logger.error("Error opening menu: %s" % str(e))

    def menu_callback(self, selection):
        """Handle menu selection"""
        try:
            if selection is not None:
                index = selection[1]
                label, callback = self.menu_items[index]
                self.logger.info("Selected menu item: %s" % label)
                if callable(callback):
                    if hasattr(self, 'current_menu') and self.current_menu:
                        self.current_menu.close()
                    callback()
        except Exception as e:
            self.logger.error("Exception during menu callback: %s" % str(e))

    def change_language(self):
        """Opens language selection screen"""
        try:
            from .LanguageScreen import LanguageScreen
            self.session.openWithCallback(
                self.on_language_selected,
                LanguageScreen,
                self.lang,
                language_flag_mapping
            )
        except Exception as e:
            self.logger.error(f"Language screen error: {str(e)}")
            self.show_message(
                _("Error opening language selection"),
                MessageBox.TYPE_ERROR)
            self.open_menu()

    def on_language_selected(self, new_lang):
        """Handle new language selection"""
        if new_lang is None:
            self.logger.info("Language selection cancelled")
            return

        self.logger.info(f"User selected language: {new_lang}")

        try:
            set_current_language(new_lang)
            self.lang = new_lang
            self.logger.info(f"New language set: {self.lang}")

            self["language_label"].setText(self.get_english_name(self.lang))
            self.set_flag_icon()
            self.initialize()

            self.logger.info(f"Language changed to {new_lang}")
            self.show_message(
                _("Language changed to %s") %
                self.get_english_name(new_lang), timeout=3)
        except Exception as e:
            self.logger.error(f"Error changing language: {str(e)}")
            self.show_message(
                _("Error changing language"),
                MessageBox.TYPE_ERROR)
        finally:
            pass

    def get_english_name(self, code):
        english_names = {
            "en": "English",
            "it": "Italian",
            "ar": "Arabic",
            "bg": "Bulgarian",
            "cs": "Czech",
            "de": "German",
            "el": "Greek",
            "es": "Spanish",
            "fa": "Persian",
            "fr": "French",
            "he": "Hebrew",
            "hr": "Croatian",
            "hu": "Hungarian",
            "ja": "Japanese",
            "ko": "Korean",
            "mk": "Macedonian",
            "nl": "Dutch",
            "pl": "Polish",
            "pt": "Portuguese",
            "ro": "Romanian",
            "ru": "Russian",
            "sk": "Slovak",
            "sl": "Slovenian",
            "sq": "Albanian",
            "sr": "Serbian",
            "th": "Thai",
            "tr": "Turkish",
            "vi": "Vietnamese",
            "zh": "Chinese"}
        return english_names.get(code, code.upper())

    def show_message(self, message, type=MessageBox.TYPE_INFO, timeout=0):
        self.session.openWithCallback(
            None, MessageBox, message, type, timeout=timeout)

    def open_settings(self):
        self.logger.info("Opening settings (placeholder)")
        try:
            # Placeholder for future Settings screen
            # Replace this block with:
            # self.session.openWithCallback(self.settings_closed,
            # SettingsScreen)
            self.defer_message(_("Settings functionality coming soon!"))
        except Exception as e:
            self.logger.error("Error in open_settings: %s" % str(e))
            self.defer_message(
                _("Error opening settings:\n%s") %
                str(e), MessageBox.TYPE_ERROR)
        finally:
            self.open_menu()

    # def settings_closed(self, result=None):
        # self.logger.info(
            # "Settings screen closed with result: %s" %
            # str(result))

    def check_update_silent(self):
        """Silently check for updates"""
        self.update_plugin(silent=True)

    def update_plugin(self, silent=False):
        """Check and update the plugin"""
        remote_version = "0.0"
        remote_changelog = ""

        try:
            req = Request(
                b64decoder(installer_url), headers={
                    "User-Agent": AgentRequest})
            page = urlopen(req).read().decode("utf-8")
        except Exception as e:
            if not silent:
                self.defer_message(
                    _("Unable to fetch version info:\n{}").format(
                        str(e)), MessageBox.TYPE_ERROR)
            return

        for line in page.split("\n"):
            line = line.strip()
            if line.startswith("version"):
                remote_version = line.split(
                    "=")[-1].strip().strip("'").strip('"')
            elif line.startswith("changelog"):
                remote_changelog = line.split(
                    "=")[-1].strip().strip("'").strip('"')
                break

        self.new_version = str(remote_version)
        self.new_changelog = str(remote_changelog)

        if PLUGIN_VERSION < self.new_version:
            self.ask_update()
        else:
            if not silent:
                self.defer_message(
                    _("You are already running the latest version: {}").format(PLUGIN_VERSION),
                    MessageBox.TYPE_INFO)

    def ask_update(self):
        """Prompt user to update"""
        def ask():
            self.session.openWithCallback(
                self.install_update,
                MessageBox,
                _("New version %s available\n\nChangelog: %s\n\nDo you want to install it now?") %
                (self.new_version,
                    self.new_changelog),
                MessageBox.TYPE_YESNO)
        self._defer_timer = eTimer()
        self._defer_timer.callback.append(ask)
        self._defer_timer.start(100, True)

    def install_update(self, answer=False):
        """Install the update"""
        if answer:
            try:
                self.session.open(
                    Console,
                    _("Upgrading..."),
                    cmdlist=[
                        "wget -q --no-check-certificate " +
                        b64decoder(installer_url) +
                        " -O - | /bin/sh"],
                    finishedCallback=self.update_callback,
                    closeOnSuccess=False)
            except Exception as e:
                self.logger.error("Error starting update: %s" % str(e))
                self.defer_message(
                    _("Update failed:\n%s") %
                    str(e), MessageBox.TYPE_ERROR)
        else:
            self.defer_message(_("Update Aborted!"), MessageBox.TYPE_INFO)

    def update_callback(self, result=None):
        """Handle update completion"""
        self.logger.info("Update finished with result: %s" % str(result))
        if result == 0:
            self.session.open(
                MessageBox,
                _("Update completed successfully!\n\nThe plugin will now close."),
                type=MessageBox.TYPE_INFO,
                timeout=4).addCallback(
                lambda _: self.close())
        else:
            self.defer_message(
                _("Update encountered an error (code: %s)") % str(result),
                MessageBox.TYPE_ERROR
            )

    def update_yt_dlp_from_github(self):
        """Update yt-dlp from GitHub"""
        self.logger.info("Starting yt-dlp update...")
        try:
            # Setup temp directory
            tmp_dir = tempfile.mkdtemp(prefix="worldcam_yt_dlp_update_")
            zip_path = join(tmp_dir, "yt_dlp.zip")

            # Download yt-dlp
            repo_url = "https://github.com/yt-dlp/yt-dlp/archive/refs/heads/master.zip"
            response = requests.get(repo_url, stream=True, timeout=30)
            response.raise_for_status()
            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                root_folder = zip_ref.namelist()[0].split("/")[0]
                self.logger.info(
                    f"Extracting 'yt_dlp' folder from {root_folder}")

                plugin_folder = dirname(abspath(__file__))
                dest_yt_dlp_folder = join(plugin_folder, "yt_dlp")

                # Remove old version
                if exists(dest_yt_dlp_folder):
                    self.logger.info("Removing old yt_dlp folder")
                    rmtree(dest_yt_dlp_folder)

                # Extract new version
                for member in zip_ref.namelist():
                    if member.startswith(f"{root_folder}/yt_dlp/"):
                        rel_path = member[len(root_folder) + 1:]
                        target_path = join(plugin_folder, rel_path)
                        if member.endswith("/"):
                            makedirs(target_path, exist_ok=True)
                        else:
                            with zip_ref.open(member) as source, open(target_path, "wb") as target:
                                copyfileobj(source, target)

            # Cleanup
            rmtree(tmp_dir)
            init_mod = join(PLUGIN_PATH, "__init__-mod-ytl-extractor.py")
            init_extract = join(PLUGIN_PATH, "yt_dlp/extractor/__init__.py")
            copyfile(init_mod, init_extract)
            self.logger.info("yt-dlp update completed successfully")
            self.defer_message(
                _("yt-dlp updated successfully!"),
                MessageBox.TYPE_INFO)

        except Exception as e:
            self.logger.error(f"Failed to update yt-dlp: {str(e)}")
            self.defer_message(
                _("Failed to update yt-dlp:\n%s") %
                str(e), MessageBox.TYPE_ERROR)

    def get_about_text(self):
        """Generate about text"""
        return (
            _("WorldCam v{}").format(PLUGIN_VERSION) + "\n\n" +
            _("Live webcam viewer featuring global locations") + "\n\n" +
            _("Developed by Lululla") + "\n\n" +
            _("Powered by Enigma2 and Python") + "\n\n" +
            _("GitHub: https://github.com/Belfagor2005/") + "\n" +
            _("Forum support: www.corvoboys.org") + "\n\n" +
            _("Included playlists and sources:") + "\n" +
            _("- Local webcam list") + "\n" +
            _("- Local YouTube playlist") + "\n" +
            _("- Online webcam list") + "\n" +
            _("- Online Direct and YouTube webcams") + "\n" +
            _("- Other sources")
        )

    def open_about(self):
        """Open about dialog from menu"""
        self.session.openWithCallback(
            self.open_menu,
            MessageBox,
            self.get_about_text(),
            MessageBox.TYPE_INFO)

    def open_about_direct(self):
        """Directly open about dialog"""
        self.session.open(
            MessageBox,
            self.get_about_text(),
            MessageBox.TYPE_INFO)

    def defer_message(self, text, mtype=MessageBox.TYPE_INFO):
        """Show message with a short delay to avoid UI modal conflicts"""
        self._defer_timer = eTimer()
        self._defer_timer.callback.append(
            lambda: self.session.open(
                MessageBox, text, type=mtype))
        self._defer_timer.start(100, True)


class WorldCamFavoritesScreen(WebcamBaseScreen):
    def __init__(self, session, lang=None):
        super().__init__(session, lang)
        disable_summary(self)
        self.logger.info("Initializing WorldCamFavoritesScreen")
        self["title"] = Label(_("Your Favorites"))
        self["flag_icon"] = Pixmap()
        self["language_label"] = Label(self.lang.upper())
        self["paypal"] = Label(paypal())
        self["key_red"] = Button(_("Exit"))
        self["key_green"] = Button(_("Play"))
        self["key_yellow"] = Button(_("Remove"))
        self["key_blue"] = Button(_("Export"))
        self["actions"] = HelpableActionMap(self, "WorldCamActions", {
            "ok": self.on_item_selected,
            "cancel": self.close,
            "red": self.close,
            "green": self.on_item_selected,
            "yellow": self.remove_favorite,
            "blue": self.export_favorites
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

    def remove_favorite(self):
        """Rimuove il webcam selezionato dai preferiti"""
        index = self["list"].getCurrentIndex()
        if index is None or index < 0 or index >= len(self.favorites):
            return

        webcam = self.favorites[index]
        if FavoritesManager.remove_favorite(webcam["url"]):
            self.load_favorites()
            self.session.open(
                MessageBox,
                _("Removed from favorites: %s") % webcam["name"],
                MessageBox.TYPE_INFO,
                timeout=3
            )

    def export_favorites(self):
        """Export favorites to Enigma2 bouquet"""
        success, message = FavoritesManager.export_to_bouquet()
        self.session.open(
            MessageBox,
            message,
            MessageBox.TYPE_INFO if success else MessageBox.TYPE_ERROR
        )

    def on_item_selected(self):
        """Riproduce il webcam selezionato"""
        index = self["list"].getCurrentIndex()
        if index is None or index < 0 or index >= len(self.favorites):
            return
        # webcam = self.favorites[index]
        self.session.open(
            WorldCamPlayer,
            webcams=self.favorites,
            current_index=index
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
            self.logger.info(
                "Loading user playlists from: %s" %
                playlists_path)
            self.user_lists = self.scraper.get_local_playlists(playlists_path)

            if not exists(playlists_path):
                try:
                    makedirs(playlists_path)
                    self.logger.info(
                        f"Created playlists directory: {playlists_path}")
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
        self.logger.info(
            "Initializing WorldCamLocal with category: %s" %
            playlists)
        self.category = playlists
        self.scraper = SkylineScraper(lang if lang else "en")
        self["title"] = Label(splitext(playlists)[0])
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
        self.logger.info(f"Loading webcams from: {path}")

        try:
            if not exists(path):
                self.logger.error(f"File not found: {path}")
                self["title"].setText(_("File not found"))
                return

            if getsize(path) == 0:
                self.logger.error(f"Empty file: {path}")
                self["title"].setText(_("Empty playlist file"))
                return

            self.webcams = self.scraper.parse_local_playlist_file(path)

            if not self.webcams:
                self.logger.warning("No webcams parsed from file")
                self["title"].setText(_("No valid webcams in playlist"))
            else:
                showlist([w["name"] for w in self.webcams],
                         self["list"], is_category=True)
                self["list"].setCurrentIndex(0)

        except Exception as e:
            self.logger.error(f"Error loading playlist: {str(e)}")
            self["title"].setText(_("Error loading playlist"))

    def on_item_selected(self):
        """Handle selection of a webcam and open the player."""
        index = self["list"].getCurrentIndex()
        if index is None or index < 0 or index >= len(self.webcams):
            self.logger.warning(
                "Invalid webcam selection index: %s" %
                str(index))
            self["title"].setText(_("Select a valid webcam"))
            return

        webcam = self.webcams[index]
        self.logger.info(
            "Selected webcam: %s URL: %s" %
            (webcam["name"], webcam["url"]))
        # self.session.open(WorldCamPlayer, webcam["name"], webcam["url"])
        self.session.open(
            WorldCamPlayer,
            webcams=self.webcams,
            current_index=index
        )


class WorldCamContinentScreen(WebcamBaseScreen):
    """Screen to display continents"""

    def __init__(self, session, lang=None):
        super().__init__(session, lang)
        disable_summary(self)
        self.logger.info("Initializing WorldCamContinentScreen")
        self.scraper = SkylineScraper(lang if lang else "en")
        self["title"] = Label(_("Continents"))
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
            continent_names = [continent["name"]
                               for continent in self.continents]
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
        self.logger.info(
            f"Initializing WorldCamContinentCountryScreen for {continent['name']}")
        self.continent = continent
        # self.scraper = SkylineScraper(lang if lang else "en")
        self["title"] = Label(continent["name"])
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
            self.logger.info(
                f"Loaded {len(country_names)} countries for {self.continent['name']}")
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
        self["title"] = Label(_("Country"))
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
            self.logger.warning(
                "Invalid country selection index: %s" %
                str(index))
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
        self.categories = []
        self.onLayoutFinish.append(self.load_categories)
        self.onLayoutFinish.append(self.set_flag_icon)

    def load_categories(self):
        """Load categories from scraper and display them sorted."""
        try:
            categories = self.scraper.get_categories()
            self.categories = sorted(
                categories, key=lambda c: c["name"].lower())
            category_names = [cat["name"] for cat in self.categories]
            self.logger.info(
                "Loaded and sorted categories: %s" %
                category_names)
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
            self.logger.warning(
                "Invalid category selection index: %s" %
                str(index))
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
            self.top_webcams = sorted(
                top_webcams, key=lambda c: c["name"].lower())
            webcam_names = [
                w["name"] for w in self.top_webcams
                if w["name"].strip().lower() != "top live cams"
            ]
            self.logger.info(
                "Loaded and sorted top webcams: %s" %
                webcam_names)
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
            self.logger.warning(
                "Invalid top webcam selection index: %s" %
                str(index))
            self["title"].setText(_("Select a valid webcam"))
            return

        webcam = self.top_webcams[index]
        self.logger.info("Selected top webcam: %s" % webcam)
        # self.session.open(WorldCamPlayer, webcam["name"], webcam["url"])
        self.session.open(
            WorldCamPlayer,
            webcams=self.top_webcams,
            current_index=index
        )


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
            location_names = sorted(
                [loc["name"] for loc in self.locations], key=lambda s: s.lower())
            self.logger.info(
                "Loaded locations for country %s: %s" %
                (self.country["name"], location_names))
            if location_names:
                showlist(location_names, self["list"], is_category=True)
                self["list"].setCurrentIndex(0)
        except Exception as e:
            self.logger.error(
                "Error loading locations for country %s: %s" %
                (self.country["name"], str(e)))
            self["title"].setText(_("Error loading locations"))

    def on_item_selected(self):
        """
        Handle the selection of a location from the list and open corresponding webcams screen.
        """
        index = self["list"].getCurrentIndex()
        self.logger.info("Selected location index: %s" % str(index))

        if index is None or index < 0 or index >= len(self.locations):
            self.logger.warning(
                "Invalid location selection index: %s" %
                str(index))
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
            self.logger.warning(
                "Selected item is None or not a list: %s" %
                str(selected_item))


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
        self["flag_icon"] = Pixmap()
        self["language_label"] = Label(self.lang.upper())
        self["paypal"] = Label(paypal())
        self["key_red"] = Button(_("Exit"))
        self["key_green"] = Button(_("Add/Remove"))
        self["key_yellow"] = Button(_("Export"))
        self["key_blue"] = Button(_("Menu"))
        self["actions"] = HelpableActionMap(self, "WorldCamActions", {
            "ok": self.on_item_selected,
            "cancel": self.close,
            "blue": self.open_context_menu,
            "green": self.toggle_favorite,
            "yellow": self.export_bouquet_direct,
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
            (_("Add to favorites"), "add_fav") if not is_fav else (
                _("Remove from favorites"), "remove_fav"),
            (_("Play"), "play"),
            (_("Export All to Bouquet"), "export_bouquet"),
        ]

        self.session.openWithCallback(
            lambda choice: self.context_menu_callback(choice, webcam),
            ChoiceBox,
            title=webcam["name"],
            list=menu_items
        )

    def toggle_favorite(self):
        """Aggiunge o rimuove la webcam corrente dai preferiti"""
        index = self["list"].getCurrentIndex()
        if index is None or index < 0 or index >= len(self.webcams):
            return

        webcam = self.webcams[index]
        is_fav = FavoritesManager.is_favorite(webcam["url"])

        if is_fav:
            FavoritesManager.remove_favorite(webcam["url"])
            self.session.open(
                MessageBox,
                _("Removed from favorites"),
                MessageBox.TYPE_INFO,
                timeout=3
            )
        else:
            FavoritesManager.add_favorite(webcam["name"], webcam["url"])
            self.session.open(
                MessageBox,
                _("Added to favorites!"),
                MessageBox.TYPE_INFO,
                timeout=3
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
        if choice[1] == "export_bouquet":
            success, message = FavoritesManager.export_to_bouquet()
            self.session.open(
                MessageBox,
                message,
                MessageBox.TYPE_INFO if success else MessageBox.TYPE_ERROR
            )
        elif choice[1] == "play":
            # self.session.open(WorldCamPlayer, webcam["name"], webcam["url"])
            index = self["list"].getCurrentIndex()
            self.session.open(
                WorldCamPlayer,
                webcams=self.webcams,
                current_index=index
            )

    def export_bouquet_direct(self):
        """Esegue direttamente l'esportazione nel bouquet"""
        success, message = FavoritesManager.export_to_bouquet()
        self.session.open(
            MessageBox,
            message,
            MessageBox.TYPE_INFO if success else MessageBox.TYPE_ERROR
        )

    def load_webcams(self):
        """
        Load and display the list of webcams for the current location.
        """
        try:
            webcams = self.scraper.get_webcams(self.location["url"])
            self.webcams = sorted(webcams, key=lambda w: w["name"].lower())
            webcam_names = [webcam["name"] for webcam in self.webcams]
            self.logger.info(
                "Loaded webcams for location %s: %s" %
                (self.location["name"], webcam_names))
            if webcam_names:
                showlist(webcam_names, self["list"], is_category=True)
                self["list"].setCurrentIndex(0)
        except Exception as e:
            self.logger.error(
                "Error loading webcams for location %s: %s" %
                (self.location["name"], str(e)))
            self["title"].setText(_("Error loading webcams"))

    def on_item_selected(self):
        """
        Handle the selection of a webcam and open the player screen.
        """
        index = self["list"].getCurrentIndex()
        self.logger.info("Selected webcam index: %s" % str(index))

        if index is None or index < 0 or index >= len(self.webcams):
            self.logger.warning(
                "Invalid webcam selection index: %s" %
                str(index))
            self["title"].setText(_("Select a valid webcam"))
            return

        selected_item = self["list"].list[index]
        self.logger.debug("Selected item from list: %s" % str(selected_item))

        if selected_item and isinstance(selected_item, list):
            selected_name = selected_item[0]
            self.logger.info("Selected webcam name: %s" % selected_name)

            webcam = self.webcams[index]
            self.logger.info("Selected webcam dict: %s" % str(webcam))
            # self.session.open(WorldCamPlayer, webcam["name"], webcam["url"])
            self.session.open(
                WorldCamPlayer,
                webcams=self.webcams,
                current_index=index
            )
        else:
            self.logger.warning(
                "Selected item is None or not a list: %s" %
                str(selected_item))


def main(session, **kwargs):
    from .checkdependencies import check_requirements
    logger = Logger()
    check_requirements(logger=logger)
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
