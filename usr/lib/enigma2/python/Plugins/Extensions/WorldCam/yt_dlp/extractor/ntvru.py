from .common import InfoExtractor
from ..utils import (
    int_or_none,
    strip_or_none,
    unescapeHTML,
    xpath_text,
)


class NTVRuIE(InfoExtractor):
    IE_NAME = 'ntv.ru'
    _VALID_URL = r'https?://(?:www\.)?ntv\.ru/(?:[^/]+/)*(?P<id>[^/?#&]+)'

    _TESTS = [{
        'url': 'http://www.ntv.ru/novosti/863142/',
        'md5': 'ba7ea172a91cb83eb734cad18c10e723',
        'info_dict': {
            'id': '746000',
            'ext': 'mp4',
            'title': 'Командующий Черноморским флотом провел переговоры в штабе ВМС Украины',
            'description': 'Командующий Черноморским флотом провел переговоры в штабе ВМС Украины',
            'thumbnail': r're:^http://.*\.jpg',
            'duration': 136,
            'view_count': int,
        },
    }, {
        'url': 'http://www.ntv.ru/video/novosti/750370/',
        'md5': 'adecff79691b4d71e25220a191477124',
        'info_dict': {
            'id': '750370',
            'ext': 'mp4',
            'title': 'Родные пассажиров пропавшего Boeing не верят в трагический исход',
            'description': 'Родные пассажиров пропавшего Boeing не верят в трагический исход',
            'thumbnail': r're:^http://.*\.jpg',
            'duration': 172,
            'view_count': int,
        },
        'skip': '404 Not Found',
    }, {
        'url': 'http://www.ntv.ru/peredacha/segodnya/m23700/o232416',
        'md5': '82dbd49b38e3af1d00df16acbeab260c',
        'info_dict': {
            'id': '747480',
            'ext': 'mp4',
            'title': '«Сегодня». 21 марта 2014 года. 16:00',
            'description': '«Сегодня». 21 марта 2014 года. 16:00',
            'thumbnail': r're:^http://.*\.jpg',
            'duration': 1496,
            'view_count': int,
        },
    }, {
        'url': 'https://www.ntv.ru/kino/Koma_film/m70281/o336036/video/',
        'md5': 'e9c7cde24d9d3eaed545911a04e6d4f4',
        'info_dict': {
            'id': '1126480',
            'ext': 'mp4',
            'title': 'Остросюжетный фильм «Кома»',
            'description': 'Остросюжетный фильм «Кома»',
            'thumbnail': r're:^http://.*\.jpg',
            'duration': 5592,
            'view_count': int,
        },
    }, {
        'url': 'http://www.ntv.ru/serial/Delo_vrachey/m31760/o233916/',
        'md5': '9320cd0e23f3ea59c330dc744e06ff3b',
        'info_dict': {
            'id': '751482',
            'ext': 'mp4',
            'title': '«Дело врачей»: «Деревце жизни»',
            'description': '«Дело врачей»: «Деревце жизни»',
            'thumbnail': r're:^http://.*\.jpg',
            'duration': 2590,
            'view_count': int,
        },
    }, {
        # Schemeless file URL
        'url': 'https://www.ntv.ru/video/1797442',
        'only_matching': True,
    }]

    _VIDEO_ID_REGEXES = [
        r'<meta property="og:url" content="https?://www\.ntv\.ru/video/(\d+)',
        r'<meta property="og:video:(?:url|iframe)" content="https?://www\.ntv\.ru/embed/(\d+)',
        r'<video embed=[^>]+><id>(\d+)</id>',
        r'<video restriction[^>]+><key>(\d+)</key>',
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_url = self._og_search_property(
            ('video', 'video:iframe'), webpage, default=None)
        if video_url:
            video_id = self._search_regex(
                r'https?://(?:www\.)?ntv\.ru/video/(?:embed/)?(\d+)',
                video_url, 'video id', default=None)

        if not video_id:
            video_id = self._html_search_regex(
                self._VIDEO_ID_REGEXES, webpage, 'video id')

        player = self._download_xml(
            f'http://www.ntv.ru/vi{video_id}/',
            video_id, 'Downloading video XML')

        title = strip_or_none(
            unescapeHTML(
                xpath_text(
                    player,
                    './data/title',
                    'title',
                    fatal=True)))

        video = player.find('./data/video')

        formats = []
        for format_id in ['', 'hi', 'webm']:
            file_ = xpath_text(video, f'./{format_id}file')
            if not file_:
                continue
            if file_.startswith('//'):
                file_ = self._proto_relative_url(file_)
            elif not file_.startswith('http'):
                file_ = 'http://media.ntv.ru/vod/' + file_
            formats.append({'url': file_, 'filesize': int_or_none(
                xpath_text(video, f'./{format_id}size')), })
        hls_manifest = xpath_text(video, './playback/hls')
        if hls_manifest:
            formats.extend(self._extract_m3u8_formats(
                hls_manifest, video_id, m3u8_id='hls', fatal=False))
        dash_manifest = xpath_text(video, './playback/dash')
        if dash_manifest:
            formats.extend(self._extract_mpd_formats(
                dash_manifest, video_id, mpd_id='dash', fatal=False))

        return {
            'id': xpath_text(
                video,
                './id'),
            'title': title,
            'description': strip_or_none(
                unescapeHTML(
                    xpath_text(
                        player,
                        './data/description'))),
            'thumbnail': xpath_text(
                video,
                './splash'),
            'duration': int_or_none(
                xpath_text(
                    video,
                    './totaltime')),
            'view_count': int_or_none(
                xpath_text(
                    video,
                    './views')),
            'formats': formats,
        }
