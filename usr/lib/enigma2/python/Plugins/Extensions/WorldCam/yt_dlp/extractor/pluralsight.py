import collections
import json
import os
import random
import re
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    dict_get,
    float_or_none,
    int_or_none,
    parse_duration,
    parse_qs,
    qualities,
    srt_subtitles_timecode,
    try_get,
    update_url_query,
    urlencode_postdata,
)


class PluralsightBaseIE(InfoExtractor):
    _API_BASE = 'https://app.pluralsight.com'

    _GRAPHQL_EP = f'{_API_BASE}/player/api/graphql'
    _GRAPHQL_HEADERS = {
        'Content-Type': 'application/json;charset=UTF-8',
    }
    _GRAPHQL_COURSE_TMPL = '''
query BootstrapPlayer {
  rpc {
    bootstrapPlayer {
      profile {
        firstName
        lastName
        email
        username
        userHandle
        authed
        isAuthed
        plan
      }
      course(courseId: "%s") {
        name
        title
        courseHasCaptions
        translationLanguages {
          code
          name
        }
        supportsWideScreenVideoFormats
        timestamp
        modules {
          name
          title
          duration
          formattedDuration
          author
          authorized
          clips {
            authorized
            clipId
            duration
            formattedDuration
            id
            index
            moduleIndex
            moduleTitle
            name
            title
            watched
          }
        }
      }
    }
  }
}'''

    def _download_course(self, course_id, url, display_id):
        try:
            return self._download_course_rpc(course_id, url, display_id)
        except ExtractorError:
            # Old API fallback
            return self._download_json(
                'https://app.pluralsight.com/player/user/api/v1/player/payload',
                display_id, data=urlencode_postdata({'courseId': course_id}),
                headers={'Referer': url})

    def _download_course_rpc(self, course_id, url, display_id):
        response = self._download_json(
            self._GRAPHQL_EP, display_id, data=json.dumps({
                'query': self._GRAPHQL_COURSE_TMPL % course_id,
                'variables': {},
            }).encode(), headers=self._GRAPHQL_HEADERS)

        course = try_get(
            response, lambda x: x['data']['rpc']['bootstrapPlayer']['course'],
            dict)
        if course:
            return course

        raise ExtractorError(
            '{} said: {}'.format(self.IE_NAME, response['error']['message']),
            expected=True)


class PluralsightIE(PluralsightBaseIE):
    IE_NAME = 'pluralsight'
    _VALID_URL = r'https?://(?:(?:www|app)\.)?pluralsight\.com/(?:training/)?player\?'
    _LOGIN_URL = 'https://app.pluralsight.com/id/'

    _NETRC_MACHINE = 'pluralsight'

    _TESTS = [{
        'url': 'http://www.pluralsight.com/training/player?author=mike-mckeown&name=hosting-sql-server-windows-azure-iaas-m7-mgmt&mode=live&clip=3&course=hosting-sql-server-windows-azure-iaas',
        'md5': '4d458cf5cf4c593788672419a8dd4cf8',
        'info_dict': {
            'id': 'hosting-sql-server-windows-azure-iaas-m7-mgmt-04',
            'ext': 'mp4',
            'title': 'Demo Monitoring',
            'duration': 338,
        },
        'skip': 'Requires pluralsight account credentials',
    }, {
        'url': 'https://app.pluralsight.com/training/player?course=angularjs-get-started&author=scott-allen&name=angularjs-get-started-m1-introduction&clip=0&mode=live',
        'only_matching': True,
    }, {
        # available without pluralsight account
        'url': 'http://app.pluralsight.com/training/player?author=scott-allen&name=angularjs-get-started-m1-introduction&mode=live&clip=0&course=angularjs-get-started',
        'only_matching': True,
    }, {
        'url': 'https://app.pluralsight.com/player?course=ccna-intro-networking&author=ross-bagurdes&name=ccna-intro-networking-m06&clip=0',
        'only_matching': True,
    }]

    GRAPHQL_VIEWCLIP_TMPL = '''
query viewClip {
  viewClip(input: {
    author: "%(author)s",
    clipIndex: %(clipIndex)d,
    courseName: "%(courseName)s",
    includeCaptions: %(includeCaptions)s,
    locale: "%(locale)s",
    mediaType: "%(mediaType)s",
    moduleName: "%(moduleName)s",
    quality: "%(quality)s"
  }) {
    urls {
      url
      cdn
      rank
      source
    },
    status
  }
}'''

    def _perform_login(self, username, password):
        login_page = self._download_webpage(
            self._LOGIN_URL, None, 'Downloading login page')

        login_form = self._hidden_inputs(login_page)

        login_form.update({
            'Username': username,
            'Password': password,
        })

        post_url = self._search_regex(
            r'<form[^>]+action=(["\'])(?P<url>.+?)\1', login_page,
            'post url', default=self._LOGIN_URL, group='url')

        if not post_url.startswith('http'):
            post_url = urllib.parse.urljoin(self._LOGIN_URL, post_url)

        response = self._download_webpage(
            post_url, None, 'Logging in',
            data=urlencode_postdata(login_form),
            headers={'Content-Type': 'application/x-www-form-urlencoded'})

        error = self._search_regex(
            r'<span[^>]+class="field-validation-error"[^>]*>([^<]+)</span>',
            response, 'error message', default=None)
        if error:
            raise ExtractorError(f'Unable to login: {error}', expected=True)

        if all(not re.search(p, response) for p in (
                r'__INITIAL_STATE__', r'["\']currentUser["\']',
                # new layout?
                r'>\s*Sign out\s*<')):
            BLOCKED = 'Your account has been blocked due to suspicious activity'
            if BLOCKED in response:
                raise ExtractorError(
                    f'Unable to login: {BLOCKED}', expected=True)
            MUST_AGREE = 'To continue using Pluralsight, you must agree to'
            if any(
                p in response for p in (
                    MUST_AGREE,
                    '>Disagree<',
                    '>Agree<')):
                raise ExtractorError(
                    f'Unable to login: {MUST_AGREE} some documents. Go to pluralsight.com, '
                    'log in and agree with what Pluralsight requires.', expected=True)

            raise ExtractorError('Unable to log in')

    def _get_subtitles(
            self,
            author,
            clip_idx,
            clip_id,
            lang,
            name,
            duration,
            video_id):
        captions = None
        if clip_id:
            captions = self._download_json(
                f'{self._API_BASE}/transcript/api/v1/caption/json/{clip_id}/{lang}',
                video_id,
                'Downloading captions JSON',
                'Unable to download captions JSON',
                fatal=False)
        if not captions:
            captions_post = {
                'a': author,
                'cn': int(clip_idx),
                'lc': lang,
                'm': name,
            }
            captions = self._download_json(
                f'{self._API_BASE}/player/retrieve-captions', video_id,
                'Downloading captions JSON', 'Unable to download captions JSON',
                fatal=False, data=json.dumps(captions_post).encode(),
                headers={'Content-Type': 'application/json;charset=utf-8'})
        if captions:
            return {
                lang: [{
                    'ext': 'json',
                    'data': json.dumps(captions),
                }, {
                    'ext': 'srt',
                    'data': self._convert_subtitles(duration, captions),
                }],
            }

    @staticmethod
    def _convert_subtitles(duration, subs):
        srt = ''
        TIME_OFFSET_KEYS = ('displayTimeOffset', 'DisplayTimeOffset')
        TEXT_KEYS = ('text', 'Text')
        for num, current in enumerate(subs):
            current = subs[num]
            start, text = (
                float_or_none(
                    dict_get(
                        current, TIME_OFFSET_KEYS, skip_false_values=False)), dict_get(
                    current, TEXT_KEYS))
            if start is None or text is None:
                continue
            end = duration if num == len(subs) - 1 else float_or_none(
                dict_get(subs[num + 1], TIME_OFFSET_KEYS, skip_false_values=False))
            if end is None:
                continue
            srt += os.linesep.join(
                (f'{num}',
                 f'{srt_subtitles_timecode(start)} --> {srt_subtitles_timecode(end)}',
                 text,
                 os.linesep,
                 ))
        return srt

    def _real_extract(self, url):
        qs = parse_qs(url)

        author = qs.get('author', [None])[0]
        name = qs.get('name', [None])[0]
        clip_idx = qs.get('clip', [None])[0]
        course_name = qs.get('course', [None])[0]

        if any(not f for f in (author, name, clip_idx, course_name)):
            raise ExtractorError('Invalid URL', expected=True)

        display_id = f'{name}-{clip_idx}'

        course = self._download_course(course_name, url, display_id)

        collection = course['modules']

        clip = None

        for module_ in collection:
            if name in (module_.get('moduleName'), module_.get('name')):
                for clip_ in module_.get('clips', []):
                    clip_index = clip_.get('clipIndex')
                    if clip_index is None:
                        clip_index = clip_.get('index')
                    if clip_index is None:
                        continue
                    if str(clip_index) == clip_idx:
                        clip = clip_
                        break

        if not clip:
            raise ExtractorError('Unable to resolve clip')

        title = clip['title']
        clip_id = clip.get('clipName') or clip.get('name') or clip['clipId']

        QUALITIES = {
            'low': {'width': 640, 'height': 480},
            'medium': {'width': 848, 'height': 640},
            'high': {'width': 1024, 'height': 768},
            'high-widescreen': {'width': 1280, 'height': 720},
        }

        QUALITIES_PREFERENCE = ('low', 'medium', 'high', 'high-widescreen')
        quality_key = qualities(QUALITIES_PREFERENCE)

        AllowedQuality = collections.namedtuple(
            'AllowedQuality', ['ext', 'qualities'])

        ALLOWED_QUALITIES = (
            AllowedQuality('webm', ['high']),
            AllowedQuality('mp4', ['low', 'medium', 'high']),
        )

        # Some courses also offer widescreen resolution for high quality (see
        # https://github.com/ytdl-org/youtube-dl/issues/7766)
        widescreen = course.get('supportsWideScreenVideoFormats') is True
        best_quality = 'high-widescreen' if widescreen else 'high'
        if widescreen:
            for allowed_quality in ALLOWED_QUALITIES:
                allowed_quality.qualities.append(best_quality)

        # In order to minimize the number of calls to ViewClip API and reduce
        # the probability of being throttled or banned by Pluralsight we will request
        # only single format until formats listing was explicitly requested.
        if self.get_param('listformats', False):
            allowed_qualities = ALLOWED_QUALITIES
        else:
            def guess_allowed_qualities():
                req_format = self.get_param('format') or 'best'
                req_format_split = req_format.split('-', 1)
                if len(req_format_split) > 1:
                    req_ext, req_quality = req_format_split
                    req_quality = '-'.join(req_quality.split('-')[:2])
                    for allowed_quality in ALLOWED_QUALITIES:
                        if req_ext == allowed_quality.ext and req_quality in allowed_quality.qualities:
                            return (AllowedQuality(req_ext, (req_quality, )), )
                req_ext = 'webm' if self.get_param(
                    'prefer_free_formats') else 'mp4'
                return (AllowedQuality(req_ext, (best_quality, )), )
            allowed_qualities = guess_allowed_qualities()

        formats = []
        for ext, qualities_ in allowed_qualities:
            for quality in qualities_:
                f = QUALITIES[quality].copy()
                clip_post = {
                    'author': author,
                    'includeCaptions': 'false',
                    'clipIndex': int(clip_idx),
                    'courseName': course_name,
                    'locale': 'en',
                    'moduleName': name,
                    'mediaType': ext,
                    'quality': '%dx%d' % (f['width'], f['height']),
                }
                format_id = f'{ext}-{quality}'

                try:
                    viewclip = self._download_json(
                        self._GRAPHQL_EP, display_id,
                        f'Downloading {format_id} viewclip graphql',
                        data=json.dumps({
                            'query': self.GRAPHQL_VIEWCLIP_TMPL % clip_post,
                            'variables': {},
                        }).encode(),
                        headers=self._GRAPHQL_HEADERS)['data']['viewClip']
                except ExtractorError:
                    # Still works but most likely will go soon
                    viewclip = self._download_json(
                        f'{self._API_BASE}/video/clips/viewclip', display_id,
                        f'Downloading {format_id} viewclip JSON', fatal=False,
                        data=json.dumps(clip_post).encode(),
                        headers={'Content-Type': 'application/json;charset=utf-8'})

                # Pluralsight tracks multiple sequential calls to ViewClip API and start
                # to return 429 HTTP errors after some time (see
                # https://github.com/ytdl-org/youtube-dl/pull/6989). Moreover it may even lead
                # to account ban (see https://github.com/ytdl-org/youtube-dl/issues/6842).
                # To somewhat reduce the probability of these consequences
                # we will sleep random amount of time before each call to
                # ViewClip.
                self._sleep(
                    random.randint(
                        5,
                        10),
                    display_id,
                    '%(video_id)s: Waiting for %(timeout)s seconds to avoid throttling')

                if not viewclip:
                    continue

                clip_urls = viewclip.get('urls')
                if not isinstance(clip_urls, list):
                    continue

                for clip_url_data in clip_urls:
                    clip_url = clip_url_data.get('url')
                    if not clip_url:
                        continue
                    cdn = clip_url_data.get('cdn')
                    clip_f = f.copy()
                    clip_f.update({
                        'url': clip_url,
                        'ext': ext,
                        'format_id': f'{format_id}-{cdn}' if cdn else format_id,
                        'quality': quality_key(quality),
                        'source_preference': int_or_none(clip_url_data.get('rank')),
                    })
                    formats.append(clip_f)

        duration = int_or_none(
            clip.get('duration')) or parse_duration(
            clip.get('formattedDuration'))

        # TODO: other languages?
        subtitles = self.extract_subtitles(
            author,
            clip_idx,
            clip.get('clipId'),
            'en',
            name,
            duration,
            display_id)

        return {
            'id': clip_id,
            'title': title,
            'duration': duration,
            'creator': author,
            'formats': formats,
            'subtitles': subtitles,
        }


class PluralsightCourseIE(PluralsightBaseIE):
    IE_NAME = 'pluralsight:course'
    _VALID_URL = r'https?://(?:(?:www|app)\.)?pluralsight\.com/(?:library/)?courses/(?P<id>[^/]+)'
    _TESTS = [{
        # Free course from Pluralsight Starter Subscription for Microsoft TechNet
        # https://offers.pluralsight.com/technet?loc=zTS3z&prod=zOTprodz&tech=zOttechz&prog=zOTprogz&type=zSOz&media=zOTmediaz&country=zUSz
        'url': 'http://www.pluralsight.com/courses/hosting-sql-server-windows-azure-iaas',
        'info_dict': {
            'id': 'hosting-sql-server-windows-azure-iaas',
            'title': 'Hosting SQL Server in Microsoft Azure IaaS Fundamentals',
            'description': 'md5:61b37e60f21c4b2f91dc621a977d0986',
        },
        'playlist_count': 31,
    }, {
        # available without pluralsight account
        'url': 'https://www.pluralsight.com/courses/angularjs-get-started',
        'only_matching': True,
    }, {
        'url': 'https://app.pluralsight.com/library/courses/understanding-microsoft-azure-amazon-aws/table-of-contents',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        course_id = self._match_id(url)

        # TODO: PSM cookie

        course = self._download_course(course_id, url, course_id)

        title = course['title']
        course_name = course['name']
        course_data = course['modules']
        description = course.get(
            'description') or course.get('shortDescription')

        entries = []
        for num, module in enumerate(course_data, 1):
            author = module.get('author')
            module_name = module.get('name')
            if not author or not module_name:
                continue
            for clip in module.get('clips', []):
                clip_index = int_or_none(clip.get('index'))
                if clip_index is None:
                    continue
                clip_url = update_url_query(
                    f'{self._API_BASE}/player', query={
                        'mode': 'live',
                        'course': course_name,
                        'author': author,
                        'name': module_name,
                        'clip': clip_index,
                    })
                entries.append({
                    '_type': 'url_transparent',
                    'url': clip_url,
                    'ie_key': PluralsightIE.ie_key(),
                    'chapter': module.get('title'),
                    'chapter_number': num,
                    'chapter_id': module.get('moduleRef'),
                })

        return self.playlist_result(entries, course_id, title, description)
