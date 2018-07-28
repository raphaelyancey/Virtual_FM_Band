#!/usr/bin/env bash

sudo apt-get update

sudo apt-get upgrade -y

sudo apt-get install -y --no-install-recommends git python-dev pulseaudio pulseaudio-utils libportaudio0 libportaudio2 libportaudiocpp0 libmad0-dev portaudio19-dev libasound-dev

mkdir ~/audio

git clone https://github.com/raphaelyancey/Virtual_FM_Band ~/app

cd ~/app

pip -V

pip install --user -r requirements.txt

(sudo crontab -l 2>/dev/null; echo "@reboot /usr/bin/env/bash -c \"python2 /home/pi/app/src/main.py\"") | sudo crontab -