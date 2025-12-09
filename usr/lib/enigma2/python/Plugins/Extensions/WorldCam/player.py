#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

"""
#########################################################
#                                                       #
#  Worldcam Player from Plugin                          #
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

import sys
from os import remove
from os.path import abspath, dirname, exists, join
from re import IGNORECASE, search

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ServiceEventTracker import InfoBarBase, ServiceEventTracker
from Components.config import config
from enigma import eServiceReference, eTimer, iPlayableService, getDesktop
from Screens.InfoBarGenerics import (
	InfoBarAudioSelection,
	InfoBarMenu,
	InfoBarNotifications,
	InfoBarSeek,
	InfoBarSubtitleSupport,
)
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

from . import _
from .scraper import SkylineScraper
from .utils import (
	unquote,
	is_ytdlp_available,
	disable_summary,
	FavoritesManager,
	AspectManager,
	Logger
)

PLUGIN_PATH = dirname(__file__)
screen_width = getDesktop(0).size().width()

yt_dlp_path = "/usr/lib/enigma2/python/Plugins/Extensions/WorldCam/yt_dlp"
if yt_dlp_path not in sys.path:
	sys.path.append(yt_dlp_path)

plugin_dir = dirname(abspath(__file__))
if plugin_dir not in sys.path:
	sys.path.append(plugin_dir)


yt_dlp_subdir = join(plugin_dir, 'yt_dlp')
if yt_dlp_subdir not in sys.path:
	sys.path.append(yt_dlp_subdir)


class TvInfoBarShowHide():
	"""InfoBar show/hide control"""
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

		self.helpOverlay = Label("")
		self.helpOverlay.skinAttributes = [
			("position", "0,0"),
			("size", "1280,50"),
			("font", "Regular;28"),
			("halign", "center"),
			("valign", "center"),
			("foregroundColor", "#FFFFFF"),
			("backgroundColor", "#666666"),
			("transparent", "0"),
			("zPosition", "100")
		]

		self["helpOverlay"] = self.helpOverlay
		self["helpOverlay"].hide()

		self.hideTimer = eTimer()
		try:
			self.hideTimer_conn = self.hideTimer.timeout.connect(
				self.doTimerHide)
		except BaseException:
			self.hideTimer.callback.append(self.doTimerHide)
		self.hideTimer.start(5000, True)
		self.onShow.append(self.__onShow)
		self.onHide.append(self.__onHide)

	def show_help_overlay(self):
		help_text = (
			"OK = Info | CH-/CH+ = Prev/Next | BLUE = Fav | PLAY/PAUSE = Toggle | STOP = Stop | EXIT = Exit"
		)
		self["helpOverlay"].setText(help_text)
		self["helpOverlay"].show()

		self.help_timer = eTimer()
		self.help_timer.callback.append(self.hide_help_overlay)
		self.help_timer.start(5000, True)

	def hide_help_overlay(self):
		self["helpOverlay"].hide()

	def OkPressed(self):
		if self["helpOverlay"].visible:
			self.help_timer.stop()
			self.hide_help_overlay()
		else:
			self.show_help_overlay()
		self.toggleShow()

	def __onShow(self):
		self.__state = self.STATE_SHOWN
		self.startHideTimer()

	def __onHide(self):
		self.__state = self.STATE_HIDDEN

	def serviceStarted(self):
		if self.execing and config.usage.show_infobar_on_zap.value:
			self.doShow()

	def startHideTimer(self):
		if self.__state == self.STATE_SHOWN and not self.__locked:
			self.hideTimer.stop()
			self.hideTimer.start(5000, True)

	def doShow(self):
		self.hideTimer.stop()
		self.show()
		self.startHideTimer()

	def doTimerHide(self):
		self.hideTimer.stop()
		if self.__state == self.STATE_SHOWN:
			self.hide()

	def toggleShow(self):
		if not self.skipToggleShow:
			if self.__state == self.STATE_HIDDEN:
				self.show()
				self.hideTimer.stop()
				self.show_help_overlay()

			else:
				self.hide()
				self.startHideTimer()

				if self["helpOverlay"].visible:
					self.help_timer.stop()
					self.hide_help_overlay()
		else:
			self.skipToggleShow = False

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


class WorldCamPlayer(
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

	def __init__(self, session, webcams, current_index=0):
		Screen.__init__(self, session)
		disable_summary(self)
		self.session = session
		self.skinName = "MoviePlayer"

		# xml_path = join(self.get_skin_path(), "WorldCamPlayer.xml")
		# self.skinName = xml_path
		self.logger = Logger()

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

		self.webcams = webcams
		self.current_index = current_index
		self.state = self.STATE_PLAYING
		self.aspect_manager = AspectManager()
		self.aspect_manager.set_aspect("16:9")
		self.scraper = SkylineScraper()
		self["state"] = Label("")
		self["eventname"] = Label("")
		self["speed"] = Label("")
		self["statusicon"] = Label("")
		self["key_green"] = Label("")
		self["key_yellow"] = Label("")
		self["key_blue"] = Label("")
		self["actions"] = ActionMap(
			[
				"ColorActions", "OkCancelActions",
				"WorldCamPlayer", "MediaPlayerActions",
			],

			{
				"cancel": self.cancel,
				"back": self.cancel,
				"red": self.cancel,

				"prevBouquet": self.previous_webcam,
				"nextBouquet": self.next_webcam,
				"prev": self.previous_webcam,
				"next": self.next_webcam,
				"leavePlayer": self.leavePlayer,
				"stop": self.leavePlayer,
				"blue": self.toggle_favorite,
				"playpauseService": self.playpauseService,
			},
			-2
		)

		self.__event_tracker = ServiceEventTracker(
			screen=self,
			eventmap={
				iPlayableService.evStart: self.__serviceStarted,
				iPlayableService.evEOF: self.__evEOF,
				iPlayableService.evStopped: self.__evStopped,
			}
		)
		self.srefInit = self.session.nav.getCurrentlyPlayingServiceReference()
		self.onClose.append(self.cleanup)
		self.onFirstExecBegin.append(self.start_playback)

	def get_current_webcam(self):
		return self.webcams[self.current_index]

	def next_webcam(self):
		if self.current_index < len(self.webcams) - 1:
			self.current_index += 1
			self.switch_webcam()

	def previous_webcam(self):
		if self.current_index > 0:
			self.current_index -= 1
			self.switch_webcam()

	def switch_webcam(self):
		try:
			self.session.nav.stopService()
			self.start_playback()
		except Exception as e:
			self.logger.error(f"Error switching webcam: {str(e)}")
			self.session.open(
				MessageBox,
				_("Error switching webcam"),
				MessageBox.TYPE_ERROR
			)

	def __serviceStarted(self):
		"""Service started playing"""
		self.logger.info("Playback started successfully")
		self.state = self.STATE_PLAYING

	def toggle_favorite(self):
		"""Add or remove from favorites"""
		current_webcam = self.get_current_webcam()
		if FavoritesManager.is_favorite(current_webcam["url"]):
			success = FavoritesManager.remove_favorite(current_webcam["url"])
			message = _("Removed from favorites") if success else _(
				"Error removing favorite")
		else:
			success = FavoritesManager.add_favorite(
				current_webcam["name"], current_webcam["url"])
			message = _("Added to favorites!") if success else _(
				"Error adding favorite")

		self.session.open(
			MessageBox,
			message,
			MessageBox.TYPE_INFO,
			timeout=3
		)

	def __evEOF(self):
		self.logger.info("Playback completed")
		self.close()

	def __evStopped(self):
		self.logger.info("Playback stopped")
		self.close()

	def leavePlayer(self):
		self.close()

	def cancel(self):
		self.close()

	def start_playback(self):
		try:
			current_webcam = self.get_current_webcam()
			self.logger.info(
				"Starting playback for: {0}".format(current_webcam["name"])
			)
			self.logger.info(
				"URL: {0}".format(current_webcam["url"])
			)

			stream_url = self.scraper.get_stream_url(current_webcam["url"])
			if not stream_url:
				self.logger.error("Could not extract stream URL")
				self.show_error(_("Could not extract video stream"))
				return

			self.logger.info("Stream URL: {0}".format(stream_url))

			if "youtube.com" in stream_url or "youtu.be" in stream_url:
				self.logger.info("Detected YouTube stream")
				self.play_youtube(stream_url, current_webcam["name"])
			else:
				self.logger.info("Detected regular stream")
				self.play_stream(stream_url, current_webcam["name"])

		except Exception as e:
			self.logger.error("Playback error: {0}".format(e))
			self.show_error("Playback error: {0}".format(e))

	def play_youtube(self, url, title):
		"""
		Play YouTube video using optimized methods:
		1. yt-dlp extraction (best quality)
		2. Direct embed method (fallback)
		"""
		try:
			self.logger.info(f"Playing YouTube: {url}")
			self.logger.info(f"Title: {title}")

			# Extract video ID
			video_id = self.extract_video_id(url)
			if not video_id:
				self.logger.error("Could not extract video ID")
				self.show_error(_("Invalid YouTube URL"))
				return

			self.logger.info(f"Video ID: {video_id}")

			# Try methods in order of reliability
			methods = [
				self.play_with_ytdlp,
				self.play_with_direct_embed
			]

			for method in methods:
				try:
					self.logger.info(f"Trying method: {method.__name__}")
					if method(video_id, title):
						self.logger.info("Playback started successfully")
						return
				except Exception as e:
					self.logger.error(f"Method failed: {str(e)}")

			self.show_error(_('All YouTube playback methods failed!'))
		except Exception as e:
			self.logger.error(f"Playback failed: {str(e)}")
			self.show_error(_('Error playing YouTube video!'))

	def play_with_ytdlp(self, video_id, title):
		"""Primary method using yt-dlp for stream extraction"""
		self.logger.info("Trying yt-dlp method")

		YoutubeDL, DownloadError = is_ytdlp_available(logger=self.logger)
		if not YoutubeDL:
			return False

		try:
			# Check validity of cookie file
			cookiefile = "/etc/enigma2/yt_cookies.txt"
			valid_cookiefile = None
			if exists(cookiefile):
				try:
					with open(cookiefile, "r") as f:
						content = f.read()
						if content.count("\t") >= 6:
							self.logger.info("Valid cookie file found")
							valid_cookiefile = cookiefile
						else:
							self.logger.warning(
								"Invalid cookie file format, skipping")
				except Exception as e:
					self.logger.warning(
						"Error reading cookie file: %s", str(e))
			# Configure yt-dlp options
			ydl_opts = {
				"format": "bestvideo[height<=720]+bestaudio/best[height<=720]",
				"quiet": False,
				"logger": self.logger,
				"nocheckcertificate": True,
				"outtmpl": "",
				"cachedir": False,
				"no_warnings": False,
				"ignoreerrors": False,
				"geo_bypass": True,
				"geo_bypass_country": "US",
				"http_headers": {
					"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
					"Referer": "https://www.youtube.com/",
					"Origin": "https://www.youtube.com"},
				"extractor_args": {
					"youtube": {
						"player_client": [
							"android_embedded",
							"web"],
						"player_skip": ["config"]}},
				"force_ipv4": True,
				"verbose": True,
				"compat_opts": ["no-youtube-unavailable-videos"],
			}

			if valid_cookiefile:
				ydl_opts["cookiefile"] = valid_cookiefile

			youtube_url = "https://www.youtube.com/watch?v=%s" % video_id

			with YoutubeDL(ydl_opts) as ydl:
				info = ydl.extract_info(youtube_url, download=False)

				if not info:
					self.logger.error("No video info returned by yt_dlp")
					return False

				if 'url' in info:
					stream_url = info['url']
				elif 'formats' in info:
					formats = [f for f in info['formats'] if f.get('protocol', '').startswith('http')]

					if not formats:
						self.logger.error("No HTTP formats available")
						return False

					compatible_formats = [
						f for f in formats
						if not f.get('acodec', 'none') == 'none'
						and not f.get('vcodec', 'none') == 'none'
					]

					if not compatible_formats:
						compatible_formats = formats

					compatible_formats.sort(
						key=lambda f: f.get(
							'height', 0), reverse=True)
					best_format = compatible_formats[0]
					stream_url = best_format['url']

					self.logger.info(
						f"Selected format: {best_format['format_id']} ({best_format.get('width', 0)}x{best_format.get('height', 0)})")
				else:
					self.logger.error("No playable formats found")
					return False

				self.logger.info(f"Stream URL: {stream_url[:200]}...")

				# Determine service type
				if '.m3u8' in stream_url.lower():
					service_type = 5001  # HLS
					self.logger.info("Detected HLS stream")
				else:
					service_type = 4097  # HTTP
					self.logger.info("Detected HTTP stream")

				service = eServiceReference(service_type, 0, stream_url)
				service.setName(title)
				self.start_service_playback(service)
				return True

		except DownloadError as e:
			self.logger.error(f"yt-dlp download error: {str(e)}")
			return False
		except Exception as e:
			self.logger.error(f"yt-dlp processing error: {str(e)}")
			return False

	def play_with_direct_embed(self, video_id, title):
		"""Fallback method using direct embed URL"""
		try:
			self.logger.info("Trying direct embed method")
			url = f"https://www.youtube.com/embed/{video_id}"

			# Create headers string
			headers = (
				"User-Agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36&"
				f"Referer=https://www.youtube.com/embed/{video_id}&"
				"Origin=https://www.youtube.com")

			service = eServiceReference(4097, 0, f"{url}|{headers}")
			service.setName(title)
			self.start_service_playback(service)
			return True
		except Exception as e:
			self.logger.error(f"Direct embed method failed: {str(e)}")
			return False

	def extract_video_id(self, url):
		"""Extracts video ID from YouTube URL"""
		try:
			decoded_url = unquote(url)
			patterns = [
				r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([^&]+)',
				r'(?:https?://)?youtu\.be/([^?]+)',
				r'(?:https?://)?(?:www\.)?youtube\.com/embed/([^/?]+)',
				r'(?:https?://)?(?:www\.)?youtube\.com/v/([^/?]+)',
				r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([^/?]+)',
				r'(?:https?://)?(?:www\.)?youtube\.com/live/([^/?]+)',
			]

			for pattern in patterns:
				match = search(pattern, decoded_url, IGNORECASE)
				if match:
					return match.group(1)

			return None
		except Exception as e:
			self.logger.error(f"URL decoding failed: {str(e)}")
			return None

	def start_service_playback(self, service):
		"""Start playback with special handling"""
		if self.session.nav.getCurrentlyPlayingServiceReference():
			self.session.nav.stopService()

		self.session.nav.playService(service)
		self.show()
		self.state = self.STATE_PLAYING
		if self.state == self.STATE_PLAYING:
			self.show_help_overlay()

	def play_stream(self, stream_url, title=""):
		"""
		Play a media stream based on the given URL
		"""
		try:
			# Convert to string if needed
			if isinstance(stream_url, (tuple, list)):
				stream_url = str(stream_url[0])
			else:
				stream_url = str(stream_url)

			self.logger.info(f"Final stream URL: {stream_url[:200]}...")

			# Determine service type
			if '.m3u8' in stream_url.lower() or stream_url.lower().startswith('http'):
				service_type = 5001  # HLS
			else:
				service_type = 4097  # HTTP

			service = eServiceReference(service_type, 0, stream_url)
			service.setName(title)
			self.start_service_playback(service)
			self.logger.info("Playback started successfully")

		except Exception as e:
			self.logger.error(f"Error playing stream: {str(e)}")
			self.show_error(_('Playback failed!'))

	def playpauseService(self):
		"""Toggle play/pause"""
		service = self.session.nav.getCurrentService()
		if not service:
			self.logger.warning("No current service")
			return

		pauseable = service.pause()
		if pauseable is None:
			self.logger.warning("Service is not pauseable")
			# Instead of failing, just stop and restart the service
			if self.state == self.STATE_PLAYING:
				current_ref = self.session.nav.getCurrentlyPlayingServiceReference()
				if current_ref:
					self.session.nav.stopService()
					self.state = self.STATE_PAUSED
					self.logger.info("Playback stopped (pause not supported)")
			elif self.state == self.STATE_PAUSED:
				current_ref = self.session.nav.getCurrentlyPlayingServiceReference()
				if current_ref:
					self.session.nav.playService(current_ref)
					self.state = self.STATE_PLAYING
					self.logger.info("Playback resumed (pause not supported)")
			return

		try:
			if self.state == self.STATE_PLAYING:
				if hasattr(pauseable, 'pause'):
					pauseable.pause()
					self.state = self.STATE_PAUSED
					self.logger.info("Playback paused")
			elif self.state == self.STATE_PAUSED:
				if hasattr(pauseable, 'play'):
					pauseable.play()
					self.state = self.STATE_PLAYING
					self.logger.info("Playback resumed")
		except Exception as e:
			self.logger.error(f"Play/pause error: {str(e)}")
			self.show_error(_("Play/pause not supported for this stream"))

	def show_error(self, message):
		"""Show error message and close player"""
		self.session.openWithCallback(
			self.close,
			MessageBox,
			message,
			MessageBox.TYPE_ERROR
		)

	def cleanup(self):
		"""Cleanup resources on close"""
		if exists('/tmp/hls.avi'):
			try:
				remove('/tmp/hls.avi')
			except BaseException:
				pass

		self.aspect_manager.restore_aspect()
		self.session.nav.stopService()

		if self.srefInit:
			try:
				self.session.nav.playService(self.srefInit)
			except BaseException:
				pass
