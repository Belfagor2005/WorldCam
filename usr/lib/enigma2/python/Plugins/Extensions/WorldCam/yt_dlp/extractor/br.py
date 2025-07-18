from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_duration,
    xpath_element,
    xpath_text,
)


class BRIE(InfoExtractor):
    _WORKING = False
    IE_DESC = 'Bayerischer Rundfunk'
    _VALID_URL = r'(?P<base_url>https?://(?:www\.)?br(?:-klassik)?\.de)/(?:[a-z0-9\-_]+/)+(?P<id>[a-z0-9\-_]+)\.html'

    _TESTS = [{'url': 'http://www.br.de/mediathek/video/sendungen/abendschau/betriebliche-altersvorsorge-104.html',
               'md5': '83a0477cf0b8451027eb566d88b51106',
               'info_dict': {'id': '48f656ef-287e-486f-be86-459122db22cc',
                             'ext': 'mp4',
                             'title': 'Die böse Überraschung',
                             'description': 'md5:ce9ac81b466ce775b8018f6801b48ac9',
                             'duration': 180,
                             'uploader': 'Reinhard Weber',
                             'upload_date': '20150422',
                             },
               'skip': '404 not found',
               },
              {'url': 'http://www.br.de/nachrichten/oberbayern/inhalt/muenchner-polizeipraesident-schreiber-gestorben-100.html',
               'md5': 'af3a3a4aa43ff0ce6a89504c67f427ef',
               'info_dict': {'id': 'a4b83e34-123d-4b81-9f4e-c0d3121a4e05',
                             'ext': 'flv',
                             'title': 'Manfred Schreiber ist tot',
                             'description': 'md5:b454d867f2a9fc524ebe88c3f5092d97',
                             'duration': 26,
                             },
               'skip': '404 not found',
               },
              {'url': 'https://www.br-klassik.de/audio/peeping-tom-premierenkritik-dance-festival-muenchen-100.html',
               'md5': '8b5b27c0b090f3b35eac4ab3f7a73d3d',
               'info_dict': {'id': '74c603c9-26d3-48bb-b85b-079aeed66e0b',
                             'ext': 'aac',
                             'title': 'Kurzweilig und sehr bewegend',
                             'description': 'md5:0351996e3283d64adeb38ede91fac54e',
                             'duration': 296,
                             },
               'skip': '404 not found',
               },
              {'url': 'http://www.br.de/radio/bayern1/service/team/videos/team-video-erdelt100.html',
               'md5': 'dbab0aef2e047060ea7a21fc1ce1078a',
               'info_dict': {'id': '6ba73750-d405-45d3-861d-1ce8c524e059',
                             'ext': 'mp4',
                             'title': 'Umweltbewusster Häuslebauer',
                             'description': 'md5:d52dae9792d00226348c1dbb13c9bae2',
                             'duration': 116,
                             },
               },
              {'url': 'http://www.br.de/fernsehen/br-alpha/sendungen/kant-fuer-anfaenger/kritik-der-reinen-vernunft/kant-kritik-01-metaphysik100.html',
               'md5': '23bca295f1650d698f94fc570977dae3',
               'info_dict': {'id': 'd982c9ce-8648-4753-b358-98abb8aec43d',
                             'ext': 'mp4',
                             'title': 'Folge 1 - Metaphysik',
                             'description': 'md5:bb659990e9e59905c3d41e369db1fbe3',
                             'duration': 893,
                             'uploader': 'Eva Maria Steimle',
                             'upload_date': '20170208',
                             },
               },
              ]

    def _real_extract(self, url):
        base_url, display_id = self._match_valid_url(url).groups()
        page = self._download_webpage(url, display_id)
        xml_url = self._search_regex(
            r"return BRavFramework\.register\(BRavFramework\('avPlayer_(?:[a-f0-9-]{36})'\)\.setup\({dataURL:'(/(?:[a-z0-9\-]+/)+[a-z0-9/~_.-]+)'}\)\);",
            page,
            'XMLURL')
        xml = self._download_xml(base_url + xml_url, display_id)

        medias = []

        for xml_media in xml.findall('video') + xml.findall('audio'):
            media_id = xml_media.get('externalId')
            media = {
                'id': media_id,
                'title': xpath_text(xml_media, 'title', 'title', True),
                'duration': parse_duration(xpath_text(xml_media, 'duration')),
                'formats': self._extract_formats(xpath_element(
                    xml_media, 'assets'), media_id),
                'thumbnails': self._extract_thumbnails(xpath_element(
                    xml_media, 'teaserImage/variants'), base_url),
                'description': xpath_text(xml_media, 'desc'),
                'webpage_url': xpath_text(xml_media, 'permalink'),
                'uploader': xpath_text(xml_media, 'author'),
            }
            broadcast_date = xpath_text(xml_media, 'broadcastDate')
            if broadcast_date:
                media['upload_date'] = ''.join(
                    reversed(broadcast_date.split('.')))
            medias.append(media)

        if len(medias) > 1:
            self.report_warning(
                'found multiple medias; please '
                'report this with the video URL to http://yt-dl.org/bug')
        if not medias:
            raise ExtractorError('No media entries found')
        return medias[0]

    def _extract_formats(self, assets, media_id):
        formats = []
        for asset in assets.findall('asset'):
            format_url = xpath_text(asset, ['downloadUrl', 'url'])
            asset_type = asset.get('type')
            if asset_type.startswith('HDS'):
                formats.extend(
                    self._extract_f4m_formats(
                        format_url +
                        '?hdcore=3.2.0',
                        media_id,
                        f4m_id='hds',
                        fatal=False))
            elif asset_type.startswith('HLS'):
                formats.extend(
                    self._extract_m3u8_formats(
                        format_url,
                        media_id,
                        'mp4',
                        'm3u8_native',
                        m3u8_id='hds',
                        fatal=False))
            else:
                format_info = {
                    'ext': xpath_text(asset, 'mediaType'),
                    'width': int_or_none(xpath_text(asset, 'frameWidth')),
                    'height': int_or_none(xpath_text(asset, 'frameHeight')),
                    'tbr': int_or_none(xpath_text(asset, 'bitrateVideo')),
                    'abr': int_or_none(xpath_text(asset, 'bitrateAudio')),
                    'vcodec': xpath_text(asset, 'codecVideo'),
                    'acodec': xpath_text(asset, 'codecAudio'),
                    'container': xpath_text(asset, 'mediaType'),
                    'filesize': int_or_none(xpath_text(asset, 'size')),
                }
                format_url = self._proto_relative_url(format_url)
                if format_url:
                    http_format_info = format_info.copy()
                    http_format_info.update({
                        'url': format_url,
                        'format_id': f'http-{asset_type}',
                    })
                    formats.append(http_format_info)
                server_prefix = xpath_text(asset, 'serverPrefix')
                if server_prefix:
                    rtmp_format_info = format_info.copy()
                    rtmp_format_info.update({
                        'url': server_prefix,
                        'play_path': xpath_text(asset, 'fileName'),
                        'format_id': f'rtmp-{asset_type}',
                    })
                    formats.append(rtmp_format_info)
        return formats

    def _extract_thumbnails(self, variants, base_url):
        thumbnails = [{
            'url': base_url + xpath_text(variant, 'url'),
            'width': int_or_none(xpath_text(variant, 'width')),
            'height': int_or_none(xpath_text(variant, 'height')),
        } for variant in variants.findall('variant') if xpath_text(variant, 'url')]
        thumbnails.sort(key=lambda x: x['width'] * x['height'], reverse=True)
        return thumbnails
