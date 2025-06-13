# -*- coding: utf-8 -*-

from __future__ import absolute_import
__author__ = "Lululla"
__email__ = "ekekaz@gmail.com"
__copyright__ = 'Copyright (c) 2024 Lululla'
__license__ = "GPL-v2"
__version__ = "1.0.0"

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import gettext
import os
import traceback
import sys
from time import strftime

PluginLanguageDomain = 'WorldCam'
PluginLanguagePath = 'Extensions/WorldCam/locale'


def paypal():
	conthelp = "If you like what I do you\n"
	conthelp += "can contribute with a coffee\n"
	conthelp += "scan the qr code and donate € 1.00"
	return conthelp


isDreamOS = False
if os.path.exists("/usr/bin/apt-get"):
	isDreamOS = True


def localeInit():
	if isDreamOS:
		lang = language.getLanguage()[:2]
		os.environ["LANGUAGE"] = lang
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


if isDreamOS:
	def _(txt):
		return gettext.dgettext(PluginLanguageDomain, txt) if txt else ""
else:
	def _(txt):
		translated = gettext.dgettext(PluginLanguageDomain, txt)
		if translated:
			return translated
		else:
			print(("[%s] fallback to default translation for %s" % (PluginLanguageDomain, txt)))
			return gettext.gettext(txt)


localeInit()
language.addCallback(localeInit)


def log_to_file(message, label="SkylineWebcams"):
	ts = strftime("%Y-%m-%d %H:%M:%S")
	with open("/tmp/worldcam_debug.log", "a") as f:
		f.write(f"[{ts}] [{label}] {message}\n")


def log_exception():
	exc_type, exc_value, exc_traceback = sys.exc_info()
	tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
	tb_text = ''.join(tb_lines)
	log_to_file(f"EXCEPTION:\n{tb_text}", "CRITICAL")


def disable_summary(screen_instance):
	try:
		if hasattr(screen_instance, "createSummary"):
			screen_instance.createSummary = lambda: None

		if hasattr(screen_instance, "summary"):
			delattr(screen_instance, "summary")

		if not hasattr(screen_instance, "summary"):
			screen_instance.summary = None

		if not hasattr(screen_instance, "SimpleSummary"):
			screen_instance.SimpleSummary = None

	except Exception as e:
		log_to_file(f"Error disabling summary: {e}")


def safe_cleanup(screen_instance):
	"""Funzione di pulizia sicura con gestione degli errori"""
	try:
		if hasattr(screen_instance, 'cleanup') and callable(screen_instance.cleanup):
			screen_instance.cleanup()
		else:
			log_to_file(f"No cleanup method for {screen_instance.__class__.__name__}", "SAFE_CLEANUP")
	except Exception as e:
		log_to_file(f"Cleanup error in {screen_instance.__class__.__name__}: {e}", "SAFE_CLEANUP")
