#!/bin/bash

## setup command=wget -q --no-check-certificate https://raw.githubusercontent.com/Belfagor2005/WorldCam/main/installer.sh -O - | /bin/sh

## Only These 2 lines to edit with new version ######
version='6.1'
changelog='\nFix it - screen\nIf you don t like this plugin, don t use it or offer beir ;)'
##############################################################

TMPPATH=/tmp/WorldCam-main
FILEPATH=/tmp/main.tar.gz

# Determine plugin path based on architecture
if [ ! -d /usr/lib64 ]; then
    PLUGINPATH=/usr/lib/enigma2/python/Plugins/Extensions/WorldCam
else
    PLUGINPATH=/usr/lib64/enigma2/python/Plugins/Extensions/WorldCam
fi

# Cleanup function
cleanup() {
    [ -d "$TMPPATH" ] && rm -rf "$TMPPATH"
    [ -f "$FILEPATH" ] && rm -f "$FILEPATH"
    [ -f "/tmp/worldcam.tar.gz" ] && rm -f "/tmp/worldcam.tar.gz"
}

# Check package manager type
if [ -f /var/lib/dpkg/status ]; then
    STATUS=/var/lib/dpkg/status
    OSTYPE=DreamOs
    PKG_MANAGER="apt-get"
else
    STATUS=/var/lib/opkg/status
    OSTYPE=Dream
    PKG_MANAGER="opkg"
fi

echo ""
cleanup

# Install wget if missing
if ! command -v wget >/dev/null 2>&1; then
    echo "Installing wget..."
    if [ "$OSTYPE" = "DreamOs" ]; then
        apt-get update && apt-get install -y wget
    else
        opkg update && opkg install wget
    fi
fi

# Detect Python version
if python --version 2>&1 | grep -q '^Python 3\.'; then
    echo "Python3 image detected"
    PYTHON=PY3
    Packagesix=python3-six
    Packagerequests=python3-requests
else
    echo "Python2 image detected"
    PYTHON=PY2
    Packagerequests=python-requests
fi

# Install required packages
install_pkg() {
    local pkg=$1
    if ! grep -qs "Package: $pkg" "$STATUS"; then
        echo "Installing $pkg..."
        if [ "$OSTYPE" = "DreamOs" ]; then
            apt-get update && apt-get install -y "$pkg"
        else
            opkg update && opkg install "$pkg"
        fi
    fi
}

[ "$PYTHON" = "PY3" ] && install_pkg "$Packagesix"
install_pkg "$Packagerequests"

# Download and install plugin
mkdir -p "$TMPPATH"
cd "$TMPPATH" || exit 1
set -e

echo -e "\n# Your image is ${OSTYPE}\n"

# Install additional dependencies for non-DreamOs systems
if [ "$OSTYPE" != "DreamOs" ]; then
    for pkg in ffmpeg exteplayer3 gstplayer enigma2-plugin-systemplugins-serviceapp; do
        install_pkg "$pkg"
    done
fi

echo "Downloading WorldCam..."
wget --no-check-certificate 'https://github.com/Belfagor2005/WorldCam/archive/refs/heads/main.tar.gz' -O "$FILEPATH"
if [ $? -ne 0 ]; then
    echo "Failed to download WorldCam package!"
    exit 1
fi

tar -xzf "$FILEPATH" -C /tmp/
cp -r /tmp/WorldCam-main/usr/* /usr/
set +e

# Verify installation
if [ ! -d "$PLUGINPATH" ]; then
    echo "Error: Plugin installation failed!"
    cleanup
    exit 1
fi

# Install yt-dlp and dependencies
echo "Installing yt-dlp and required dependencies..."
[ -e "/usr/bin/python3" ] && PY="python3" || PY="python"

opkg update && \
opkg install \
    ffmpeg \
    exteplayer3 \
    enigma2-plugin-systemplugins-serviceapp \
    gstplayer \
    streamlink \
    enigma2-plugin-extensions-streamlinkwrapper \
    enigma2-plugin-extensions-streamlinkproxyv \
    enigma2-plugin-extensions-ytdlpwrapper \
    enigma2-plugin-extensions-ytdlwrapper \
    streamlink \
    python3-re \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    ${PY}-requests \
    ${PY}-yt-dlp \
    ${PY}-youtube-dl

# Create YouTube cookies file
mkdir -p /etc/enigma2
echo -e "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t2147483647\tCONSENT\tYES+cb.20210615-14-p0.it+FX+294\n.youtube.com\tTRUE\t/\tTRUE\t2147483647\tPREF\tf1=50000000" > /etc/enigma2/yt_cookies.txt
echo "yt-dlp installation done."

# Cleanup
cleanup
sync

# System info
FILE="/etc/image-version"
box_type=$(head -n 1 /etc/hostname 2>/dev/null || echo "Unknown")
distro_value=$(grep '^distro=' "$FILE" 2>/dev/null | awk -F '=' '{print $2}')
distro_version=$(grep '^version=' "$FILE" 2>/dev/null | awk -F '=' '{print $2}')
python_vers=$(python --version 2>&1)

cat <<EOF
#########################################################
#               INSTALLED SUCCESSFULLY                  #
#                developed by LULULLA                   #
#               https://corvoboys.org                   #
#########################################################
#           your Device will RESTART Now                #
#########################################################
^^^^^^^^^^Debug information:
BOX MODEL: $box_type
OO SYSTEM: $OSTYPE
PYTHON: $python_vers
IMAGE NAME: ${distro_value:-Unknown}
IMAGE VERSION: ${distro_version:-Unknown}
EOF

sleep 5
killall -9 enigma2
exit 0
