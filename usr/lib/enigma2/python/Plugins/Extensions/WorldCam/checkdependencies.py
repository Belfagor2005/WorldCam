import subprocess
from shutil import which
import sys

REQUIRED_PACKAGES = {
    "ffmpeg": "ffmpeg",
    "exteplayer3": "exteplayer3",
    "streamlink": "streamlink",
    "yt-dlp": "yt-dlp",
    "youtube-dl": "youtube-dl",
    "gstplayer": "gst-play-1.0",
    "requests": "requests",
    "serviceapp": "/etc/enigma2/serviceapp.conf",
    "streamlinkwrapper": "/usr/lib/enigma2/python/Plugins/Extensions/StreamlinkWrapper",
    "ytdlpwrapper": "/usr/lib/enigma2/python/Plugins/Extensions/YtdlpWrapper",
    "ytdlwrapper": "/usr/lib/enigma2/python/Plugins/Extensions/YtdlWrapper",
}

OPKG_PACKAGES = [
    "ffmpeg",
    "exteplayer3",
    "enigma2-plugin-systemplugins-serviceapp",
    "gstplayer",
    "streamlink",
    "enigma2-plugin-extensions-streamlinkwrapper",
    "enigma2-plugin-extensions-ytdlpwrapper",
    "enigma2-plugin-extensions-ytdlwrapper",
    "{py}-yt-dlp",
    "{py}-youtube-dl",
    "{py}-requests",
    "gstreamer1.0-plugins-good",
    "gstreamer1.0-plugins-bad",
    "gstreamer1.0-plugins-ugly",
    "gstreamer1.0-libav"
]


def get_python_variant():
    return "python3" if which("python3") else "python"


def check_requirements(logger=None):
    """
    Check optional dependencies needed for YouTube playback.
    Returns a list of missing component names (str).
    """
    missing = []

    # Check yt_dlp (plugin path only, non di sistema)
    try:
        plugin_path = "/usr/lib/enigma2/python/Plugins/Extensions/WorldCam/yt_dlp"
        if plugin_path not in sys.path:
            sys.path.append(plugin_path)
        from yt_dlp import YoutubeDL  # noqa: F401
    except ImportError:
        missing.append("yt-dlp")

    # Check streamlink (binary)
    if which("streamlink") is None:
        missing.append("streamlink")

    # Check requests (Python module)
    try:
        import requests  # noqa: F401
    except ImportError:
        missing.append("requests")

    if logger and missing:
        logger.warning("Missing optional components: " + ", ".join(missing))
    return missing


def install_missing_packages(missing, logger=None):
    python_variant = get_python_variant()
    try:
        subprocess.call(["opkg", "update"])
        for pkg in OPKG_PACKAGES:
            name = pkg.replace("{py}", python_variant)
            base = name.split("/")[-1].replace("enigma2-plugin-extensions-", "").replace("{py}-", "").replace(python_variant + "-", "")
            if base in missing or base.split("-")[0] in missing:
                cmd = ["opkg", "install", name]
                if logger:
                    logger.info("Installing: " + " ".join(cmd))
                subprocess.call(cmd)
        return True
    except Exception as e:
        if logger:
            logger.error("Failed to install packages: " + str(e))
        return False
