import itertools

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    format_field,
    int_or_none,
    str_or_none,
    try_get,
)

CDN_API_BASE = 'https://cdn.younow.com/php/api'
MOMENT_URL_FORMAT = f'{CDN_API_BASE}/moment/fetch/id=%s'


class YouNowLiveIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?younow\.com/(?P<id>[^/?#&]+)'
    _TEST = {
        'url': 'https://www.younow.com/AmandaPadeezy',
        'info_dict': {
            'id': 'AmandaPadeezy',
            'ext': 'mp4',
            'is_live': True,
            'title': 'March 26, 2017',
            'thumbnail': r're:^https?://.*\.jpg$',
            'tags': ['girls'],
            'categories': ['girls'],
            'uploader': 'AmandaPadeezy',
            'uploader_id': '6716501',
            'uploader_url': 'https://www.younow.com/AmandaPadeezy',
            'creator': 'AmandaPadeezy',
        },
        'skip': True,
    }

    @classmethod
    def suitable(cls, url):
        return (False if YouNowChannelIE.suitable(url)
                or YouNowMomentIE.suitable(url) else super().suitable(url))

    def _real_extract(self, url):
        username = self._match_id(url)

        data = self._download_json(
            f'https://api.younow.com/php/api/broadcast/info/curId=0/user={username}',
            username)

        if data.get('errorCode') != 0:
            raise ExtractorError(data['errorMsg'], expected=True)

        uploader = try_get(
            data, lambda x: x['user']['profileUrlString'],
            str) or username

        return {
            'id': uploader,
            'is_live': True,
            'title': uploader,
            'thumbnail': data.get('awsUrl'),
            'tags': data.get('tags'),
            'categories': data.get('tags'),
            'uploader': uploader,
            'uploader_id': data.get('userId'),
            'uploader_url': f'https://www.younow.com/{username}',
            'creator': uploader,
            'view_count': int_or_none(
                data.get('viewers')),
            'like_count': int_or_none(
                data.get('likes')),
            'formats': [
                {
                    'url': '{}/broadcast/videoPath/hls=1/broadcastId={}/channelId={}'.format(
                        CDN_API_BASE,
                        data['broadcastId'],
                        data['userId']),
                    'ext': 'mp4',
                    'protocol': 'm3u8',
                }],
        }


def _extract_moment(item, fatal=True):
    moment_id = item.get('momentId')
    if not moment_id:
        if not fatal:
            return
        raise ExtractorError('Unable to extract moment id')

    moment_id = str(moment_id)

    title = item.get('text')
    if not title:
        title = 'YouNow %s' % (
            item.get('momentType') or item.get('titleType') or 'moment')

    uploader = try_get(item, lambda x: x['owner']['name'], str)
    uploader_id = try_get(item, lambda x: x['owner']['userId'])
    uploader_url = format_field(uploader, None, 'https://www.younow.com/%s')

    return {
        'extractor_key': 'YouNowMoment',
        'id': moment_id,
        'title': title,
        'view_count': int_or_none(item.get('views')),
        'like_count': int_or_none(item.get('likes')),
        'timestamp': int_or_none(item.get('created')),
        'creator': uploader,
        'uploader': uploader,
        'uploader_id': str_or_none(uploader_id),
        'uploader_url': uploader_url,
        'formats': [{
            'url': f'https://hls.younow.com/momentsplaylists/live/{moment_id}/{moment_id}.m3u8',
            'ext': 'mp4',
            'protocol': 'm3u8_native',
        }],
    }


class YouNowChannelIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?younow\.com/(?P<id>[^/]+)/channel'
    _TEST = {
        'url': 'https://www.younow.com/its_Kateee_/channel',
        'info_dict': {
            'id': '14629760',
            'title': 'its_Kateee_ moments',
        },
        'playlist_mincount': 8,
    }

    def _entries(self, username, channel_id):
        created_before = 0
        for page_num in itertools.count(1):
            if created_before is None:
                break
            info = self._download_json(
                f'{CDN_API_BASE}/moment/profile/channelId={channel_id}/createdBefore={created_before}/records=20',
                username, note=f'Downloading moments page {page_num}')
            items = info.get('items')
            if not items or not isinstance(items, list):
                break
            for item in items:
                if not isinstance(item, dict):
                    continue
                item_type = item.get('type')
                if item_type == 'moment':
                    entry = _extract_moment(item, fatal=False)
                    if entry:
                        yield entry
                elif item_type == 'collection':
                    moments = item.get('momentsIds')
                    if isinstance(moments, list):
                        for moment_id in moments:
                            m = self._download_json(
                                MOMENT_URL_FORMAT % moment_id, username,
                                note=f'Downloading {moment_id} moment JSON',
                                fatal=False)
                            if m and isinstance(m, dict) and m.get('item'):
                                entry = _extract_moment(m['item'])
                                if entry:
                                    yield entry
                created_before = int_or_none(item.get('created'))

    def _real_extract(self, url):
        username = self._match_id(url)
        channel_id = str(
            self._download_json(
                f'https://api.younow.com/php/api/broadcast/info/curId=0/user={username}',
                username,
                note='Downloading user information')['userId'])
        return self.playlist_result(
            self._entries(username, channel_id), channel_id,
            f'{username} moments')


class YouNowMomentIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?younow\.com/[^/]+/(?P<id>[^/?#&]+)'
    _TEST = {
        'url': 'https://www.younow.com/GABO.../20712117/36319236/3b316doc/m',
        'md5': 'a30c70eadb9fb39a1aa3c8c0d22a0807',
        'info_dict': {
            'id': '20712117',
            'ext': 'mp4',
            'title': 'YouNow capture',
            'view_count': int,
            'like_count': int,
            'timestamp': 1490432040,
            'upload_date': '20170325',
            'uploader': 'GABO...',
            'uploader_id': '35917228',
        },
    }

    @classmethod
    def suitable(cls, url):
        return (False
                if YouNowChannelIE.suitable(url)
                else super().suitable(url))

    def _real_extract(self, url):
        video_id = self._match_id(url)
        item = self._download_json(MOMENT_URL_FORMAT % video_id, video_id)
        return _extract_moment(item['item'])
