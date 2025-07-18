from .common import InfoExtractor
from ..utils import (
    KNOWN_EXTENSIONS,
    determine_ext,
    str_to_int,
)


class HearThisAtIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hearthis\.at/(?P<artist>[^/?#]+)/(?P<title>[\w.-]+)'
    _PLAYLIST_URL = 'https://hearthis.at/playlist.php'
    _TESTS = [{
        'url': 'https://hearthis.at/moofi/dr-kreep',
        'md5': 'ab6ec33c8fed6556029337c7885eb4e0',
        'info_dict': {
            'id': '150939',
            'display_id': 'moofi - dr-kreep',
            'ext': 'wav',
            'title': 'Moofi - Dr. Kreep',
            'thumbnail': r're:^https?://.*\.jpg$',
            'timestamp': 1421564134,
            'description': 'md5:1adb0667b01499f9d27e97ddfd53852a',
            'upload_date': '20150118',
            'view_count': int,
            'duration': 70,
            'genres': ['Experimental'],
        },
    }, {
        # 'download' link redirects to the original webpage
        'url': 'https://hearthis.at/twitchsf/dj-jim-hopkins-totally-bitchin-80s-dance-mix/',
        'md5': '5980ceb7c461605d30f1f039df160c6e',
        'info_dict': {
            'id': '811296',
            'display_id': 'twitchsf - dj-jim-hopkins-totally-bitchin-80s-dance-mix',
            'ext': 'mp3',
            'title': 'TwitchSF - DJ Jim Hopkins -  Totally Bitchin\' 80\'s Dance Mix!',
            'description': 'md5:ef26815ca8f483272a87b137ff175be2',
            'upload_date': '20160328',
            'timestamp': 1459186146,
            'thumbnail': r're:^https?://.*\.jpg$',
            'view_count': int,
            'duration': 4360,
            'genres': ['Dance'],
        },
    }, {
        'url': 'https://hearthis.at/tindalos/0001-tindalos-gnrique/eQd/',
        'md5': 'cd08e51911f147f6da2d9678905b0bd9',
        'info_dict': {
            'id': '2685222',
            'ext': 'mp3',
            'duration': 86,
            'view_count': int,
            'timestamp': 1545471670,
            'display_id': 'tindalos - 0001-tindalos-gnrique',
            'thumbnail': r're:^https?://.*\.jpg$',
            'genres': ['Other'],
            'title': 'Tindalos - Tindalos - générique n°1',
            'description': '',
            'upload_date': '20181222',
        },
    }, {
        'url': 'https://hearthis.at/sithi2/biochip-c-classics-set-wolle-xdp-tresor.core-special-tresor-globus-berlin-13.07.20011/',
        'md5': 'b45ac60f0c8111eef6ddc10ec232e312',
        'info_dict': {
            'id': '7145959',
            'ext': 'mp3',
            'description': 'md5:d7ae36a453d78903f6b7ed6eb2fce1f2',
            'duration': 8986,
            'thumbnail': r're:^https?://.*\.jpg$',
            'title': 'md5:62669ce5b1b67f45c6f846033f37d3b9',
            'timestamp': 1588699409,
            'display_id': 'sithi2 - biochip-c-classics-set-wolle-xdp-tresor.core-special-tresor-globus-berlin-13.07.20011',
            'view_count': int,
            'upload_date': '20200505',
            'genres': ['Other'],
        },
    }]

    def _real_extract(self, url):
        m = self._match_valid_url(url)
        display_id = '{artist:s} - {title:s}'.format(**m.groupdict())
        api_url = url.replace(
            'www.', '').replace(
            'hearthis.at', 'api-v2.hearthis.at')
        data_json = self._download_json(api_url, display_id)
        track_id = data_json.get('id')
        artist_json = data_json.get('user')
        title = '{} - {}'.format(artist_json.get('username'),
                                 data_json.get('title'))
        genre = data_json.get('genre')
        description = data_json.get('description')
        thumbnail = data_json.get('artwork_url') or data_json.get('thumb')
        view_count = str_to_int(data_json.get('playback_count'))
        duration = str_to_int(data_json.get('duration'))
        timestamp = data_json.get('release_timestamp')

        formats = []
        mp3_url = data_json.get('stream_url')

        if mp3_url:
            formats.append({
                'format_id': 'mp3',
                'vcodec': 'none',
                'acodec': 'mp3',
                'url': mp3_url,
                'ext': 'mp3',
            })

        if data_json.get('download_url'):
            download_url = data_json['download_url']
            ext = determine_ext(data_json['download_filename'])
            if ext in KNOWN_EXTENSIONS:
                formats.append({
                    'format_id': ext,
                    'vcodec': 'none',
                    'ext': ext,
                    'url': download_url,
                    'acodec': ext,
                    'quality': 2,  # Usually better quality
                })

        return {
            'id': track_id,
            'display_id': display_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'description': description,
            'duration': duration,
            'timestamp': timestamp,
            'view_count': view_count,
            'genre': genre,
        }
