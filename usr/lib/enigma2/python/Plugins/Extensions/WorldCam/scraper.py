#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

"""
#########################################################
#														#
#  Worldcam Cam Scraper from Plugin						#
#  Completely rewritten and optimized in version *5.0*	#
#  Version: 5.8											#
#  Created by Lululla (https://github.com/Belfagor2005) #
#  License: CC BY-NC-SA 4.0								#
#  https://creativecommons.org/licenses/by-nc-sa/4.0	#
#  Last Modified: "18:30 - 20250703"					#
#														#
#  Credits:												#
#  - Original concept Lululla							#
#  Usage of this code without proper attribution		#
#  is strictly prohibited.								#
#  For modifications and redistribution,				#
#  please maintain this credit header.					#
#########################################################
"""

__author__ = "Lululla"

from enigma import eTimer
from re import search, escape, findall, DOTALL, IGNORECASE, sub
from os import listdir
from os.path import (
	exists,
	isfile,
	join,
)

from .utils import (
	Logger,
	Request,
	HTTPError,
	URLError,
	urlopen,
	# clean_html_entities
	# quote,
	# urlparse,
	# urlunparse,
	# safe_encode_url
)

try:
	unicode
except NameError:
	unicode = str


BASE_URL = "https://www.skylinewebcams.com"

"""

1. **WorldCamContinentScreen**
   * `self.scraper.get_continents()
   *  get_countries_by_continent

2. **WorldCamCountryScreen**
   * `self.scraper.get_countries()`

3. **WorldCamCategoryScreen**
   * `self.scraper.get_categories()`

4. **WorldCamTopScreen**
   * `self.scraper.get_top_webcams()`

5. **WorldCamLocationScreen**
   * `self.scraper.get_locations(self.country["url"])`

6. **WorldCamWebcamScreen**
   * `self.scraper.get_webcams(self.location["url"])`

7. **WorldCamLocal**
   * `self.scraper.get_local_playlists(playlists_path)
"""


def safe_log_string(text):
	"""Safely encode strings for logging"""
	if isinstance(text, unicode):
		return text.encode('utf-8', 'replace')
	return text


class SkylineScraper:
	"""
	A scraper class for extracting webcam streams and related information
	from skylinewebcams.com, supporting caching and multi-language.
	"""

	BASE_URL = "https://www.skylinewebcams.com"
	HEADERS = {"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en;q=0.5"}

	def __init__(self, lang="en"):
		"""
		Initialize scraper with language and setup cache and timer.
		"""
		self.logger = Logger()
		self.logger.info("Entering __init__")
		self.lang = lang
		self.cache = {}

		self.timer = eTimer()
		self.timer.callback.append(self.clear_cache)
		self.timer.start(3600000)  # Clear cache every hour (3600000 ms)

	def clear_cache(self):
		"""Clear the internal content cache."""
		self.logger.info("Entering clear_cache")
		self.cache = {}

	def get_full_url(self, path):
		"""
		Return a full absolute URL with proper formatting
		"""
		self.logger.info("Entering get_full_url with path: " + path)

		if path.startswith("http"):
			return path

		# Handle relative paths correctly
		if path.startswith("//"):
			return "https:" + path

		# Handle absolute paths
		if path.startswith("/"):
			return self.BASE_URL + path

		# Handle relative paths
		return self.BASE_URL + "/" + path

	def is_direct_stream(self, url):
		"""Check if URL is a direct video stream"""
		video_extensions = ['.m3u8', '.mp4', '.m4v', '.flv', '.ts', '.mov', '.mkv']
		url_lower = url.lower()
		return (any(url_lower.endswith(ext) for ext in video_extensions) or 
				'm3u8' in url_lower or 
				'mp4' in url_lower or
				'stream' in url_lower or
				'explore.org' in url_lower)

	def get_stream_url(self, webcam_page_url):
		"""
		Extract the streaming URL from a webcam page.
		"""
		self.logger.info("Entering get_stream_url")
		try:
			# Case 1: URL is already a direct stream
			if self.is_direct_stream(webcam_page_url):
				self.logger.info("URL is already a direct stream, returning as is")
				return webcam_page_url
				
			# Case 2: YouTube URL
			if 'youtube.com' in webcam_page_url or 'youtu.be' in webcam_page_url:
				self.logger.info("Detected direct YouTube URL, returning as is")
				return webcam_page_url
				
			# Case 3: Explore.org direct stream (specific pattern)
			if 'explore.org' in webcam_page_url and 'm3u8' in webcam_page_url:
				self.logger.info("Detected explore.org direct stream URL")
				return webcam_page_url
				
			# Otherwise proceed with the analysis of the SkylineWebcams page
			content = self.fetch(webcam_page_url, use_cache=False)
			if not content:
				self.logger.warning("No content fetched for URL: " + webcam_page_url)
				return None
				
			# Pattern 1: Standard HLS stream
			hls_match = search(r"source:\s*'livee\.m3u8\?a=([^']+)'", content)
			if hls_match:
				video_id = hls_match.group(1)
				self.logger.info("Found HLS livee.m3u8 stream with video ID: " + video_id)
				return "https://hd-auth.skylinewebcams.com/live.m3u8?a=" + video_id

			# Pattern 2: YouTube video ID
			yt_match = search(r"videoId:\s*'([^']+)'", content)
			if yt_match:
				video_id = yt_match.group(1)
				stream_url = "https://www.youtube.com/watch?v=" + video_id
				self.logger.info(f"Returning YouTube URL: {stream_url}")
				return stream_url

			# Pattern 3: JW Player file URL
			jw_match = search(r'player\.setup\({.*?file:\s*"([^"]+)"', content, DOTALL)
			if jw_match:
				self.logger.info("Found JW Player file URL")
				return jw_match.group(1)

			# Pattern 4: New HLS format
			hls_match2 = search(r"hls:\s*'([^']+)'", content)
			if hls_match2:
				self.logger.info("Found new HLS format URL")
				return hls_match2.group(1)

			# Pattern 5: Direct video source from <video> tag
			video_match = search(r'<video[^>]+src="([^"]+)"', content)
			if video_match:
				url = self.get_full_url(video_match.group(1))
				self.logger.info("Found direct video source: " + url)
				return url

			self.logger.warning("No stream URL found in the page: " + webcam_page_url)
		except Exception as e:
			self.logger.error("Error parsing stream URL from {}: {}".format(webcam_page_url, str(e)))
		return None

	def fetch(self, url, use_cache=True):
		"""
		Fetch the content of the URL with enhanced encoding handling
		"""
		self.logger.info("Entering fetch for URL: " + str(url))

		safe_url = str(url)

		if use_cache and safe_url in self.cache:
			self.logger.info("Using cached content for: " + safe_url)
			return self.cache[safe_url]

		self.logger.info(f"Fetching URL: {safe_url}")

		try:
			req = Request(safe_url, headers=self.HEADERS)
			response = urlopen(req, timeout=15)

			if response is None:
				self.logger.error("No response received for URL: " + safe_url)
				return ""

			content = response.read()
			if not content:
				self.logger.error("Empty response body for URL: " + safe_url)
				return ""

			try:
				decoded_content = content.decode("utf-8", errors="replace")
			except Exception as e:
				self.logger.error(f"Exception Unexpected error: {str(e)}")
				try:
					decoded_content = content.decode("latin-1")
				except:
					decoded_content = content.decode("utf-8", errors="ignore")

			if use_cache:
				self.cache[safe_url] = decoded_content
				self.logger.info("Cached content for URL: " + safe_url)

			return decoded_content

		except (HTTPError, URLError) as e:
			self.logger.error(f"Fetch error: {str(e)}")
		except Exception as e:
			self.logger.error(f"Unexpected error: {str(e)}")

		return ""

	@staticmethod
	def parse_countries(html, language="en"):
		"""
		Extract country links and names from the main page.
		"""
		Logger().info("Entering parse_countries")  # static method: use fresh Logger
		pattern = r'<a href="(/' + escape(language) + r'/webcam/[^"]+\.html)">([^<]+)</a>'
		try:
			result = findall(pattern, html, IGNORECASE)
			Logger().info("Found {} countries".format(len(result)))
			return result
		except Exception as e:
			Logger().error("Error parsing countries: " + str(e))
			return []

	@staticmethod
	def parse_categories(html, language="en"):
		"""
		Extract main categories from homepage HTML.
		"""
		Logger().info("Entering parse_categories")
		pattern = r'<a href="(/' + escape(language) + r'/[^"]+)"[^>]*>\s*<p class="tcam">([^<]+)</p>'
		try:
			result = findall(pattern, html)
			Logger().info("Found {} categories".format(len(result)))
			return result
		except Exception as e:
			Logger().error("Error parsing categories: " + str(e))
			return []

	@staticmethod
	def parse_top_webcams(html, language="en", base_url=None, fetch_func=None, parse_func=None, logger=None):
		"""
		Parse top webcams with pagination support (static)
		"""
		if logger:
			logger.info("Entering parse_top_webcams")

		webcams = []
		if parse_func:
			webcams = parse_func(html, escape(language), base_url)

		pagination_pattern = r'<a href="(/' + escape(language) + r'/top-webcams-(\d+)\.html)"'
		pagination_matches = findall(pagination_pattern, html, IGNORECASE)

		for url, page_num in pagination_matches:
			full_url = base_url + url
			if logger:
				logger.info(f"Processing top webcams page {page_num}: {full_url}")
			if fetch_func:
				page_content = fetch_func(full_url)
				if page_content and parse_func:
					webcams.extend(parse_func(page_content, language, base_url))

		if logger:
			logger.info(f"Total top webcams found: {len(webcams)}")
		return webcams

	@staticmethod
	def parse_webcams(html, language="en", base_url="https://www.skylinewebcams.com"):
		Logger().info("Entering parse_webcams")
		webcams = []
		
		# Improved pattern to capture all webcam entries
		pattern = (
			r'<a\s+href="([^"]+)"\s+class="[^"]*col-xs-12[^"]*col-sm-6[^"]*col-md-4[^"]*"[^>]*>'
			r'.*?<img\s+src="([^"]+)"[^>]*alt="([^"]*)"[^>]*>'
			r'.*?<p\s+class="tcam">(.*?)</p>'
			r'.*?<p\s+class="subt">(.*?)</p>'
		)
		
		matches = findall(pattern, html, DOTALL)
		Logger().info(f"Found {len(matches)} webcam matches")
		
		for match in matches:
			href = match[0]
			thumbnail = match[1]
			alt = match[2]
			name = match[3].strip()
			description = match[4].strip()
			
			# Skip ads and invalid entries
			if "Advertisement" in name or not href:
				continue
				
			# Build full URL
			if href.startswith('http'):
				full_url = href
			else:
				full_url = base_url + (href if href.startswith('/') else '/' + href)
				
			webcams.append({
				"url": full_url,
				"thumbnail": thumbnail,
				"alt": alt,
				"name": name,
				"description": description
			})
		
		# Fallback for different formats
		if not webcams:
			Logger().info("Using fallback parsing method")
			# ... [keep your existing fallback logic] ...
		
		Logger().info(f"Returning {len(webcams)} valid webcams")
		return webcams

	@staticmethod
	def parse_locations(html, language="en", country_code=None):
		Logger().info("Entering parse_locations")
		locations = []

		# Primary pattern for location buttons
		location_pattern = r'<a href="([^"]+)" class="[^"]*\bbtn\b[^"]*\bbtn-primary\b[^"]*"[^>]*>([^<]+)</a>'
		
		# Webcam grid fallback pattern
		webcam_pattern = (
			r'<a href="([^"]+)" class="[^"]*col-xs-12[^"]*col-sm-6[^"]*col-md-4[^"]*"[^>]*>'
			r'.*?<div class="cam-light">'
		)

		try:
			# Extract locations from buttons
			location_matches = findall(location_pattern, html)
			for href, name in location_matches:
				locations.append((href, name))
				Logger().info(f"Location found: {name} -> {href}")

			# If no buttons found, fallback to extracting from webcam grid
			if not locations:
				webcam_matches = findall(webcam_pattern, html, DOTALL)
				for href in webcam_matches:
					# Extract location name from URL
					parts = href.split('/')
					if len(parts) >= 5:
						name = parts[4].replace('.html', '').replace('-', ' ').title()
						locations.append((href, name))
						Logger().info(f"Fallback location: {name} -> {href}")

			return locations

		except Exception as e:
			Logger().error(f"Error parsing locations: {str(e)}")
			return []

	@staticmethod
	def parse_local_playlist_file(path):
		"""
		Parse playlist file with flexible format.
		"""
		logger = Logger()
		webcams = []

		if not exists(path):
			logger.error(f"Playlist file not found: {path}")
			return webcams

		try:
			with open(path, "r") as f:
				for line in f:
					line = line.strip()
					if not line or line.startswith("#"):
						continue

					# New: Flexible parsing for different formats
					if "###" in line:
						parts = line.split("###")
						parts = [p.strip() for p in parts if p.strip()]

						if len(parts) >= 2:
							# Last part is always the URL
							# url = parts[-1]
							url = parts[-1].replace("###", "").strip()

							# Name is everything before the URL
							name = " ".join(parts[:-1])

							# Clean YouTube URLs
							if "youtube.com" in url or "youtu.be" in url:
								# Remove any "URL:" text and trailing delimiters
								# url = sub(r'(URL:)|(###)', '', url, flags=IGNORECASE)
								url = sub(r'URL:\s*', '', url, flags=IGNORECASE).strip()
								# Extract just the video ID
								match = search(r'(?:v=|youtu\.be/|embed/)([a-zA-Z0-9_-]{11})', url)
								if match:
									url = f"https://www.youtube.com/watch?v={match.group(1)}"

							webcams.append({
								"group": "User List",
								"name": name,
								"url": url
							})
							continue

					# Traditional formats with three parts separated by various delimiters
					if ":::" in line:
						parts = line.split(":::", 2)
					elif ";;" in line:
						parts = line.split(";;", 2)
					elif "::" in line:
						parts = line.split("::", 2)
					elif ";" in line:
						parts = line.split(";", 2)
					else:
						continue

					if len(parts) >= 3:
						webcams.append({
							"group": parts[0].strip(),
							"name": parts[1].strip(),
							"url": parts[2].strip()
						})
					elif len(parts) == 2:
						webcams.append({
							"group": "User List",
							"name": parts[0].strip(),
							"url": parts[1].strip()
						})
					else:
						logger.warning(f"Skipping line: {line}")

			logger.info(f"Parsed {len(webcams)} webcams from {path}")
			return webcams

		except Exception as e:
			logger.error(f"Error parsing playlist {path}: {str(e)}")
			return []

	@staticmethod
	def _parse_text_playlist(content, logger=None):
		"""
		Parse playlist content supporting multiple formats.
		"""
		channels = []
		lines = content.splitlines()
		line_count = 0

		for line in lines:
			line = line.strip()
			line_count += 1

			if not line or line.startswith('#'):
				continue

			# Support different separators
			separators = ['###', '|', ';', ',']
			parts = None

			for sep in separators:
				if sep in line:
					parts = line.split(sep, 2)
					break

			if not parts:
				parts = [line]

			# Extract data fields
			name = "Unknown"
			url = ""
			logo = ""

			if len(parts) >= 2:
				name = parts[0].strip()
				url = parts[1].strip()
				if len(parts) > 2:
					logo = parts[2].strip()
			elif len(parts) == 1:
				url = parts[0].strip()

			if not url:
				if logger:
					logger.warning(f"Invalid line {line_count}: Missing URL")
				continue

			channels.append({
				'name': name,
				'url': url,
				'type': 'stream',
				'logo': logo
			})

		if logger:
			logger.info(f"Parsed {len(channels)} channels from playlist")
		return channels

	def get_continents(self):
		"""
		Get continents from the main page.
		"""
		self.logger.info("Entering get_continents")
		url = self.BASE_URL + "/" + self.lang
		html = self.fetch(url)
		continents = []

		continent_pattern = r'<div class="continent\s+(\w+)"><strong>([^<]+)</strong></div>(.*?)</div>\s*</div>'
		country_pattern = r'<a href="(/' + self.lang + r'/webcam/[^"]+\.html)">([^<]+)</a>'

		try:
			matches = findall(continent_pattern, html, DOTALL | IGNORECASE)
			for match in matches:
				continent_class = match[0]
				continent_name = match[1]
				continent_html = match[2]

				countries = []
				country_matches = findall(country_pattern, continent_html, IGNORECASE)
				for path, name in country_matches:
					full_url = self.BASE_URL + path
					countries.append({"name": name, "url": full_url})

				continents.append({
					"name": continent_name,
					"class": continent_class,
					"countries": sorted(countries, key=lambda c: c["name"].lower())
				})
			return continents
		except Exception as e:
			self.logger.error("Error in get_continents: " + str(e))
			return []

	def get_countries_by_continent(self, continent_url=None):
		"""
		Get countries for a specific continent
		"""
		Logger().info(f"Entering get_countries_by_continent: {continent_url}")
		html = self.fetch(continent_url)
		countries = []

		# Pattern to find country links
		country_pattern = r'<a href="(/' + self.lang + r'/webcam/[^"]+\.html)">([^<]+)</a>'
		try:
			matches = findall(country_pattern, html, IGNORECASE)
			for path, name in matches:
				full_url = self.BASE_URL + path
				countries.append({"name": name, "url": full_url})
			return sorted(countries, key=lambda c: c["name"].lower())
		except Exception as e:
			Logger().info("Error in get_countries_by_continent: " + str(e))
			return []

	def get_countries(self, category_url=None):
		"""
		Get countries from a category page or homepage.
		"""
		self.logger.info("Entering get_countries")
		url = category_url or self.BASE_URL
		html = self.fetch(url)
		countries = []
		try:
			for path, name in self.parse_countries(html, self.lang):
				full_url = self.BASE_URL + path
				self.logger.info("Country found: {} -> {}".format(name, full_url))
				countries.append({"name": name, "url": full_url})
		except Exception as e:
			self.logger.error("Error in get_countries: " + str(e))
		return countries

	def get_categories(self):
		"""
		Get main categories from homepage.
		"""
		self.logger.info("Entering get_categories")
		html = self.fetch(self.BASE_URL + "/" + self.lang)

		categories = []
		try:
			for path, name in self.parse_categories(html, self.lang):
				full_url = self.BASE_URL + path
				self.logger.info("Category found: {} -> {}".format(name, full_url))
				categories.append({"name": name, "url": full_url})
		except Exception as e:
			self.logger.error("Error in get_categories: " + str(e))
		return categories

	def get_top_webcams(self):
		"""Get featured webcams from the homepage."""
		self.logger.info("Entering get_top_webcams")
		url = self.BASE_URL + "/" + self.lang + "/top-live-cams.html"
		html = self.fetch(url)
		
		if not html:
			self.logger.error("Failed to fetch top webcams page")
			return []

		try:
			# Use the same parsing method as regular webcams
			webcams = self.parse_webcams(html, self.lang, self.BASE_URL)
			"""
			# webcams = self.parse_top_webcams(
				# html,
				# language=self.lang,
				# base_url=self.BASE_URL,
				# fetch_func=self.fetch,
				# parse_func=self.parse_webcams,
				# logger=self.logger
			# )
			"""
			# Filter out any invalid entries
			valid_webcams = [
				w for w in webcams
				if w.get("name") and w.get("url") and "Advertisement" not in w["name"]
			]
			
			self.logger.info(f"Found {len(valid_webcams)} valid top webcams")
			return valid_webcams
		except Exception as e:
			self.logger.error("Error in get_top_webcams: " + str(e))
			return []

	def get_locations(self, country_url=None):
		"""
		Fetch and parse the list of locations for a given country URL.
		"""
		self.logger.info(f"Processing country: {country_url}")
		content = self.fetch(country_url)
		self.logger.info(f"Country page length: {len(content)}")

		locations = []
		location_data = self.parse_locations(content, self.lang)

		for url, name in location_data:
			full_url = self.get_full_url(url)
			locations.append({
				"name": name,
				"url": full_url
			})

		self.logger.info(f"Loaded {len(locations)} locations")
		return locations

	def get_local_playlists(self, playlists_path=None):
		"""
		Return list of filenames in playlists directory.
		"""
		self.logger.info("Entering get_local_playlists for path: " + playlists_path)
		user_lists = []

		if not exists(playlists_path):
			self.logger.error(f"Playlists directory not found: {playlists_path}")
			return user_lists

		try:
			for filename in listdir(playlists_path):
				full_path = join(playlists_path, filename)
				if isfile(full_path) and filename.lower().endswith(('.txt', '.m3u', '.list')):
					user_lists.append(filename)
			return user_lists
		except Exception as e:
			self.logger.error(f"Error reading playlists directory: {str(e)}")
			return user_lists

	def get_webcams(self, page_url=None):
		"""
		Ottiene le webcam per una pagina usando il nuovo parser robusto
		"""
		self.logger.info(f"Processing page: {page_url}")
		html = self.fetch(page_url)
		
		if not html:
			self.logger.error("Failed to fetch page content")
			return []
		
		return self.parse_webcams(html, self.lang, self.BASE_URL)
