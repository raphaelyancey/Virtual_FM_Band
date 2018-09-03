#!/usr/bin/env bash

set -x

HOME=/home/pi

echo ""
echo "[•] Upgrading and installing required packages"
echo ""

sudo apt-get update

sudo apt-get upgrade -y

sudo apt-get install -y --no-install-recommends git python-dev pulseaudio pulseaudio-utils libportaudio0 libportaudio2 libportaudiocpp0 libmad0-dev portaudio19-dev libasound-dev

echo ""
echo "[•] Installing pip"
echo ""

curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py | python

echo ""
echo "[•] Cloning the virtual radio software"
echo ""

mkdir ${HOME}/audio

git clone https://github.com/raphaelyancey/Virtual_FM_Band ${HOME}/app

cd ${HOME}/app

echo ""
echo "[•] Installing Python modules (might take a while — about 10mn)"
echo ""

# Should try https://www.piwheels.hostedpi.com/faq.html

pip -V

pip install --user -r requirements.txt

echo ""
echo "[•] Installing crontab"
echo ""

(sudo crontab -l 2>/dev/null; echo "@reboot /usr/bin/env/bash /home/pi/app/run.sh") | sudo crontab -

echo ""
echo "[•] Finished!"
echo "[•] To complete the installation, put your audio files in ${HOME}/audio and reboot the Pi."
echo ""