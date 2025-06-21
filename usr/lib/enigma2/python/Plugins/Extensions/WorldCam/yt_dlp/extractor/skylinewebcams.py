# coding: utf-8
from __future__ import unicode_literals
import re

# Import corretti per la tua struttura
from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    str_or_none,
    try_get,
    unified_timestamp,
    update_url_query,
)


class SkylineWebcamsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?skylinewebcams\.com/[^/]+/webcam/(?:[^/]+/)+(?P<id>[^/]+)\.html'
    _TESTS = [{
        'url': 'https://www.skylinewebcams.com/it/webcam/italia/lazio/roma/scalinata-piazza-di-spagna-barcaccia.html',
        'info_dict': {
            'id': 'scalinata-piazza-di-spagna-barcaccia',
            'ext': 'mp4',
            'title': 're:^Live Webcam Scalinata di Piazza di Spagna - La Barcaccia',
            'description': 'Roma, veduta sulla Scalinata di Piazza di Spagna e sulla Barcaccia',
            'is_live': True,
        },
        'params': {
            'skip_download': True,
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # Pattern 1: Direct HLS in JavaScript
        hls_url = self._search_regex(
            r'player\.setup\(\s*{\s*[^}]*source\s*:\s*["\'](https?://[^"\']+\.m3u8\?[^"\']*)["\']',
            webpage, 'hls url', default=None)

        # Pattern 2: HLS with token
        if not hls_url:
            token = self._search_regex(
                r'token\s*:\s*["\']([^"\']+)["\']',
                webpage, 'token', default=None)
            cam_id = self._search_regex(
                r'cam_id\s*:\s*["\'](\d+)["\']',
                webpage, 'cam_id', default=None)

            if token and cam_id:
                hls_url = f'https://hd-auth.skylinewebcams.com/live.m3u8?token={token}&cam_id={cam_id}'

        # Pattern 3: YouTube fallback
        if not hls_url:
            youtube_id = self._search_regex(
                r'videoId\s*:\s*["\']([^"\']+)["\']',
                webpage, 'youtube id', default=None)
            if youtube_id:
                return {
                    '_type': 'url',
                    'url': youtube_id,
                    'ie_key': 'Youtube',
                }

        # Pattern 4: Generic m3u8 search
        if not hls_url:
            hls_url = self._search_regex(
                r'(https?://[^\s"]+\.m3u8[^\s"]*)',
                webpage, 'generic hls url', default=None)

        if not hls_url:
            raise ExtractorError('Could not extract video URL')

        # Clean and normalize URL
        if not hls_url.startswith('http'):
            hls_url = 'https:' + hls_url

        title = self._og_search_title(webpage, default=video_id)
        description = self._og_search_description(webpage, default='')

        # Clean title from dates/times
        title = re.sub(r'\s*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}$', '', title)
        title = re.sub(r'^Live Webcam\s*', '', title)
        title = title.strip()

        return {
            'id': video_id,
            'url': hls_url,
            'title': title,
            'description': description,
            'is_live': True,
            'http_headers': {
                'Referer': url,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            }}
