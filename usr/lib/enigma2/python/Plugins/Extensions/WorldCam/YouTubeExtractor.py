#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function
"""
#########################################################
#                                                       #
#  YouTube Video Extractor                              #
#  Version: 2.0                                         #
#  Created by Lululla                                   #
#  License: CC BY-NC-SA 4.0                             #
#  https://creativecommons.org/licenses/by-nc-sa/4.0/   #
#  Last Modified: "00:00 - 20250616"                    #
#                                                       #
#  Credits:                                             #
#  - Original concept by Lululla                        #
#  Usage of this code without proper attribution        #
#  is strictly prohibited.                              #
#  For modifications and redistribution,                #
#  please maintain this credit header.                  #
#########################################################
"""
__author__ = "Lululla"

# import re
import json
import requests
import urllib.parse
# import time
from bs4 import BeautifulSoup
from re import sub, search, IGNORECASE, DOTALL
from .utils import quote


class YouTubeExtractor:
	_YT_INITIAL_PLAYER_RESPONSE_RE = r'ytInitialPlayerResponse\s*=\s*({.+?})\s*;'
	_VIDEO_EXTENSIONS = {
		'18': 'mp4', '22': 'mp4', '37': 'mp4', '38': 'mp4', '43': 'webm',
		'44': 'webm', '45': 'webm', '46': 'webm', '133': 'mp4', '134': 'mp4',
		'135': 'mp4', '136': 'mp4', '137': 'mp4', '138': 'mp4', '139': 'mp4a',
		'140': 'mp4a', '141': 'mp4a', '160': 'mp4', '242': 'webm', '243': 'webm',
		'244': 'webm', '247': 'webm', '248': 'webm', '271': 'webm', '278': 'webm',
		'298': 'mp4', '299': 'mp4', '302': 'webm', '303': 'webm', '308': 'webm',
		'313': 'webm', '315': 'webm', '394': 'mp4', '395': 'mp4', '396': 'mp4',
		'397': 'mp4', '398': 'mp4', '399': 'mp4', '400': 'mp4', '401': 'mp4',
		'hls': 'm3u8'
	}

	def __init__(self, logger=None):
		self.logger = logger
		self.headers = {
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
			'Accept-Language': 'en-US,en;q=0.9',
			'Referer': 'https://www.youtube.com/',
			'Origin': 'https://www.youtube.com'
		}
		# Initialize session with proper headers and retries
		self.session = requests.Session()
		self.session.headers.update(self.headers)
		# Add retry adapter with backoff strategy
		self.session.mount('https://', requests.adapters.HTTPAdapter(
			max_retries=requests.packages.urllib3.util.Retry(
				total=3,
				backoff_factor=0.5,
				status_forcelist=[500, 502, 503, 504]
			)
		))

	def log(self, message, level='info'):
		"""Unified logging with different levels"""
		if self.logger:
			if level == 'error':
				self.logger.error(message)
			elif level == 'warning':
				self.logger.warning(message)
			else:
				self.logger.info(message)
		else:
			print(f"[{level.upper()}] {message}")

	def direct_extraction(self, video_id):
		"""Direct extraction without API"""
		try:
			url = f"https://yewtu.be/latest_version?id={video_id}&itag=22"
			response = self.session.get(url, allow_redirects=True, timeout=10)

			if 200 <= response.status_code < 300:
				return response.url, 'mp4'

		except Exception as e:
			self.log(f"Direct extraction failed: {str(e)}", 'error')

		return None, None

	def direct_fallback(self, video_id):
		"""Direct extraction last resort"""
		try:
			# Try DASH manifest
			dash_url = f"https://www.youtube.com/api/manifest/dash/id/video_{video_id}"
			response = self.session.head(dash_url, allow_redirects=True, timeout=5)

			if response.status_code == 200:
				return dash_url, 'mpd'

			# Try HLS
			hls_url = f"https://www.youtube.com/watch?v={video_id}"
			return hls_url, 'm3u8'

		except Exception as e:
			self.log(f"Direct fallback failed: {str(e)}", 'error')
			return None, None

	def extract_video_id(self, url):
		"""Extract video ID from YouTube URL"""
		# Clean the URL first
		clean_url = self.clean_url(url)
		self.log(f"Cleaned URL: {clean_url}")

		"""Extracts video ID from YouTube URL"""
		patterns = [
			r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([^&]+)',
			r'(?:https?://)?youtu\.be/([^?]+)',
			r'(?:https?://)?(?:www\.)?youtube\.com/embed/([^/?]+)',
			r'(?:https?://)?(?:www\.)?youtube\.com/v/([^/?]+)',
			r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([^/?]+)',
			r'(?:https?://)?(?:www\.)?youtube\.com/live/([^/?]+)'
		]
		for pattern in patterns:
			match = search(pattern, url, IGNORECASE)
			if match:
				return match.group(1)
		self.log(f"No valid video ID found in URL: {url}", 'error')
		return None

	def get_stream_url(self, video_id):
		"""Return direct stream URL for Enigma2 players - ULTIMATE FIX"""
		try:
			# Return proper embed URL for plugin method
			embed_url = f"https://www.youtube.com/embed/{video_id}?autoplay=1"
			self.log(f"Returning plugin URL: {embed_url}", 'info')
			return embed_url, 'plugin', ""
		except Exception as e:
			self.log(f"Stream extraction failed: {str(e)}", 'error')
			# Fallback to standard YouTube URL
			return f"https://www.youtube.com/watch?v={video_id}", 'm3u8', ""

	def _fix_invalid_json(self, json_str):
		"""Alternative approach: Search all scripts"""
		# 1. Removes function calls
		json_str = sub(r'^\s*function\s*\(\)\s*{', '', json_str)
		json_str = sub(r'}\s*\(\)\s*;?\s*$', '', json_str)

		# 2. Fix trailing commas
		json_str = sub(r',\s*([}\]])', r'\1', json_str)

		# 3. Handles unquoted strings
		json_str = sub(r'([\{,])\s*([a-zA-Z0-9_]+)\s*:', r'\1"\2":', json_str)

		# 4. Fix JavaScript values
		json_str = sub(r':\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*([,\}])', r':"\1"\2', json_str)

		# 5. Remove comments
		json_str = sub(r'/\*.*?\*/', '', json_str, flags=DOTALL)

		return json_str

	def get_fallback_stream(self, video_id):
		"""Last attempt at extraction with alternative technique"""
		try:
			# Prova con invidious (instance pubblica)
			response = requests.get(
				f"https://vid.puffyan.us/api/v1/videos/{video_id}",
				timeout=10
			)
			data = response.json()

			# Trova la migliore qualità
			best_format = None
			for fmt in data.get('formatStreams', []) + data.get('adaptiveFormats', []):
				if not best_format or fmt.get('quality', '') > best_format.get('quality', ''):
					best_format = fmt

			if best_format:
				return best_format['url'], best_format['type'].split('/')[-1]

		except Exception as e:
			self.logger.error(f"Fallback extraction failed: {str(e)}")

		return None, None

	def _get_video_info_api(self, video_id):
		"""New version with updated clients and correct parameters"""
		clients = [
			{
				"context": {
					"client": {
						"clientName": "WEB",
						"clientVersion": "2.20240410.01.00",
						"hl": "en",
						"gl": "US"
					}
				}
			},
			{
				"context": {
					"client": {
						"clientName": "ANDROID",
						"clientVersion": "19.09.37",
						"androidSdkVersion": 30,
						"hl": "en",
						"gl": "US"
					}
				}
			},
			{
				"context": {
					"client": {
						"clientName": "TVHTML5_SIMPLY_EMBEDDED_PLAYER",
						"clientVersion": "2.0",
						"hl": "en",
						"gl": "US"
					}
				}
			},
			{
				"context": {
					"client": {
						"clientName": "IOS",
						"clientVersion": "19.09.3",
						"hl": "en",
						"gl": "US"
					}
				}
			}
		]

		api_url = "https://www.youtube.com/youtubei/v1/player"

		for client in clients:
			try:
				payload = {
					"videoId": video_id,
					"contentCheckOk": True,
					"racyCheckOk": True,
					"params": "CgIQBg=="  # Parametro critico
				}
				payload.update(client)

				response = self.session.post(
					api_url,
					json=payload,
					timeout=15
				)
				response.raise_for_status()
				return response.json()
			except Exception as e:
				self.log(f"API request failed with client {client['context']['client']['clientName']}: {str(e)}", 'warning')

		return None

	def _get_headers_str(self, video_id):
		"""Generate headers string for service reference"""
		headers = {
			'User-Agent': self.headers['User-Agent'],
			'Referer': f'https://www.youtube.com/watch?v={video_id}',
			'Origin': 'https://www.youtube.com'
		}
		return "&".join([f"{k}={quote(v)}" for k, v in headers.items()])

	def _extract_formats(self, player_response):
		"""Extracts video formats from player response"""
		formats = []

		# Extracts from streamingData.formats
		streaming_data = player_response.get('streamingData', {})

		for fmt in streaming_data.get('formats', []):
			if 'url' in fmt or 'cipher' in fmt or 'signatureCipher' in fmt:
				formats.append(fmt)

		# Extracts from streamingData.adaptiveFormats
		for fmt in streaming_data.get('adaptiveFormats', []):
			if 'url' in fmt or 'cipher' in fmt or 'signatureCipher' in fmt:
				formats.append(fmt)

		# Extract HLS URL manifest
		hls_manifest = streaming_data.get('hlsManifestUrl')
		if hls_manifest:
			formats.append({
				'url': hls_manifest,
				'mimeType': 'application/vnd.apple.mpegurl',
				'itag': 'hls'
			})

		# Extract DASH URL manifest
		dash_manifest = streaming_data.get('dashManifestUrl')
		if dash_manifest:
			formats.append({
				'url': dash_manifest,
				'mimeType': 'application/dash+xml',
				'itag': 'dash'
			})

		return formats

	def _process_cipher(self, cipher):
		"""Process encrypted URLs"""
		params = dict(urllib.parse.parse_qsl(cipher))
		url = params.get('url', '')
		s = params.get('s', '')
		sp = params.get('sp', 'signature')

		if not url and 'url' in params.get('player_response', {}):
			# Extract URL from embedded player_response
			try:
				player_response = json.loads(params.get('player_response', '{}'))
				url = player_response.get('streamingData', {}).get('formats', [{}])[0].get('url', '')
				if not url:
					url = player_response.get('streamingData', {}).get('adaptiveFormats', [{}])[0].get('url', '')
			except:
				pass

		if s:
			# For now we return the URL as is
			# In a full implementation this is where the decryption would go
			return f"{url}&{sp}={s}"

		return url

	def _select_best_format(self, formats):
		"""Select the best available format"""
		if not formats:
			return None

		# Search for HLS/DASH formats first
		for fmt in formats:
			if fmt.get('itag') in ['hls', 'dash']:
				return fmt

		# Sort by quality
		formats.sort(
			key=lambda f: (
				f.get('width', 0),
				f.get('height', 0),
				f.get('bitrate', 0),
				f.get('fps', 0)
			),
			reverse=True
		)

		return formats[0]

	def get_video_info(self, video_id):
		"""Gets basic video information with fallback"""
		try:
			# First attempt: official API
			api_data = self._get_video_info_api(video_id)
			if api_data:
				details = api_data.get('videoDetails', {})
				return {
					'title': details.get('title', f"Video {video_id}"),
					'thumbnail': details.get('thumbnail', {}).get('thumbnails', [{}])[-1].get('url', ''),
					'duration': int(details.get('lengthSeconds', 0))
				}

			# Second attempt: HTML scraping
			response = self.session.get(
				f"https://www.youtube.com/watch?v={video_id}",
				timeout=10
			)
			response.raise_for_status()

			soup = BeautifulSoup(response.text, 'html.parser')
			title = soup.find('title').text.replace(' - YouTube', '').strip()

			# Get thumbnail
			thumbnail = ""
			thumbnail_tag = soup.find('meta', property='og:image')

			if thumbnail_tag:
				thumbnail = thumbnail_tag.get('content', '')

			return {
				'title': title,
				'thumbnail': thumbnail,
				'duration': 0
			}

		except Exception as e:
			self.log(f"Video info error: {str(e)}", 'error')
			return {
				'title': f"Video {video_id}",
				'thumbnail': '',
				'duration': 0
			}

	def clean_url(self, url):
		"""Clean YouTube URLs by removing invalid characters and parameters"""
		# Remove trailing delimiters
		url = sub(r'#+$', '', url)

		# Extract just the video ID part
		video_id_match = search(r'(?:v=|youtu\.be/|embed/)([a-zA-Z0-9_-]{11})', url)
		if video_id_match:
			return f"https://www.youtube.com/watch?v={video_id_match.group(1)}"

		# Remove invalid parameters
		url = sub(r'\?.*$', '', url)
		return url
