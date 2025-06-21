#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

"""
#########################################################
#                                                       #
#  Worldcam Cam Scraper from Plugin                     #
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

from enigma import eTimer
from re import search, escape, findall, DOTALL, IGNORECASE, sub
from os import listdir
from os.path import (
    # basename,
    # dirname,
    # isdir,
    # getsize,
    exists,
    isfile,
    join,
)

from .utils import (
    Logger,
    Request,
    HTTPError,
    URLError,
    urlopen,
    quote,
    urlparse,
    urlunparse
)

try:
    unicode
except NameError:
    unicode = str


"""

1. **WorldCamContinentScreen**
   * `self.scraper.get_continents()
   *  get_countries_by_continent

2. **WorldCamCountryScreen**
   * `self.scraper.get_countries()`

3. **WorldCamCategoryScreen**
   * `self.scraper.get_categories()`

4. **WorldCamTopScreen**
   * `self.scraper.get_top_webcams()`

5. **WorldCamLocationScreen**
   * `self.scraper.get_locations(self.country["url"])`

6. **WorldCamWebcamScreen**
   * `self.scraper.get_webcams(self.location["url"])`

7. **WorldCamLocal**
   * `self.scraper.get_local_playlists(playlists_path)
"""


def safe_log_string(text):
    """Safely encode strings for logging"""
    if isinstance(text, unicode):
        return text.encode('utf-8', 'replace')
    return text


# Update the safe_encode_url function
def safe_encode_url(url):
    """Safely encode URLs with non-ASCII characters"""
    if isinstance(url, unicode):
        try:
            parsed = urlparse(url)
            netloc = parsed.netloc.encode('idna')
            path = quote(parsed.path.encode('utf-8'), safe='/-_')
            query = quote(parsed.query.encode('utf-8'), safe='=&')
            return urlunparse((
                parsed.scheme,
                netloc,
                path,
                parsed.params,
                query,
                parsed.fragment
            ))
        except Exception:
            # Fallback to UTF-8 encoding
            return url.encode('utf-8', 'ignore')
    return url


class SkylineScraper:
    """
    A scraper class for extracting webcam streams and related information
    from skylinewebcams.com, supporting caching and multi-language.
    """

    BASE_URL = "https://www.skylinewebcams.com"
    HEADERS = {"User-Agent": "Mozilla/5.0",
               "Accept-Language": "en-US,en;q=0.5"}

    def __init__(self, lang="en"):
        """
        Initialize scraper with language and setup cache and timer.
        """
        self.logger = Logger()
        self.logger.info("Entering __init__")
        self.lang = lang
        self.cache = {}

        self.timer = eTimer()
        self.timer.callback.append(self.clear_cache)
        self.timer.start(3600000)  # Clear cache every hour (3600000 ms)

    def clear_cache(self):
        """Clear the internal content cache."""
        self.logger.info("Entering clear_cache")
        self.cache = {}

    def get_full_url(self, path):
        """
        Return a full absolute URL with proper formatting
        """
        self.logger.info("Entering get_full_url with path: " + path)

        if path.startswith("http"):
            return path

        # Handle relative paths correctly
        if path.startswith("//"):
            return "https:" + path

        # Handle absolute paths
        if path.startswith("/"):
            return self.BASE_URL + path

        # Handle relative paths
        return self.BASE_URL + "/" + path

    def is_direct_stream(self, url):
        """Check if URL is a direct video stream"""
        video_extensions = [
            '.m3u8',
            '.mp4',
            '.m4v',
            '.flv',
            '.ts',
            '.mov',
            '.mkv']
        return any(url.lower().endswith(ext)
                   for ext in video_extensions) or "m3u8" in url.lower()

    def get_stream_url(self, webcam_page_url):
        """
        Extract the streaming URL from a webcam page.
        """
        self.logger.info("Entering get_stream_url")
        content = self.fetch(webcam_page_url, use_cache=False)
        if not content:
            self.logger.warning(
                "No content fetched for URL: " +
                webcam_page_url)
            return None
        try:
            # Pattern 1: Standard HLS stream
            hls_match = search(r"source:\s*'livee\.m3u8\?a=([^']+)'", content)
            if hls_match:
                video_id = hls_match.group(1)
                self.logger.info(
                    "Found HLS livee.m3u8 stream with video ID: " + video_id)
                return "https://hd-auth.skylinewebcams.com/live.m3u8?a=" + video_id

            # Pattern 2: YouTube video ID
            yt_match = search(r"videoId:\s*'([^']+)'", content)
            if yt_match:
                video_id = yt_match.group(1)
                self.logger.info("Found YouTube video ID: " + video_id)
                return "https://www.youtube.com/watch?v=" + video_id

            # Pattern 3: JW Player file URL
            jw_match = search(
                r'player\.setup\({.*?file:\s*"([^"]+)"', content, DOTALL)
            if jw_match:
                self.logger.info("Found JW Player file URL")
                return jw_match.group(1)

            # Pattern 4: New HLS format
            hls_match2 = search(r"hls:\s*'([^']+)'", content)
            if hls_match2:
                self.logger.info("Found new HLS format URL")
                return hls_match2.group(1)

            # Pattern 5: Direct video source from <video> tag
            video_match = search(r'<video[^>]+src="([^"]+)"', content)
            if video_match:
                url = self.get_full_url(video_match.group(1))
                self.logger.info("Found direct video source: " + url)
                return url

            self.logger.warning(
                "No stream URL found in the page: " +
                webcam_page_url)
        except Exception as e:
            self.logger.error(
                "Error parsing stream URL from {}: {}".format(
                    webcam_page_url, str(e)))
        return None

    def fetch(self, url, use_cache=True):
        """
        Fetch the content of the URL with enhanced encoding handling
        """
        self.logger.info("Entering fetch for URL: " + str(url))

        safe_url = str(url)

        if use_cache and safe_url in self.cache:
            self.logger.info("Using cached content for: " + safe_url)
            return self.cache[safe_url]

        self.logger.info(f"Fetching URL: {safe_url}")

        try:
            req = Request(safe_url, headers=self.HEADERS)
            response = urlopen(req, timeout=15)

            if response is None:
                self.logger.error("No response received for URL: " + safe_url)
                return ""

            content = response.read()
            if not content:
                self.logger.error("Empty response body for URL: " + safe_url)
                return ""

            try:
                decoded_content = content.decode("utf-8", errors="replace")
            except Exception as e:
                self.logger.error(f"Exception Unexpected error: {str(e)}")
                try:
                    decoded_content = content.decode("latin-1")
                except BaseException:
                    decoded_content = content.decode("utf-8", errors="ignore")

            if use_cache:
                self.cache[safe_url] = decoded_content
                self.logger.info("Cached content for URL: " + safe_url)

            return decoded_content

        except (HTTPError, URLError) as e:
            self.logger.error(f"Fetch error: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")

        return ""

    @staticmethod
    def parse_countries(html, language="en"):
        """
        Extract country links and names from the main page.
        """
        Logger().info("Entering parse_countries")  # static method: use fresh Logger
        pattern = r'<a href="(/' + language + \
            r'/webcam/[^"]+\.html)">([^<]+)</a>'
        try:
            result = findall(pattern, html, IGNORECASE)
            Logger().info("Found {} countries".format(len(result)))
            return result
        except Exception as e:
            Logger().error("Error parsing countries: " + str(e))
            return []

    @staticmethod
    def parse_categories(content, language="en"):
        """
        Extract main categories from homepage HTML.
        """
        Logger().info("Entering parse_categories")
        pattern = r'<a href="(/' + language + \
            r'/[^"]+)"[^>]*>\s*<p class="tcam">([^<]+)</p>'
        try:
            result = findall(pattern, content)
            Logger().info("Found {} categories".format(len(result)))
            return result
        except Exception as e:
            Logger().error("Error parsing categories: " + str(e))
            return []

    @staticmethod
    def parse_top_webcams(content, language="en"):
        """
        Extract featured webcams from the homepage.
        """
        Logger().info("Entering parse_top_webcams")
        pattern = (
            r'<a href="(/' + escape(language) + r'/webcam/[^"]+)"[^>]*>'
            r'.*?<img src="([^"]+)"[^>]*alt="([^"]+)"'
        )
        try:
            result = findall(pattern, content, DOTALL | IGNORECASE)
            Logger().info("Found {} top webcams".format(len(result)))
            return result
        except Exception as e:
            Logger().error("Error parsing top webcams: " + str(e))
            return []

    @staticmethod
    def parse_webcams(html, language="en"):
        """
        Extract webcams from location page HTML.
        Combines new structure detection with old reliable parsing techniques.
        """
        Logger().info("Entering parse_webcams")
        # webcams = []

        # Main pattern for webcams
        pattern = (
            r'<a href="([^"]+)" class="col-xs-12 col-sm-6 col-md-4">\s*'
            r'<div class="cam-light">\s*'
            r'<img src="([^"]+)"[^>]*alt="([^"]+)"[^>]*>\s*'
            r'<p class="tcam">([^<]+)</p>'
        )

        # Pattern fallback
        fallback_pattern = r'<a href="(/{}/webcam/[^"]+)"[^>]*>.*?<img src="([^"]+)"[^>]*alt="([^"]+)"'.format(
            language)

        try:
            # Try with the main pattern
            matches = findall(pattern, html, DOTALL)
            if matches:
                Logger().info(
                    f"Found {len(matches)} webcams using main pattern")
                return matches

            # Fallback to the old pattern
            matches = findall(fallback_pattern, html, DOTALL)
            Logger().info(
                f"Found {len(matches)} webcams using fallback pattern")
            return matches

        except Exception as e:
            Logger().error(f"Error parsing webcams: {str(e)}")
            return []

    @staticmethod
    def parse_locations(content, language="en", country_code=None):
        """
        Parse locations from the given HTML content.
        """
        Logger().info("Entering parse_locations")
        locations = []

        # Pattern for location buttons
        location_pattern = r'<a href="([^"]+)" class="btn btn-primary tag">([^<]+)</a>'

        # Pattern for webcams in the grid
        webcam_pattern = (
            r'<a href="([^"]+)" class="col-xs-12 col-sm-6 col-md-4">\s*'
            r'<div class="cam-light">\s*'
            r'<img src="([^"]+)"[^>]*alt="([^"]+)"[^>]*>\s*'
            r'<p class="tcam">([^<]+)</p>'
        )

        try:
            # Extract locations from buttons
            location_matches = findall(location_pattern, content)
            for match in location_matches:
                location_url = match[0]
                location_name = match[1]
                locations.append((location_url, location_name))
                Logger().info(
                    f"Location found: {location_name} -> {location_url}")

            # If no buttons found, fallback to extracting webcams directly
            if not locations:
                webcam_matches = findall(webcam_pattern, content, DOTALL)
                for match in webcam_matches:
                    location_url = match[0]
                    # Extract location name from URL
                    parts = location_url.split('/')
                    if len(parts) >= 5:
                        location_name = parts[4].replace(
                            '.html', '').replace('-', ' ').title()
                        locations.append((location_url, location_name))
                        Logger().info(
                            f"Fallback location: {location_name} -> {location_url}")

            return locations

        except Exception as e:
            Logger().error(f"Error parsing locations: {str(e)}")
            return []

    @staticmethod
    def parse_local_playlist_file(path):
        """
        Parse playlist file with flexible format.
        """
        logger = Logger()
        webcams = []

        if not exists(path):
            logger.error(f"Playlist file not found: {path}")
            return webcams

        try:
            with open(path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    # New: Flexible parsing for different formats
                    if "###" in line:
                        parts = line.split("###")
                        parts = [p.strip() for p in parts if p.strip()]

                        if len(parts) >= 2:
                            # Last part is always the URL
                            # url = parts[-1]
                            url = parts[-1].replace("###", "").strip()

                            # Name is everything before the URL
                            name = " ".join(parts[:-1])

                            # Clean YouTube URLs
                            if "youtube.com" in url or "youtu.be" in url:
                                # Remove any "URL:" text and trailing delimiters
                                # url = sub(r'(URL:)|(###)', '', url,
                                # flags=IGNORECASE)
                                url = sub(
                                    r'URL:\s*', '', url, flags=IGNORECASE).strip()
                                # Extract just the video ID
                                match = search(
                                    r'(?:v=|youtu\.be/|embed/)([a-zA-Z0-9_-]{11})', url)
                                if match:
                                    url = f"https://www.youtube.com/watch?v={match.group(1)}"

                            webcams.append({
                                "group": "User List",
                                "name": name,
                                "url": url
                            })
                            continue

                    # Traditional formats with three parts separated by various
                    # delimiters
                    if ":::" in line:
                        parts = line.split(":::", 2)
                    elif ";;" in line:
                        parts = line.split(";;", 2)
                    elif "::" in line:
                        parts = line.split("::", 2)
                    elif ";" in line:
                        parts = line.split(";", 2)
                    else:
                        continue

                    if len(parts) >= 3:
                        webcams.append({
                            "group": parts[0].strip(),
                            "name": parts[1].strip(),
                            "url": parts[2].strip()
                        })
                    elif len(parts) == 2:
                        webcams.append({
                            "group": "User List",
                            "name": parts[0].strip(),
                            "url": parts[1].strip()
                        })
                    else:
                        logger.warning(f"Skipping line: {line}")

            logger.info(f"Parsed {len(webcams)} webcams from {path}")
            return webcams

        except Exception as e:
            logger.error(f"Error parsing playlist {path}: {str(e)}")
            return []

    @staticmethod
    def clean_html_entities(text):
        """Clean HTML entities like &amp; &quot; etc."""
        import html
        return html.unescape(text)

    @staticmethod
    def _parse_text_playlist(content, logger=None):
        """
        Parse playlist content supporting multiple formats.
        """
        channels = []
        lines = content.splitlines()
        line_count = 0

        for line in lines:
            line = line.strip()
            line_count += 1

            if not line or line.startswith('#'):
                continue

            # Support different separators
            separators = ['###', '|', ';', ',']
            parts = None

            for sep in separators:
                if sep in line:
                    parts = line.split(sep, 2)
                    break

            if not parts:
                parts = [line]

            # Extract data fields
            name = "Unknown"
            url = ""
            logo = ""

            if len(parts) >= 2:
                name = parts[0].strip()
                url = parts[1].strip()
                if len(parts) > 2:
                    logo = parts[2].strip()
            elif len(parts) == 1:
                url = parts[0].strip()

            if not url:
                if logger:
                    logger.warning(f"Invalid line {line_count}: Missing URL")
                continue

            channels.append({
                'name': name,
                'url': url,
                'type': 'stream',
                'logo': logo
            })

        if logger:
            logger.info(f"Parsed {len(channels)} channels from playlist")
        return channels

    def get_continents(self):
        """
        Get continents from the main page.
        """
        self.logger.info("Entering get_continents")
        url = self.BASE_URL + "/" + self.lang
        html = self.fetch(url)
        continents = []

        continent_pattern = r'<div class="continent\s+(\w+)"><strong>([^<]+)</strong></div>(.*?)</div>\s*</div>'
        country_pattern = r'<a href="(/' + self.lang + \
            r'/webcam/[^"]+\.html)">([^<]+)</a>'

        try:
            matches = findall(continent_pattern, html, DOTALL | IGNORECASE)
            for match in matches:
                continent_class = match[0]
                continent_name = match[1]
                continent_html = match[2]

                countries = []
                country_matches = findall(
                    country_pattern, continent_html, IGNORECASE)
                for path, name in country_matches:
                    full_url = self.BASE_URL + path
                    countries.append({"name": name, "url": full_url})

                continents.append({
                    "name": continent_name,
                    "class": continent_class,
                    "countries": sorted(countries, key=lambda c: c["name"].lower())
                })
            return continents
        except Exception as e:
            self.logger.error("Error in get_continents: " + str(e))
            return []

    def get_countries_by_continent(self, continent_url):
        """
        Get countries for a specific continent
        """
        Logger().info(f"Entering get_countries_by_continent: {continent_url}")
        html = self.fetch(continent_url)
        countries = []

        # Pattern to find country links
        country_pattern = r'<a href="(/' + self.lang + \
            r'/webcam/[^"]+\.html)">([^<]+)</a>'
        try:
            matches = findall(country_pattern, html, IGNORECASE)
            for path, name in matches:
                full_url = self.BASE_URL + path
                countries.append({"name": name, "url": full_url})
            return sorted(countries, key=lambda c: c["name"].lower())
        except Exception as e:
            Logger().info("Error in get_countries_by_continent: " + str(e))
            return []

    def get_countries(self, category_url=None):
        """
        Get countries from a category page or homepage.
        """
        self.logger.info("Entering get_countries")
        url = category_url or self.BASE_URL
        html = self.fetch(url)
        countries = []
        try:
            for path, name in self.parse_countries(html, self.lang):
                full_url = self.BASE_URL + path
                self.logger.info(
                    "Country found: {} -> {}".format(name, full_url))
                countries.append({"name": name, "url": full_url})
        except Exception as e:
            self.logger.error("Error in get_countries: " + str(e))
        return countries

    def get_categories(self):
        """
        Get main categories from homepage.
        """
        self.logger.info("Entering get_categories")
        html = self.fetch(self.BASE_URL + "/" + self.lang)

        categories = []
        try:
            for path, name in self.parse_categories(html, self.lang):
                full_url = self.BASE_URL + path
                self.logger.info(
                    "Category found: {} -> {}".format(name, full_url))
                categories.append({"name": name, "url": full_url})
        except Exception as e:
            self.logger.error("Error in get_categories: " + str(e))
        return categories

    def get_top_webcams(self):
        """
        Get featured webcams from the homepage.
        """
        self.logger.info("Entering get_top_webcams")
        html = self.fetch(self.BASE_URL + "/" + self.lang)
        webcams = []
        try:
            for path, thumb, name in self.parse_top_webcams(html, self.lang):
                full_url = self.BASE_URL + path
                self.logger.info(
                    "Top webcam found: {} -> {}".format(name, full_url))
                webcams.append(
                    {"name": name, "url": full_url, "thumbnail": thumb})
        except Exception as e:
            self.logger.error("Error in get_top_webcams: " + str(e))
        return webcams

    def get_locations(self, country_url):
        """
        Fetch and parse the list of locations for a given country URL.
        """
        self.logger.info(f"Processing country: {country_url}")
        content = self.fetch(country_url)
        self.logger.info(f"Country page length: {len(content)}")

        locations = []
        location_data = self.parse_locations(content, self.lang)

        for url, name in location_data:
            full_url = self.get_full_url(url)
            locations.append({
                "name": name,
                "url": full_url
            })

        self.logger.info(f"Loaded {len(locations)} locations")
        return locations

    def get_local_playlists(self, playlists_path):
        """
        Return list of filenames in playlists directory.
        """
        self.logger.info(
            "Entering get_local_playlists for path: " +
            playlists_path)
        user_lists = []

        if not exists(playlists_path):
            self.logger.error(
                f"Playlists directory not found: {playlists_path}")
            return user_lists

        try:
            for filename in listdir(playlists_path):
                full_path = join(playlists_path, filename)
                if isfile(full_path) and filename.lower().endswith(
                        ('.txt', '.m3u', '.list')):
                    user_lists.append(filename)
            return user_lists
        except Exception as e:
            self.logger.error(f"Error reading playlists directory: {str(e)}")
            return user_lists

    def get_webcams(self, location_url):
        """
        Fetch and parse webcams from a given location URL.
        """
        self.logger.info(f"Processing location: {location_url}")

        # Apply known URL corrections (for test)
        if "albania" in location_url.lower():
            location_url = location_url.replace(
                "vlorë", "valona").replace(
                "vlore", "valona")

        html = self.fetch(location_url)
        webcams = []

        try:
            for item in self.parse_webcams(html, self.lang):
                # Handle both formats
                if len(item) == 4:  # New format: (path, thumb, alt, name)
                    path, thumb, alt, name = item
                else:  # Old format: (path, thumb, alt)
                    path, thumb, alt = item
                    name = alt

                # Clean HTML entities
                name = self.clean_html_entities(name)
                alt = self.clean_html_entities(alt)

                # Build full URL
                url = self.get_full_url(path)

                webcams.append({
                    "url": url,
                    "thumbnail": thumb,
                    "alt": alt,
                    "name": name
                })

                self.logger.info(f"Webcam added: {name}")

        except Exception as e:
            self.logger.error(f"Error processing webcams: {str(e)}")

        return webcams
