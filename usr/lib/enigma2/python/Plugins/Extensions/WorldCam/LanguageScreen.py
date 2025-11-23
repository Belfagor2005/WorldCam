#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

"""
#########################################################
#                                                       #
#  Worldcam Utils for Plugin                            #
#  Version: 5.0                                         #
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

from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Screens.Screen import Screen
from Tools.LoadPixmap import LoadPixmap

from . import _
from .utils import get_flag_path


def LanguageEntryComponent(name, code):
    """
    Create a language list entry with flag and name.
    """
    flag_path = get_flag_path(code)
    png = LoadPixmap(flag_path)
    if png is None:
        png = LoadPixmap(get_flag_path("en"))
    return (code, name, png)


class LanguageScreen(Screen):
    """Language selection screen with flags"""

    def __init__(self, session, current_lang, flag_mapping):
        Screen.__init__(self, session)
        self.setTitle(_("Select language"))
        self.current_lang = current_lang
        self.flag_mapping = flag_mapping

        self.skin = """
            <screen name="LanguageScreen" position="center,center" size="600,800" title="Select language" flags="wfNoBorder">
                <widget source="list" render="Listbox" position="27,13" size="550,750" itemHeight="50" enableWrapAround="1" transparent="1" itemCornerRadius="8" scrollbarMode="showOnDemand" scrollbarSliderForegroundColor="mcolor5" scrollbarSliderBorderColor="mcolor2" scrollbarWidth="10" scrollbarSliderBorderWidth="1">
                    <convert type="TemplatedMultiContent">
                        {"template": [
                            MultiContentEntryPixmapAlphaTest(pos = (10, 5), size = (60, 40), png = 2),
                            MultiContentEntryText(pos = (90, 0), size = (400, 40), flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 1)
                        ],
                        "fonts": [gFont("Regular", 28)],
                        "itemHeight": 50
                        }
                    </convert>
                </widget>
            </screen>
        """

        self["list"] = List([])
        self["actions"] = ActionMap(["OkCancelActions"], {
            "ok": self.ok,
            "cancel": self.cancel,
        })

        self.onLayoutFinish.append(self.buildList)

    def buildList(self):
        languages = []
        for code in sorted(self.flag_mapping.keys()):
            name = self.get_english_name(code)
            entry = LanguageEntryComponent(
                name, code)  # returns (code, name, png)
            languages.append(entry)

        self["list"].setList(languages)
        self.selectActiveLanguage()

    def get_english_name(self, code):
        """Returns the English name of the language"""
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

    def selectActiveLanguage(self):
        """Select the current language in the list"""
        for index, entry in enumerate(self["list"].list):
            if entry[0] == self.current_lang:
                self["list"].index = index
                break

    def get_english_namex(self, code):
        """Return the English name of the language"""
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
            "jp": "Japanese",
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
            "zh": "Chinese",
        }
        return english_names.get(code, code.upper())

    def ok(self):
        """Confirm the selected language"""
        selected = self["list"].getCurrent()
        if selected:
            self.close(selected[0])
        else:
            self.close(None)

    def cancel(self):
        """Cancel the language selection"""
        self.close(None)
