#!/usr/bin/env bash

#set -x
set -e

INSTALL_DIR=/home/pi

echo ""
echo "[•] Upgrading and installing required packages"
echo ""

sudo apt-get update

#sudo apt-get upgrade -y

sudo apt-get install -y --no-install-recommends git python-dev pulseaudio pulseaudio-utils libportaudio0 libportaudio2 libportaudiocpp0 libmad0-dev portaudio19-dev libasound-dev

echo ""
echo "[•] Installing pip"
echo ""

curl https://bootstrap.pypa.io/get-pip.py | sudo python

echo ""
echo "[•] Cloning the virtual radio software"
echo ""

mkdir -p ${INSTALL_DIR}/audio

git clone https://github.com/raphaelyancey/Virtual_FM_Band ${INSTALL_DIR}/app

cd ${INSTALL_DIR}/app

mv .env-example .env

echo ""
echo "[•] Installing Python modules (might take a while — about 10mn)"
echo ""

# Should try https://www.piwheels.hostedpi.com/faq.html

pip -V

pip install --user -r requirements.txt

echo ""
echo "[•] Installing crontab"
echo ""

(crontab -l 2>/dev/null; echo "@reboot /usr/bin/env bash ${INSTALL_DIR}/app/run.sh") | crontab -

echo ""
echo "[•] Finished!"
echo "[•] To complete the installation:"
echo "    - Put your audio files in ${INSTALL_DIR}/audio"
echo "    - Customize the configuration file ${INSTALL_DIR}/app/.env (optionnal)"
echo "    - Reboot the Pi and enjoy!"
echo ""
