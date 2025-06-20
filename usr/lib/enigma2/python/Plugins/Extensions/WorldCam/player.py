#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function
"""
#########################################################
#                                                       #
#  Worldcam Cam Player from Plugin                      #
#  Completely rewritten and optimized in version *5.0*  #
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

import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from os import remove
from os.path import abspath, dirname, exists, join
from re import IGNORECASE, search
from time import sleep
import time
import subprocess
import requests

from Components.ActionMap import ActionMap
from Components.ServiceEventTracker import InfoBarBase, ServiceEventTracker
from Components.Label import Label
from Components.config import config
# from Components.Pixmap import MultiPixmap
# , iServiceInformation
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
from .utils import urlparse, parse_qs, quote, is_ytdlp_available
from .utils import disable_summary, FavoritesManager, AspectManager, Logger
from .scraper import SkylineScraper


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
    """ InfoBar show/hide control, accepts toggleShow and hide actions, might start
    fancy animations. """
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
        self.hideTimer = eTimer()
        try:
            self.hideTimer_conn = self.hideTimer.timeout.connect(
                self.doTimerHide)
        except BaseException:
            self.hideTimer.callback.append(self.doTimerHide)
        self.hideTimer.start(5000, True)

        self.onShow.append(self.__onShow)
        self.onHide.append(self.__onHide)

    def OkPressed(self):
        self.toggleShow()

    def createButtons(self):
        """Crea i pulsanti della barra informativa"""
        self["key_red"] = Label(_("Exit"))
        self["key_blue"] = Label("")

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

    def __init__(self, session, name, url):
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

        self.name = name
        self.url = url
        self.state = self.STATE_PLAYING
        self.aspect_manager = AspectManager()
        self.aspect_manager.set_aspect("16:9")
        self.scraper = SkylineScraper()

        # self["title"] = Label(self.name)
        # self["status"] = Label(_("Playing"))
        # self["key_red"] = Label(_("Exit"))
        # self["key_blue"] = Label("")
        self.proxy_thread = None
        # self.start_proxy_server()
        self["actions"] = ActionMap(
            [
                "ColorActions", "OkCancelActions",
                "MediaPlayerActions",
            ],

            {
                "cancel": self.cancel,
                "back": self.cancel,
                "red": self.cancel,
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
        # self.updateButtons()
        self.onClose.append(self.cleanup)
        self.onFirstExecBegin.append(self.start_playback)
        self.onLayoutFinish.append(self.show_help_message)

    def get_skin_path(self):
        """Restituisce il percorso della skin in base alla risoluzione"""
        width = getDesktop(0).size().width()
        if width == 2560:
            return join(PLUGIN_PATH, "skin/uhd")
        elif width == 1920:
            return join(PLUGIN_PATH, "skin/fhd")
        else:
            return join(PLUGIN_PATH, "skin/hd")

    def show_help_message(self):
        help_text = _(
            "Player Controls:\n"
            "OK - Show/hide info bar\n"
            "BLUE - Toggle favorite\n"
            "PLAY/PAUSE - Toggle playback\n"
            "STOP - Stop playback\n"
            "EXIT - Close player\n"
        )

        def open_msgbox():
            self.session.open(
                MessageBox,
                help_text,
                MessageBox.TYPE_INFO,
                timeout=5)

        self.timer = eTimer()
        self.timer.callback.append(open_msgbox)
        self.timer.start(100, True)

    def createButtons(self):
        """Crea i pulsanti della barra informativa"""
        self["key_red"] = Label(_("Exit"))
        self["key_blue"] = Label("")

    def __serviceStarted(self):
        """Service started playing"""
        self.logger.info("Playback started successfully")
        self.state = self.STATE_PLAYING
        self.logger.info("Playback started successfully")

    def updateButtons(self):
        """Aggiorna i pulsanti"""
        pass
        # is_fav = FavoritesManager.is_favorite(self.url)
        # self["key_blue"].setText(_("Remove Favorite") if is_fav else _("Add Favorite"))
        # self["key_red"].setText(_("Exit"))

    def toggle_favorite(self):
        """Add or remove from favorites"""
        if FavoritesManager.is_favorite(self.url):
            success = FavoritesManager.remove_favorite(self.url)
            message = _("Removed from favorites") if success else _(
                "Error removing favorite")
        else:
            success = FavoritesManager.add_favorite(self.name, self.url)
            message = _("Added to favorites!") if success else _(
                "Error adding favorite")

        self.updateButtons()
        self.session.open(
            MessageBox,
            message,
            MessageBox.TYPE_INFO,
            timeout=3
        )

    def __evEOF(self):
        """End of file reached"""
        self.logger.info("Playback completed")
        self.close()

    def __evStopped(self):
        """Service stopped"""
        self.logger.info("Playback stopped")
        self.close()

    """
    # def createSummary(self):
        # return None

    # def __onClose(self):
        # if self.hideTimer:
            # self.hideTimer.stop()
    """

    def leavePlayer(self):
        """Close player"""
        self.close()

    def cancel(self):
        """Close player"""
        self.close()

    def start_playback(self):
        """
        Start playback from a direct stream or extracted embedded URL.
        """
        try:
            self.logger.info(f"Starting playback for: {self.name}")
            self.logger.info(f"URL: {self.url}")

            # if URL YouTube, direct stream
            if 'youtube.com' in self.url or 'youtu.be' in self.url:
                self.play_youtube(self.url, self.name)
                return

            # Check if it's a direct stream URL
            if self.is_direct_stream_url(self.url):
                self.logger.info(
                    "Direct stream URL detected - bypassing scraper")
                stream_url = self.url
            else:
                # Use scraper for embedded stream
                self.logger.info("Using scraper for web page source")
                scraper = SkylineScraper()
                stream_url = scraper.get_stream_url(self.url)

                if not stream_url:
                    self.logger.error("Could not extract stream URL")
                    self.show_error(_("Could not extract video stream"))
                    return

            self.logger.info(f"Using stream URL: {stream_url}")

            # Handle YouTube or generic stream playback
            if 'youtube.com' in stream_url or 'youtu.be' in stream_url:
                self.play_youtube(stream_url, self.name)
            else:
                self.play_stream(stream_url, self.name)

        except Exception as e:
            self.logger.error(f"Playback error: {str(e)}")
            self.show_error(f"Playback error: {str(e)}")

    def load_ytdlp(self):
        """Load yt-dlp with detailed error handling"""
        try:
            # Primo tentativo: import diretto (se disponibile a livello di
            # sistema)
            try:
                from yt_dlp import YoutubeDL
                self.logger.info("yt-dlp caricato dal percorso di sistema")
                return YoutubeDL
            except ImportError:
                pass

            # Secondo tentativo: percorso predefinito
            try:
                yt_dlp_path = "/usr/lib/enigma2/python/Plugins/Extensions/WorldCam/yt_dlp"
                if yt_dlp_path not in sys.path:
                    sys.path.append(yt_dlp_path)

                from yt_dlp import YoutubeDL
                self.logger.info("yt-dlp caricato dal percorso predefinito")
                return YoutubeDL
            except ImportError:
                pass

            # Terzo tentativo: percorso del plugin
            try:
                plugin_dir = dirname(abspath(__file__))
                if plugin_dir not in sys.path:
                    sys.path.append(plugin_dir)

                yt_dlp_subdir = join(plugin_dir, 'yt_dlp')
                if yt_dlp_subdir not in sys.path:
                    sys.path.append(yt_dlp_subdir)

                from yt_dlp import YoutubeDL
                self.logger.info("yt-dlp caricato dalla cartella del plugin")
                return YoutubeDL
            except ImportError:
                pass

            # Quarto tentativo: import con imp
            try:
                import imp
                plugin_dir = dirname(abspath(__file__))
                yt_dlp_path = join(plugin_dir, 'yt_dlp', '__init__.py')

                if exists(yt_dlp_path):
                    yt_dlp_module = imp.load_source('yt_dlp', yt_dlp_path)
                    self.logger.info("yt-dlp caricato con imp")
                    return yt_dlp_module.YoutubeDL
            except Exception as e:
                self.logger.error(f"Caricamento con imp fallito: {str(e)}")

            self.logger.error(
                "Impossibile caricare yt-dlp con qualsiasi metodo")
            return None

        except Exception as e:
            self.logger.error(f"Errore nel caricamento di yt-dlp: {str(e)}")
            return None

    def play_youtube(self, url, title):
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
                self.play_with_direct_embed,
                # self.play_with_direct_headers
            ]

            for method in methods:
                try:
                    self.logger.info(f"Trying method: {method.__name__}")
                    if method(video_id, title):
                        self.logger.info("Playback started successfully")
                        return
                except Exception as e:
                    self.logger.error(f"Method failed: {str(e)}")

            # If all methods fail
            self.show_error(_('All YouTube playback methods failed!'))

        except Exception as e:
            self.logger.error(f"Playback failed: {str(e)}")
            self.show_error(_('Error playing YouTube video!'))
            import traceback
            self.logger.error(traceback.format_exc())

    def play_with_ytdlp(self, video_id, title):
        """Method 1: Use yt-dlp with proper configuration"""
        try:
            self.logger.info("Trying yt-dlp method")

            # Load yt-dlp
            YoutubeDL, DownloadError = is_ytdlp_available(logger=self.logger)
            if not YoutubeDL:
                return False

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
                    formats = [f for f in info['formats']
                               if f.get('protocol', '').startswith('http')]

                    if not formats:
                        self.logger.error("No HTTP formats available")
                        return False

                    compatible_formats = [
                        f for f in formats
                        # Richiede audio
                        if not f.get('acodec', 'none') == 'none'
                        # Richiede video
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
            if "live stream recording is not available" in str(e):
                try:
                    self.log_info("Trying VOD extraction method")
                    vod_url = self.url.replace(
                        "/live", "")  # Rimuove il contesto live
                    with YoutubeDL({**ydl_opts, 'live_from_start': False}) as ydl:
                        info = ydl.extract_info(vod_url, download=False)
                        return info['url']

                except Exception as vod_e:
                    print('erro except youtube player:', str(vod_e))
                    self.log_info("Trying Wayback Machine archive")
                    archive_url = f"https://web.archive.org/web/2oe_/http://youtube.com/watch?v={self.video_id}"
                    return self.play_with_streamlink_fallback(archive_url)

            else:
                raise

    def play_with_streamlink_fallback(self, url):
        try:
            return subprocess.check_output([
                'streamlink',
                '--stream-url',
                '--http-header',
                "User-Agent=Mozilla/5.0 (X11; Linux armv7l) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
                '--default-stream', 'best',
                url
            ], timeout=15).decode().strip()
        except Exception as e:
            self.log_error(f"Streamlink Fallback Failed: {str(e)}")
            return None

    def convert_hls_to_ts(self, hls_url):
        ts_path = f"/tmp/{time.time()}.ts"
        subprocess.Popen([
            'ffmpeg',
            '-i', hls_url,
            '-c', 'copy',
            '-f', 'mpegts',
            ts_path
        ])
        return f"file://{ts_path}"

    def play_with_direct_embed(self, video_id, title):
        """Method 2: Direct embed URL with headers"""
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

    def play_with_direct_headers(self, video_id, title):
        """Method 3: Direct video URL with headers"""
        try:
            self.logger.info("Trying direct video method")
            url = f"https://www.youtube.com/v/{video_id}"

            # Create headers string
            headers = (
                "User-Agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36&"
                f"Referer=https://www.youtube.com/watch?v={video_id}&"
                "Origin=https://www.youtube.com")

            service = eServiceReference(4097, 0, f"{url}|{headers}")
            service.setName(title)
            self.start_service_playback(service)
            return True
        except Exception as e:
            self.logger.error(f"Direct video method failed: {str(e)}")
            return False

    def extract_video_id(self, url):
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

        return None

    def start_service_playback(self, service):
        """Start playback with special handling"""
        # Stop any current playback
        if self.session.nav.getCurrentlyPlayingServiceReference():
            self.session.nav.stopService()

        # Start new playback
        self.session.nav.playService(service)
        self.show()
        self.state = self.STATE_PLAYING

    def play_youtube_direct(self, url, title):
        """Fallback method for direct YouTube playback"""
        try:
            self.logger.info("Using direct YouTube method")
            service = eServiceReference(
                4097, 0, f"https://www.youtube.com/watch?v={self.extract_video_id(url)}")
            service.setName(title)
            self.start_service_playback(service)
        except Exception as e:
            self.logger.error(f"Direct method failed: {str(e)}")
            self.show_error(_('All YouTube methods failed!'))

    def is_direct_stream_url(self, url):
        """
        Check if the URL is a direct stream or a web page.
        """
        try:
            # Normalize URL
            url_lower = url.lower()

            # YouTube URLs are considered direct
            if "youtube.com" in url_lower or "youtu.be" in url_lower:
                self.logger.info(
                    "YouTube URL detected - treating as direct stream")
                return True

            parsed = urlparse(url)
            path = parsed.path.lower()
            query = parsed.query.lower()

            # Check for stream file extensions
            stream_extensions = [
                ".m3u8",
                ".mp4",
                ".ts",
                ".flv",
                ".mpd",
                ".avi",
                ".mov",
                ".mkv"]
            if any(path.endswith(ext) for ext in stream_extensions):
                self.logger.info(
                    f"Direct stream detected by file extension: {path}")
                return True

            # Check for direct stream protocols
            stream_protocols = [
                "rtmp://",
                "rtsp://",
                "udp://",
                "mms://",
                "http://",
                "https://"]
            if any(url_lower.startswith(proto) for proto in stream_protocols):
                if url_lower.startswith(("http://", "https://")):
                    web_page_indicators = [
                        ".html", ".htm", ".php", ".asp", ".aspx",
                        ".jsp", ".cgi", "/index", "/main", "/home",
                        "?page=", "?id=", "?view=", "?action="
                    ]
                    if not any(
                            ind in url_lower for ind in web_page_indicators):
                        self.logger.info(
                            f"HTTP/HTTPS URL without web page indicators: {url}")
                        return True
                else:
                    self.logger.info(
                        f"Direct stream protocol detected: {url.split('://')[0]}")
                    return True

            # Keywords in path
            stream_keywords = [
                "/live/", "/stream/", "/hls/", "/dash/",
                "index.m3u8", "playlist.m3u8", "manifest.mpd",
                "chunklist", "segment", "video", "live"
            ]
            if any(kw in path for kw in stream_keywords):
                self.logger.info(f"Stream keyword found in path: {path}")
                return True

            # Keywords in query
            stream_params = [
                "m3u8", "mp4", "ts", "flv", "mpd", "stream", "live",
                "hls", "dash", "video", "playlist", "manifest"
            ]
            if any(param in query for param in stream_params):
                self.logger.info(f"Stream parameter found in query: {query}")
                return True

            # Known services that require scraping
            streaming_services = [
                "livestream.com", "ustream.tv", "twitch.tv",
                "dailymotion.com", "vimeo.com", "facebook.com/live"
            ]
            if any(service in url_lower for service in streaming_services):
                self.logger.info(f"Known streaming service detected: {url}")
                return False

            # Token parameters in query
            token_patterns = [
                "token=", "key=", "secret=", "signature=",
                "exp=", "session=", "auth_token="
            ]
            if any(pattern in query for pattern in token_patterns):
                self.logger.info(
                    "Token detected in URL - assuming direct stream")
                return True

            # URL with query only
            if not path.strip("/") and query:
                self.logger.info(
                    "URL with only query parameters - likely API/stream endpoint")
                return True

            self.logger.info(f"URL appears to be a web page: {url}")
            return False

        except Exception as e:
            self.logger.error(f"Error analyzing URL: {str(e)}")
            return False

    def play_stream(self, stream_url, title=""):
        """
        Play a media stream based on the given URL.
        Attempts to identify the appropriate service type (HLS, HTTP, RTMP)
        and initiate playback using Enigma2's navigation system. Supports
        basic stream type detection via file extension and protocol.
        Args:
            stream_url (str or list/tuple): The URL of the media stream. If a list/tuple is passed, only the first item is used.
            title (str, optional): The display name for the stream. Defaults to an empty string.
        Notes:
            - Automatically stops any ongoing playback before starting the new one.
            - Supports HLS (.m3u8), HTTP, and RTMP protocols.
            - If stream availability check is re-enabled, invalid URLs will be rejected.
        Logs:
            - Detailed information on stream type, final URL, and playback success or failure.
        Displays:
            - An error message if stream playback fails.
        """
        try:
            self.logger.info(
                f"Attempting to play stream of type: {type(stream_url)}")

            # Safe conversion to string
            if isinstance(stream_url, (tuple, list)):
                stream_url = str(stream_url[0])
            else:
                stream_url = str(stream_url)

            self.logger.info(f"Final stream URL: {stream_url[:200]}...")

            # Check for stream availability (optional)
            """
            if not self.check_stream_availability(stream_url):
                self.show_error(_("Stream unavailable or invalid"))
                return
            """

            # Determine the service type based on the URL
            if '.m3u8' in stream_url.lower() or stream_url.lower().startswith('http'):
                # Use HLS service for M3U8 and HTTP
                service = eServiceReference(5001, 0, stream_url)
            elif stream_url.lower().startswith('rtmp'):
                # Use RTMP service
                service = eServiceReference(4097, 0, stream_url)
            else:
                # Default to HTTP/other service
                service = eServiceReference(4097, 0, stream_url)

            service.setName(title)

            # Stop current playback if any
            if self.session.nav.getCurrentlyPlayingServiceReference():
                self.session.nav.stopService()

            # Start new playback
            self.session.nav.playService(service)
            self.show()

            # Update state
            self.state = self.STATE_PLAYING
            self.logger.info("Playback started successfully")

        except Exception as e:
            self.logger.error(f"Error playing stream: {str(e)}")
            self.show_error(_('Playback failed!'))
            import traceback
            self.logger.error(traceback.format_exc())

    def check_stream_availability(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0'}
            response = requests.head(
                url, headers=headers, timeout=5, allow_redirects=True)

            if response.status_code != 200:
                self.logger.error(
                    f"Stream unavailable. Status code: {response.status_code}")
                return False

            content_type = response.headers.get('Content-Type', '').lower()

            if 'video' in content_type or 'application' in content_type:
                return True

            self.logger.error(f"Unexpected content type: {content_type}")
            return False

        except Exception as e:
            self.logger.error(f"Stream check failed: {str(e)}")
            return False

    def playpauseService(self):
        """Toggle play/pause"""
        service = self.session.nav.getCurrentService()
        if not service:
            return

        pauseable = service.pause()
        if pauseable is None:
            self.logger.warning("Service is not pauseable")
            return

        if self.state == self.STATE_PLAYING:
            pauseable.pause()
            self.state = self.STATE_PAUSED
            self.logger.info("Playback paused")
        elif self.state == self.STATE_PAUSED:
            pauseable.play()
            self.state = self.STATE_PLAYING
            self.logger.info("Playback resumed")

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
        # Remove temporary files
        if exists('/tmp/hls.avi'):
            try:
                remove('/tmp/hls.avi')
            except BaseException:
                pass

        # Restore aspect ratio
        self.aspect_manager.restore_aspect()

        # Stop current service
        self.session.nav.stopService()

        # Restore initial service
        if self.srefInit:
            try:
                self.session.nav.playService(self.srefInit)
            except BaseException:
                pass

        if self.proxy_thread and self.proxy_thread.is_alive():
            # There is no clean way to stop HTTPServer, but since it is a daemon thread, it will
            # automatically terminate when the main program terminates
            pass

    def test_youtube_playback(self):
        """Test method for YouTube playback"""
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
        self.logger.info(f"Testing YouTube playback with URL: {test_url}")
        self.play_youtube(test_url, "YouTube Test Video")

    def start_proxy_server(self):
        """Start the proxy server if not already running"""
        if self.proxy_thread and self.proxy_thread.is_alive():
            return

        self.logger.info("Starting HLS proxy server")

        # Create a new thread for the proxy server
        self.proxy_thread = threading.Thread(
            target=self.run_proxy_server,
            daemon=True
        )
        self.proxy_thread.start()

        # Wait briefly for server to initialize
        sleep(1)

    def run_proxy_server(self):
        """Run the proxy server indefinitely"""
        server = HTTPServer(('127.0.0.1', 8000),
                            lambda *args: HLSProxyHandler(self, *args))
        self.logger.info("HLS proxy server started on port 8000")
        server.serve_forever()

    def play_youtube_proxy(self, url, title):
        """
        Play YouTube video using our local proxy server for enhanced compatibility.
        This method handles the entire process:
        1. Extracts the YouTube video ID
        2. Gets the direct stream URL using YouTubeExtractor
        3. Starts the proxy server if not already running
        4. Creates a proxy playlist URL
        5. Plays the video through the proxy with proper headers
        """
        try:
            self.logger.info(f"Starting proxy playback for: {title}")
            self.logger.info(f"URL: {url}")

            # # Ensure proxy server is running
            self.start_proxy_server()

            # Extract video ID
            from .YouTubeExtractor import YouTubeExtractor
            extractor = YouTubeExtractor(logger=self.logger)
            video_id = extractor.extract_video_id(url)

            if not video_id:
                self.logger.error("Invalid YouTube URL")
                self.show_error(_("Invalid YouTube URL"))
                return

            self.logger.info(f"Video ID: {video_id}")

            # Get stream URL and headers
            stream_url, extension, headers = extractor.get_stream_url(video_id)

            if not stream_url:
                self.logger.error("Failed to extract stream URL")
                self.show_error(_("Couldn't extract video stream"))
                return

            self.logger.info(f"Extracted stream URL: {stream_url[:200]}...")
            self.logger.info(f"File extension: {extension}")
            self.logger.info(f"Headers: {headers}")

            # Encode stream URL for proxy
            from .utils import quote
            encoded_url = quote(stream_url, safe='')

            # Create two proxy URLs:
            # 1. For the playlist (M3U8)
            playlist_url = f"http://127.0.0.1:8000/proxy.m3u8?url={encoded_url}"

            # 2. For the video stream
            video_url = f"http://127.0.0.1:8000/video?url={encoded_url}"

            # Generate the M3U8 playlist content
            m3u8_content = f"""#EXTM3U
    #EXT-X-VERSION:3
    #EXT-X-TARGETDURATION:10
    #EXT-X-MEDIA-SEQUENCE:0
    #EXTINF:10.0,
    {video_url}
    #EXT-X-ENDLIST"""
            self.logger.info(f"YouTube m3u8_content: {str(m3u8_content)}")

            # Create headers string for service reference
            headers_str = f"User-Agent=Mozilla%2F5.0%20(X11%3B%20Linux%20x86_64)%20AppleWebKit%2F537.36%20(KHTML%2C%20like%20Gecko)%20Chrome%2F91.0.4472.114%20Safari%2F537.36&Referer=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3D{video_id}&Origin=https%3A%2F%2Fwww.youtube.com"

            # Use service 5001 (HLS) with the proxy playlist
            service = eServiceReference(
                5001, 0, f"{playlist_url}|{headers_str}")
            service.setName(title)

            # Start playback
            self.start_service_playback(service)
            self.logger.info("YouTube proxy playback started successfully")

        except Exception as e:
            self.logger.error(f"Proxy playback failed: {str(e)}")
            self.show_error(_('Error playing YouTube video with proxy!'))
            import traceback
            self.logger.error(traceback.format_exc())


class HLSProxyHandler(BaseHTTPRequestHandler):
    def __init__(self, player_instance, *args, **kwargs):
        self.player = player_instance
        super().__init__(*args, **kwargs)

    @property
    def logger(self):
        return self.player.logger if self.player else None

    def do_GET(self):
        try:
            # Handle M3U8 playlist requests
            if self.path.startswith("/proxy.m3u8"):
                query = urlparse(self.path).query
                params = parse_qs(query)
                target_url = params.get('url', [''])[0]

                if not target_url:
                    self.send_error(404, 'Missing URL parameter')
                    return

                # Generate proxy playlist
                m3u8_content = self.generate_proxy_playlist(target_url)

                self.send_response(200)
                self.send_header(
                    'Content-Type',
                    'application/vnd.apple.mpegurl')
                self.end_headers()
                self.wfile.write(m3u8_content.encode('utf-8'))
                return

            # Handle video segment requests
            elif self.path.startswith("/video"):
                query = urlparse(self.path).query
                params = parse_qs(query)
                target_url = params.get('url', [''])[0]

                if not target_url:
                    self.send_error(404, 'Missing URL parameter')
                    return

                # Get video ID for headers
                video_id = self.extract_video_id(target_url)

                # Set headers for YouTube
                headers = {
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
                    'Referer': f'https://www.youtube.com/watch?v={video_id}',
                    'Origin': 'https://www.youtube.com'}

                # Fetch the video segment
                response = requests.get(
                    target_url,
                    headers=headers,
                    stream=True,
                    timeout=10,
                    allow_redirects=True
                )

                # Forward the response
                self.send_response(response.status_code)
                for key, value in response.headers.items():
                    if key.lower() not in [
                            'transfer-encoding', 'connection', 'keep-alive']:
                        self.send_header(key, value)
                self.end_headers()

                # Stream the content
                for chunk in response.iter_content(chunk_size=8192):
                    self.wfile.write(chunk)

                return

        except Exception as e:
            self.logger.error(f"Proxy error: {str(e)}")
            self.send_error(500, str(e))

        self.send_error(404, 'Not Found')

    def generate_proxy_playlist(self, target_url):
        """Generate a proxy M3U8 playlist"""
        return f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXTINF:10.0,
http://127.0.0.1:8000/video?url={quote(target_url, safe='')}
#EXT-X-ENDLIST"""
