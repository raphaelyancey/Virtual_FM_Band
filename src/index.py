#!/usr/bin/env python3

from icecream import ic
import os
import logging
import argparse
import time
import threading
from radio import Radio
from gi.repository import GObject, GLib


try:
    from RPi import GPIO
    has_gpio = True
except ImportError:
    has_gpio = False

# If the machine has GPIO capabilities, import the encoder library
if has_gpio:
    from pyky040 import pyky040

# `ic` is used for dumping values whereas `logging` is used for standard logging
ic.configureOutput(prefix='> ')
logging.basicConfig()
logger = logging.getLogger('virtual_fm_band')
logger.setLevel(logging.DEBUG if os.getenv('DEBUG') == 'True' else logging.INFO)

# If the machine doesn't have encoders wired in, the auto mode simulate frequency encoder rotation. Used for development and testing.
parser = argparse.ArgumentParser(description='Plays virtual radio stations.')
parser.add_argument('-a', '--auto', action='store_true', help='Move through the stations at a regular pace, ignoring encoders input if any. Useful when testing without encoders.')
args = parser.parse_args()

# Creates stations
radio = Radio()

ic(radio.STATIONS)

mainloop = GLib.MainLoop()

t = threading.Thread(target=lambda: mainloop.run())
t.daemon = True
t.start()

logger.debug("Started!")

# Tune in the first station
radio.set_vfreq(1)

if args.auto:
    auto_vfreq = 0

while True:

    time.sleep(1)

    if args.auto:
        auto_vfreq += 1
        radio.set_vfreq(auto_vfreq)
