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
#  Last Modified: "21:50 - 20250606"                    #
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

from json import load, dump
from os import makedirs, remove, listdir
from os.path import abspath, dirname, exists, isfile, join

from re import search, sub
import sys
import html
from time import strftime
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, unquote, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen
from enigma import eDVBDB, eEnv
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN

from . import _
from . import checkdependencies

# Python version flags
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info.major >= 3
PY34 = sys.version_info[0:2] >= (3, 4)
PY39 = sys.version_info[0:2] >= (3, 9)

# Plugin path and resources
PLUGIN_PATH = dirname(__file__)
COUNTRY_CODES_FILE = {}
COUNTRY_CODES_FILE = join(PLUGIN_PATH, "cowntry_code.json")
DEFAULT_ICON = join(PLUGIN_PATH, "pics/webcam.png")

# Compatibility alias for unicode
try:
	unicode
except NameError:
	unicode = str


def reload_services():
	"""Reload the list of services"""
	eDVBDB.getInstance().reloadServicelist()
	eDVBDB.getInstance().reloadBouquets()


class Logger:
	_instance = None

	LEVELS = {
		"DEBUG": ("\033[92m", "[DEBUG]"),    # green
		"INFO": ("\033[97m", "[INFO] "),     # white
		"WARNING": ("\033[93m", "[WARN] "),  # yellow
		"ERROR": ("\033[91m", "[ERROR]"),    # red
		"CRITICAL": ("\033[95m", "[CRIT] ")  # magenta
	}
	END = "\033[0m"

	def __new__(cls, *args, **kwargs):
		if cls._instance is None:
			cls._instance = super(Logger, cls).__new__(cls)
			cls._instance.__initialized = False
		return cls._instance

	def __init__(self, log_path=None, clear_on_start=True):
		if self.__initialized:
			return
		self.__initialized = True
		log_dir = "/tmp/worldcam"

		if not exists(log_dir):
			try:
				makedirs(log_dir)
			except Exception:
				pass

		# Set default log path if not provided
		self.log_path = log_path or join(log_dir, "worldcam.log")

		# Clear log if requested
		if clear_on_start and exists(self.log_path):
			try:
				remove(self.log_path)
			except Exception as e:
				print(f"Couldn't clear log file: {str(e)}")

	def log(self, message, level="INFO", *args):
		# Get prefix and label, default to INFO if unknown level
		prefix, label = self.LEVELS.get(level, self.LEVELS["INFO"])
		timestamp = strftime("%Y-%m-%d %H:%M:%S")

		# Create formatted console message with colors
		console_msg = f"{timestamp} {label} {prefix}{message}{self.END}"
		print(console_msg)

		# Write to log file (without color codes)
		if self.log_path:
			try:
				with open(self.log_path, "a") as f:
					f.write(f"{timestamp} {label} {message}\n")
			except Exception as e:
				print(f"Log write failed: {str(e)}")

	def info(self, message, *args):
		self.log(message, "INFO")

	def warning(self, message, *args):
		self.log(message, "WARNING")

	def error(self, message, *args):
		self.log(message, "ERROR")

	def critical(self, message, *args):
		self.log(message, "CRITICAL")

	def debug(self, message, *args):
		self.log(message, "DEBUG")


FAVORITES_FILE = join(PLUGIN_PATH, "favorites.json")


# Update the safe_encode_url function
def safe_encode_url(url):
	"""Safely encode URLs with non-ASCII characters"""
	if isinstance(url, unicode):
		try:
			parsed = urlparse(url)
			netloc = parsed.netloc.encode('idna')
			path = quote(parsed.path.encode('utf-8'), safe='/-_')
			query = quote(parsed.query.encode('utf-8'), safe='=&')
			return urlunparse((
				parsed.scheme,
				netloc,
				path,
				parsed.params,
				query,
				parsed.fragment
			))
		except Exception:
			# Fallback to UTF-8 encoding
			return url.encode('utf-8', 'ignore')
	return url


def encode_url(url):
	"""Properly encode URLs with special characters"""
	if not url.startswith('http'):
		return url
		
	parsed = urlparse(url)
	encoded_path = quote(parsed.path)
	safe_url = urlunparse((
		parsed.scheme,
		parsed.netloc,
		encoded_path,
		parsed.params,
		parsed.query,
		parsed.fragment
	))
	return safe_url


def clean_html_entities(text):
	"""Clean HTML entities like &amp; &quot; etc."""
	if not text:
		return text
		
	try:
		# Unescape HTML entities
		cleaned = html.unescape(text)
		
		# Additional cleaning for specific cases
		cleaned = cleaned.replace('&amp;', '&')
		cleaned = cleaned.replace('&quot;', '"')
		cleaned = cleaned.replace('&apos;', "'")
		cleaned = cleaned.replace('&lt;', '<')
		cleaned = cleaned.replace('&gt;', '>')
		cleaned = cleaned.replace('&nbsp;', ' ')
		
		return cleaned.strip()
	except Exception as e:
		Logger().error(f"Error cleaning HTML entities: {str(e)}")
		return text


class FavoritesManager:
	@staticmethod
	def load_favorites():
		"""Carica i preferiti dal file JSON"""
		if not exists(FAVORITES_FILE):
			return []
		try:
			with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
				return load(f)
		except Exception as e:
			logger.error(f"Error loading favorites: {str(e)}")
			return []

	@staticmethod
	def save_favorites(favorites):
		"""Salva i preferiti nel file JSON"""
		try:
			with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
				dump(favorites, f, indent=4, ensure_ascii=False)
			return True
		except Exception as e:
			logger.error(f"Error saving favorites: {str(e)}")
			return False

	@staticmethod
	def add_favorite(name, url):
		"""Aggiunge un webcam ai preferiti"""
		favorites = FavoritesManager.load_favorites()

		# Controlla se esiste già
		if any(fav["url"] == url for fav in favorites):
			return False

		favorites.append({"name": name, "url": url})
		return FavoritesManager.save_favorites(favorites)

	@staticmethod
	def remove_favorite(url):
		"""Rimuove un webcam dai preferiti"""
		favorites = FavoritesManager.load_favorites()
		new_favorites = [fav for fav in favorites if fav["url"] != url]

		if len(new_favorites) == len(favorites):
			return False  # Non trovato

		return FavoritesManager.save_favorites(new_favorites)

	@staticmethod
	def is_favorite(url):
		"""Controlla se un URL è nei preferiti"""
		return any(
			fav["url"] == url for fav in FavoritesManager.load_favorites())

	@staticmethod
	def export_to_bouquet():
		"""Export favorites to Enigma2 bouquet"""
		try:
			favorites = FavoritesManager.load_favorites()
			if not favorites:
				return False, _("No favorites to export")

			# Create bouquet directory if needed
			bouquet_dir = eEnv.resolve("${sysconfdir}/enigma2")
			if not exists(bouquet_dir):
				makedirs(bouquet_dir)

			# Create bouquet file
			bouquet_name = "userbouquet.worldcam_favorites.tv"
			bouquet_path = join(bouquet_dir, bouquet_name)

			with open(bouquet_path, "w", encoding="utf-8") as f:
				f.write("#NAME WorldCam Favorites\n")
				for fav in favorites:
					# Create service reference
					if "youtube.com" in fav["url"] or "youtu.be" in fav["url"]:
						# YouTube streams require special handling
						service_type = 5001  # HLS
						service_url = f"http://localhost:8000/proxy.m3u8?url={quote(fav['url'])}"
					else:
						service_type = 4097  # HTTP
						service_url = fav["url"]

					# Create service line
					service_line = f"#SERVICE {service_type}:0:1:0:0:0:0:0:0:0:{service_url}\n"
					f.write(service_line)
					f.write(f"#DESCRIPTION {fav['name']}\n")

			# Add to bouquet list
			bouquets_path = join(bouquet_dir, "bouquets.tv")
			if not exists(bouquets_path):
				with open(bouquets_path, "w") as f:
					f.write("#NAME Bouquets (TV)\n")

			# Check if already exists in bouquets
			with open(bouquets_path, "r") as f:
				content = f.read()

			bouquet_ref = f"#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"{bouquet_name}\" ORDER BY bouquet"
			if bouquet_ref not in content:
				with open(bouquets_path, "a") as f:
					f.write(f"{bouquet_ref}\n")

			from twisted.internet import reactor
			reactor.callFromThread(reload_services)
			return True, _(
				"Favorites exported successfully! Restart Enigma2 to see them.")
		except Exception as e:
			logger.error(f"Export error: {str(e)}")
			return False, _("Export failed: ") + str(e)


def isPythonFolder():
	path = "/usr/lib/"
	for name in listdir(path):
		fullname = join(path, name)
		if not isfile(fullname) and "python" in name:
			print(fullname)
			print("sys.version_info =", sys.version_info)
			x = join(fullname, "site-packages", "streamlink")
			print(x)
			if exists(x):
				return x
	return False


def is_streamlinkproxy_available():
	"""Verifica se StreamlinkProxy è installato"""
	try:
		import subprocess
		result = subprocess.run(
			["opkg", "list-installed", "enigma2-plugin-extensions-streamlinkproxy"],
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			text=True
		)
		return "enigma2-plugin-extensions-streamlinkproxy" in result.stdout
	except Exception:
		return False


def is_streamlink_available():
	streamlink_folder = isPythonFolder()
	return streamlink_folder


def get_streamlink_path():
	"""Find streamlink executable in common locations"""
	possible_paths = [
		"/usr/bin/streamlink",
		"/usr/local/bin/streamlink",
		join(dirname(abspath(__file__)), "bin/streamlink")
	]
	
	for path in possible_paths:
		if exists(path):
			return path
	return None


def is_exteplayer3_Available():
	from enigma import eEnv
	path = eEnv.resolve("$bindir/exteplayer3")
	return isfile(path)


def b64encoder(source):
	"""Encode a string to base64, ensuring bytes input for Python 3."""
	import base64
	if PY3:
		source = source.encode("utf-8")
	content = base64.b64encode(source).decode("utf-8")
	return content


def b64decoder(data):
	"""Robust base64 decoding with padding correction, returns decoded utf-8 string or empty on error."""
	import base64
	data = data.strip()
	pad = len(data) % 4
	if pad == 1:  # Invalid base64 length
		return ""
	if pad:
		data += "=" * (4 - pad)
	try:
		decoded = base64.b64decode(data)
		return decoded.decode("utf-8") if PY3 else decoded
	except Exception as e:
		print("Base64 decoding error: %s" % e)
		return ""


def get_system_language():
	"""Retrieve system language from Enigma2 settings file."""
	try:
		with open("/etc/enigma2/settings", "r") as settings_file:
			for line in settings_file:
				if "config.osd.language=" in line:
					lang = line.split("=")[1].strip().split("_")[0]
					return lang
	except Exception:
		pass
	return "en"  # Default language


def disable_summary(screen_instance):
	"""Disable summary features safely on a screen instance."""
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
		logger = Logger()
		logger.error("Error disabling summary: " + str(e))


def safe_cleanup(screen_instance):
	"""Perform safe cleanup on a screen instance with error handling."""
	logger = Logger()
	logger.info("safe_cleanup:")
	try:
		if hasattr(
				screen_instance,
				"cleanup") and callable(
				screen_instance.cleanup):
			screen_instance.cleanup()
		else:
			logger.debug(
				"No cleanup method for " +
				screen_instance.__class__.__name__,
				"SAFE_CLEANUP")
	except Exception as e:
		logger.error(
			"Cleanup error in " +
			screen_instance.__class__.__name__ +
			": " +
			str(e),
			"SAFE_CLEANUP")


def _sort_by_name(items):
	"""
	If items is a list of strings, sort directly.
	If items is a list of dicts with "name", sort by the name key.
	"""
	if not items:
		return items
	if isinstance(items[0], str):
		return sorted(items, key=lambda x: x.lower())
	elif isinstance(items[0], dict) and "name" in items[0]:
		return sorted(items, key=lambda x: x["name"].lower())
	else:
		return items


def get_ytdlp_path():
	"""Return valid yt-dlp import path or None if not found"""
	possible_paths = [
		"/usr/bin/yt-dlp",
		"/usr/local/bin/yt-dlp",
		"/usr/lib/enigma2/python/Plugins/Extensions/WorldCam/yt_dlp",
		join(dirname(abspath(__file__)), 'yt_dlp')
	]
	
	for path in possible_paths:
		if exists(path):
			return path
	return None


def is_ytdlp_available(logger=None):
	"""
	Check availability of yt_dlp module in different locations with fallbacks.
	Returns:
		tuple: (YoutubeDL, DownloadError) if found, otherwise (None, None)
	"""

	# 1. Try system-wide import
	try:
		from yt_dlp import YoutubeDL
		from yt_dlp.utils import DownloadError
		if logger:
			logger.info("Using system-wide yt_dlp")
		return YoutubeDL, DownloadError
	except ImportError:
		pass

	# 2. Try plugin's hardcoded path
	try:
		yt_dlp_path = "/usr/lib/enigma2/python/Plugins/Extensions/WorldCam/yt_dlp"
		if yt_dlp_path not in sys.path:
			sys.path.append(yt_dlp_path)
		from yt_dlp import YoutubeDL
		from yt_dlp.utils import DownloadError
		if logger:
			logger.info("Using plugin's hardcoded path yt_dlp")
		return YoutubeDL, DownloadError
	except ImportError:
		pass

	# 3. Try plugin's relative path
	try:
		plugin_dir = dirname(abspath(__file__))
		if plugin_dir not in sys.path:
			sys.path.append(plugin_dir)
		from yt_dlp import YoutubeDL
		from yt_dlp.utils import DownloadError
		if logger:
			logger.info("Using plugin's relative path yt_dlp")
		return YoutubeDL, DownloadError
	except ImportError:
		pass

	# 4. Try plugin's yt_dlp subdirectory
	try:
		plugin_dir = dirname(abspath(__file__))
		yt_dlp_subdir = join(plugin_dir, 'yt_dlp')
		if yt_dlp_subdir not in sys.path:
			sys.path.append(yt_dlp_subdir)
		from yt_dlp import YoutubeDL
		from yt_dlp.utils import DownloadError
		if logger:
			logger.info("Using plugin's yt_dlp subdirectory")
		return YoutubeDL, DownloadError
	except ImportError:
		pass

	# 5. Try imp fallback
	try:
		import imp
		plugin_dir = dirname(abspath(__file__))
		yt_dlp_path = join(plugin_dir, 'yt_dlp', '__init__.py')

		if exists(yt_dlp_path):
			yt_dlp_module = imp.load_source('yt_dlp', yt_dlp_path)
			if logger:
				logger.info("Using imp-loaded yt_dlp")
			return yt_dlp_module.YoutubeDL, Exception  # fallback generico
	except Exception as e:
		if logger:
			logger.error("imp fallback failed: %s", str(e))

	# All methods failed
	if logger:
		logger.error("yt_dlp not found in any location")
	return None, None


def extract_list_item(current, logger=None):
	"""
	Universal function to extract item data from list selection
	Returns: (item_name, item_data) or (None, None) on error
	"""
	try:
		if logger:
			logger.debug(f"Elemento selezionato: {str(current)[:100]}...")

		# Gestione struttura Enigma2 standard
		if isinstance(current, list) and len(current) > 0:
			# Caso 1: Elemento con struttura [nome, dati, ...]
			if len(current) >= 2:
				return current[0], current[1]
			# Caso 2: Elemento con solo nome
			elif len(current) == 1:
				return current[0], None

		# Gestione oggetti MenuList particolari
		elif hasattr(current, '__getitem__'):
			return current[0], current[1] if len(current) > 1 else None

		logger.error(f"Struttura elemento non supportata: {type(current)}")
		return None, None

	except Exception as e:
		if logger:
			logger.error(f"Errore estrazione elemento: {str(e)}")
			import traceback
			logger.error(traceback.format_exc())
		return None, None


# Language to flag mapping
language_flag_mapping = {
	"ar": "🇸🇦",  # Arabic
	"bg": "🇧🇬",  # Bulgarian
	"cs": "🇨🇿",  # Czech
	"de": "🇩🇪",  # German
	"el": "🇬🇷",  # Greek
	"en": "🇬🇧",  # English
	"es": "🇪🇸",  # Spanish
	"fa": "🇮🇷",  # Persian
	"fr": "🇫🇷",  # French
	"he": "🇮🇱",  # Hebrew
	"hr": "🇭🇷",  # Croatian
	"hu": "🇭🇺",  # Hungarian
	"it": "🇮🇹",  # Italian
	"jp": "🇯🇵",  # Japanese
	"ko": "🇰🇷",  # Korean
	"mk": "🇲🇰",  # Macedonian
	"nl": "🇳🇱",  # Dutch
	"pl": "🇵🇱",  # Polish
	"pt": "🇵🇹",  # Portuguese
	"ro": "🇷🇴",  # Romanian
	"ru": "🇷🇺",  # Russian
	"sk": "🇸🇰",  # Slovak
	"sl": "🇸🇮",  # Slovenian
	"sq": "🇦🇱",  # Albanian
	"sr": "🇷🇸",  # Serbian
	"th": "🇹🇭",  # Thai
	"tr": "🇹🇷",  # Turkish
	"vi": "🇻🇳",  # Vietnamese
	"zh": "🇨🇳",  # Chinese

	# AMERICA
	"argentina": "🇦🇷",  # Argentina
	"bb": "🇧🇧",  # Barbados
	"bm": "🇧🇲",  # Bermuda
	"bq": "🇧🇶",  # Paesi Bassi Caraibici
	"bo": "🇧🇴",  # Bolivia
	"br": "🇧🇷",  # Brasile
	"ca": "🇨🇦",  # Canada
	"cl": "🇨🇱",  # Cile
	"cr": "🇨🇷",  # Costa Rica
	"ec": "🇪🇨",  # Ecuador
	"sv": "🇸🇻",  # El Salvador
	"gd": "🇬🇩",  # Grenada
	"hn": "🇭🇳",  # Honduras
	"vni": "🇻🇮",  # Isole Vergini Americane
	"mx": "🇲🇽",  # Messico
	"pa": "🇵🇦",  # Panama
	"pe": "🇵🇪",  # Perù
	"do": "🇩🇴",  # Repubblica Dominicana
	"sx": "🇸🇽",  # Sint Maarten
	"us": "🇺🇸",  # Stati Uniti
	"uy": "🇺🇾",  # Uruguay
	"ve": "🇻🇪",  # Venezuela

	# AFRICA
	"cv": "🇨🇻",  # Capo Verde
	"eg": "🇪🇬",  # Egitto
	"ke": "🇰🇪",  # Kenya
	"mu": "🇲🇺",  # Mauritius
	"sn": "🇸🇳",  # Senegal
	"sc": "🇸🇨",  # Seychelles
	"za": "🇿🇦",  # Sudafrica
	"zm": "🇿🇲",  # Zambia
	"tz": "🇹🇿",  # Zanzibar (Tanzania)

	# ASIA
	"cn": "🇨🇳",  # Cina
	"ae": "🇦🇪",  # Emirati Arabi Uniti
	"ph": "🇵🇭",  # Filippine
	"jo": "🇯🇴",  # Giordania
	"id": "🇮🇩",  # Indonesia
	"il": "🇮🇱",  # Israele
	"mv": "🇲🇻",  # Maldive
	"lk": "🇱🇰",  # Sri Lanka
	"th": "🇹🇭",  # Thailandia
	"tr": "🇹🇷",  # Turchia
	"vn": "🇻🇳",  # Vietnam
}


CATEGORY_ICONS = {
	_("User Lists"): "user_lists.png",
	_("Continents"): "continents.png",
	_("Countries"): "countries.png",
	_("Categories"): "categories.png",
	_("Top Webcams"): "top_webcams.png",
	_("AMERICAS"): "americas.png",
	_("EUROPE"): "europe.png",
	_("AFRICA"): "africa.png",
}


def get_category_icon(icon_file_name):
	"""
	Return the full file path of a category icon image.
	"""
	plugin_path = dirname(__file__)
	full_path = join(plugin_path, "countries", icon_file_name)
	print("Icon path: %s + %s" % (plugin_path, icon_file_name))
	return full_path


# Loading data
try:
	with open(COUNTRY_CODES_FILE, "r", encoding="utf-8") as f:
		worldcam_data = load(f)
	translations = worldcam_data.get("translations", {})
except Exception as e:
	logger = Logger()
	logger.error("Error loading country codes: " + str(e))
	country_codes = {}
	translations = {}


# Creating the flat map for research
country_map = {}
for lang, countries in translations.items():
	for name, code in countries.items():
		country_map[name.lower()] = code
		country_map[sub(r'\W', '', name.lower())] = code


def get_country_code(country_name):
	"""Find country code with flexible matches"""
	if not country_name or not country_map:
		return None

	# Normalize the input
	name_clean = country_name.strip().lower()
	name_no_punct = sub(r'\W', '', name_clean)

	# Search by accuracy
	return (
		country_map.get(name_clean) or
		country_map.get(name_no_punct) or
		next((code for name, code in country_map.items()
			  if name in name_clean or name_clean in name), None)
	)


# Flag Path Function
def get_flag_path(country_code=None):
	"""
	Find the country code by matching various forms of country names.
	Returns None if no match is found.
	"""
	if not country_code:
		country_code = "en"  # Default

	special_cases = {"ar": "argentina.png", "bm": "bm.png"}
	filename = special_cases.get(country_code, f"{country_code}.png")

	# Routes to check
	paths_to_check = [
		join(resolveFilename(SCOPE_CURRENT_SKIN), "countries", filename),
		join(dirname(__file__), "countries", filename),
		join(dirname(__file__), "pics", "webcam.png")
	]

	# Return the first valid path
	for path in paths_to_check:
		if isfile(path):
			return path

	return paths_to_check[-1]  # Default icon


# # Esempio di utilizzo
# country_name = "Deutschland"
# country_code = get_country_code(country_name)  # Restituisce 'de'
# flag_path = get_flag_path(country_code)  # Restituisce .../countries/de.png


"""
def get_country_code(country_name):
	cleaned_name = country_name.lower()

	# Exact match
	if cleaned_name in country_codes:
		return country_codes[cleaned_name]

	# Match without special characters
	normalized_name = sub(r"[^a-z0-9]", "", cleaned_name)
	for name, code in country_codes.items():
		normalized_key = sub(r"[^a-z0-9]", "", name.lower())
		if normalized_name == normalized_key:
			return code

	# Partial match for longer names
	for name, code in country_codes.items():
		if cleaned_name in name.lower() or name.lower() in cleaned_name:
			return code

	# Match after removing common prefixes/suffixes
	base_name = sub(r"\b(region|province|state|of|the|and)\b", "", cleaned_name).strip()
	for name, code in country_codes.items():
		if base_name in name.lower():
			return code

	return None
"""


class VideoURLHelper:
	MAIN_URL = "https://www.skylinewebcams.com"

	def __init__(self):
		self.logger = Logger()

	def get_video_url(self, url):
		"""
		Extracts the video URL from a webcam page, safely handling errors.
		"""
		self.logger.info("Fetching video URL for: " + url)
		headers = {"User-Agent": "Mozilla/5.0", "Referer": self.MAIN_URL}

		try:
			from . import client
			content = client.request(url, headers=headers)
			if not content:
				self.logger.warning("Empty content received")
				return None

			if isinstance(content, bytes):
				content = content.decode("utf-8", errors="ignore")

			# Search for HLS stream
			hls_match = search(r"source:\s*'livee\.m3u8\?a=([^']+)'", content)
			if hls_match:
				video_id = hls_match.group(1)
				final_url = "https://hd-auth.skylinewebcams.com/live.m3u8?a=" + video_id
				self.logger.info("Found HLS stream: " + final_url)
				return final_url

			# Search for YouTube video
			yt_match = search(r"videoId:\s*'([^']+)'", content)
			if yt_match:
				video_id = yt_match.group(1)
				yt_url = "https://www.youtube.com/watch?v=" + video_id
				self.logger.info("Found YouTube video: " + yt_url)
				return yt_url

		except Exception as e:
			self.logger.error("Error getting video URL: " + str(e))

		self.logger.warning("No video URL found")
		return None


class AspectManager:
	def save_aspect(self):
		"""Save the current aspect ratio settings."""
		try:
			with open("/proc/stb/video/aspect", "r") as f:
				self.old_aspect = f.read().strip()
		except Exception:
			self.old_aspect = None

	def set_aspect(self, aspect="16:9"):
		"""Set a new aspect ratio."""
		try:
			with open("/proc/stb/video/aspect", "w") as f:
				f.write(aspect)
		except Exception:
			pass

	def restore_aspect(self):
		"""Restore the original aspect ratio."""
		if hasattr(self, "old_aspect") and self.old_aspect:
			try:
				with open("/proc/stb/video/aspect", "w") as f:
					f.write(self.old_aspect)
			except Exception:
				pass


# Global variable for the current system language
_current_language = get_system_language()


def set_current_language(lang):
	"""Set the current system language."""
	global _current_language
	_current_language = lang


def get_current_language():
	"""Get the current system language."""
	return _current_language


def check_and_warn_dependencies(logger=None):
	try:
		missing = checkdependencies.check_requirements(logger=logger)
		if missing and logger:
			logger.warning("Missing optional components: %s", ", ".join(missing))
		return missing
	except Exception as e:
		if logger:
			logger.error("Error checking dependencies: %s", str(e))
		return []
