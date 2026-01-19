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
import subprocess
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
    # is_ytdlp_available,
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
            ["InfobarShowHideActions"],
            {
                "toggleShow": self.OkPressed,
                "hide": self.hide
            },
            0
        )
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
            "OK = Info | CH-/CH+ = Prev/Next | BLUE = Fav | PLAY/PAUSE = Toggle | STOP = Stop | EXIT = Exit | by Lululla"
        )
        self["helpOverlay"].setText(help_text)
        self["helpOverlay"].show()

        if not hasattr(self, 'help_timer'):
            self.help_timer = eTimer()
            self.help_timer.callback.append(self.hide_help_overlay)

        self.help_timer.start(5000, True)

    def hide_help_overlay(self):
        if self["helpOverlay"].visible:
            self["helpOverlay"].hide()

    def OkPressed(self):
        if self.__state == self.STATE_SHOWN:
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

    def doShow(self):
        self.hideTimer.stop()
        self.show()
        self.startHideTimer()

    def doHide(self):
        self.hideTimer.stop()
        self.hide()
        if self["helpOverlay"].visible:
            self.help_timer.stop()
            self.hide_help_overlay()
        self.startHideTimer()

    def serviceStarted(self):
        if self.execing and config.usage.show_infobar_on_zap.value:
            self.doShow()

    def startHideTimer(self):
        if self.__state == self.STATE_SHOWN and not self.__locked:
            self.hideTimer.stop()
            self.hideTimer.start(5000, True)

    def doTimerHide(self):
        self.hideTimer.stop()
        if self.__state == self.STATE_SHOWN:
            self.hide()
            if self["helpOverlay"].visible:
                self.help_timer.stop()
                self.hide_help_overlay()

    def toggleShow(self):
        if not self.skipToggleShow:
            if self.__state == self.STATE_HIDDEN:
                self.doShow()
                self.show_help_overlay()
            else:
                self.doHide()
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


class WorldCamPlayer(InfoBarBase, InfoBarMenu, InfoBarSeek, InfoBarAudioSelection, InfoBarSubtitleSupport, InfoBarNotifications, TvInfoBarShowHide, Screen):
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
                "ColorActions",
                "OkCancelActions",
                "WorldCamPlayer",
                "MediaPlayerActions",
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
            self.logger.error("Error switching webcam: " + str(e))
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

            # Check if it's YouTube
            url = current_webcam["url"]
            stream_url = self.scraper.get_stream_url(url)
            if not stream_url:
                self.logger.error("Could not extract stream URL")
                self.show_error(_("Could not extract video stream"))
                return

            self.logger.info("Stream URL: {0}".format(stream_url))

            if "youtube.com" in url or "youtu.be" in url:
                self.logger.info("Detected YouTube stream")
                self.play_youtube(url, current_webcam["name"])
            else:
                # For other streams
                self.logger.info("Stream URL extracted")
                self.play_stream(stream_url, current_webcam["name"])

        except Exception as e:
            self.logger.error("Playback error: " + str(e))
            self.show_error(_("Playback error"))

    def play_youtube(self, url, title):
        """
        Main YouTube playback method
        """
        try:
            self.logger.info("[YouTube Playback] Starting for: " + title)
            # Extract video ID
            video_id = self.extract_video_id(url)
            if not video_id:
                self.logger.error("Could not extract video ID")
                self.show_error(_("Invalid YouTube URL"))
                return False

            self.logger.info("Video ID: " + video_id)

            # Try to find yt-dlp
            ytdlp_path = self.find_ytdlp()
            if not ytdlp_path:
                self.logger.error("yt-dlp not found")
                self.show_error(_("yt-dlp not found. Please install it."))
                return False

            # Extract stream URL using yt-dlp
            stream_url = self.get_stream_with_ytdlp(ytdlp_path, video_id)
            if not stream_url:
                self.logger.error("Failed to extract stream URL")
                self.show_error(_("Could not extract YouTube stream"))
                return False

            # Play the stream
            self.logger.info("Playing extracted stream")
            self.play_stream(stream_url, title)
            return True
        except Exception as e:
            self.logger.error("YouTube playback error: " + str(e))
            self.show_error(_("YouTube playback error"))
            return False

    def find_ytdlp(self):
        """
        Find yt-dlp executable
        """
        ytdlp_paths = [
            "/usr/bin/yt-dlp",
            "/usr/local/bin/yt-dlp",
            "/usr/lib/enigma2/python/Plugins/Extensions/WorldCam/yt_dlp/yt-dlp",
            PLUGIN_PATH + "/yt_dlp/yt-dlp",
        ]

        for path in ytdlp_paths:
            try:
                if exists(path):
                    # Test if it works
                    cmd = [path, "--version"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        self.logger.info("Found working yt-dlp at: " + path)
                        return path
            except:
                continue

        self.logger.error("No working yt-dlp found")
        return None

    def get_url_type(self, url):
        """
        Determine type of URL for logging
        """
        url_lower = url.lower()
        if ".mp4" in url_lower:
            return "MP4"
        elif ".m3u8" in url_lower:
            return "HLS"
        elif "googlevideo.com/videoplayback" in url:
            return "Direct Google Video"
        elif "manifest.googlevideo.com" in url:
            return "YouTube Manifest"
        else:
            return "Unknown"

    def get_stream_with_ytdlp(self, ytdlp_path, video_id):
        """
        Get stream URL using yt-dlp with various format options
        """
        youtube_url = "https://www.youtube.com/watch?v=" + video_id

        # Format options in order of preference
        # MP4 formats are most compatible with Enigma2
        format_options = [
            ["-g", "-f", "18"],                             # MP4 360p (most compatible)
            ["-g", "-f", "best[ext=mp4]"],                  # Best MP4
            ["-g", "-f", "22/37"],                          # MP4 720p/1080p
            ["-g", "-f", "best[protocol!=m3u8_native]"],    # Avoid HLS
            ["-g", "-f", "best"],                           # Any format
        ]

        for fmt in format_options:
            cmd = [ytdlp_path] + fmt + [youtube_url]
            self.logger.info("Trying: " + " ".join(cmd))

            try:
                # Run yt-dlp with timeout
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    stream_url = result.stdout.strip()

                    # Check if we got a valid URL
                    if stream_url and stream_url.startswith(("http://", "https://")):
                        self.logger.info("Successfully extracted stream URL")
                        self.logger.debug("URL type: " + self.get_url_type(stream_url))
                        return stream_url
                else:
                    # Log error but continue trying other formats
                    error_msg = result.stderr[:100] if result.stderr else "Unknown error"
                    self.logger.warning("Format failed: " + error_msg)

            except subprocess.TimeoutExpired:
                self.logger.warning("Timeout for format: " + " ".join(fmt))
                continue
            except Exception as e:
                self.logger.warning("Error for format: " + str(e))
                continue

        return None

    def extract_video_id(self, url):
        """
        Extract video ID from YouTube URL
        """
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
            self.logger.error("URL decoding failed: " + str(e))
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

            self.logger.info("Final stream URL: " + stream_url[:200] + "...")

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
            self.logger.error("Error playing stream: " + str(e))
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
            self.logger.error("Play/pause error: " + str(e))
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
