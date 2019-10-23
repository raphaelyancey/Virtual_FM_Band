#!/usr/bin/env python3

from icecream import ic
import os
import logging
import argparse
import time
import threading
from radio import Radio
from gi.repository import GObject, GLib
from dotenv import load_dotenv, find_dotenv

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

# Load env vars (also loaded by Radio later, but not handling the same vars)
load_dotenv(find_dotenv(), verbose=True)

SETTINGS = {
    "VOLUME_STEP": os.getenv("VOLUME_STEP", 1),
    "TUNED_LED_PIN": int(os.getenv("TUNED_LED_PIN", 25)),
    "VOLUME_PIN_CLK": int(os.getenv("VOLUME_PIN_CLK", 5)),
    "VOLUME_PIN_DT": int(os.getenv("VOLUME_PIN_DT", 6)),
    "VOLUME_PIN_SW": int(os.getenv("VOLUME_PIN_SW", 13)),
    "TUNING_PIN_CLK": int(os.getenv("TUNING_PIN_CLK", 17)),
    "TUNING_PIN_DT": int(os.getenv("TUNING_PIN_DT", 27)),
    "TUNING_PIN_SW": int(os.getenv("TUNING_PIN_SW", 22)),
    "NOISE_PATH": os.getenv(
        "NOISE_PATH", "{}/audio/noise".format(os.getenv("HOME"))
    ),
    "AUDIO_PATH": os.getenv("AUDIO_PATH", "{}/audio".format(os.getenv("HOME"))),
    "NOISE_TRIGGER_THRESHOLD": float(os.getenv("NOISE_TRIGGER_THRESHOLD", 0.9)),
    "MIN_VFREQ": 1,
    "MAX_VFREQ": 300,  # TODO: create a user-friendly, computed env var to customize the transition speed from a station to the next?
}

ic(SETTINGS)


def tuned_station():
    logger.debug('A station is tuned')
    if has_gpio:
        GPIO.output(SETTINGS['TUNED_LED_PIN'], GPIO.HIGH)


def untuned_station():
    if has_gpio:
        GPIO.output(SETTINGS['TUNED_LED_PIN'], GPIO.LOW)


radio = Radio(on_tuned_station=tuned_station,
              on_detuned_station=untuned_station,
              settings=SETTINGS)

ic(radio.STATIONS)

mainloop = GLib.MainLoop()
gstreamer_thread = threading.Thread(target=lambda: mainloop.run())
gstreamer_thread.daemon = True
gstreamer_thread.start()

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
