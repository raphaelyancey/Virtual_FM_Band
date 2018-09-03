#!/usr/bin/env bash

pulseaudio -D

# TODO: Set audio in ENV instead
python2 /home/pi/audio/main.py