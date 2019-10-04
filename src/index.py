#!/usr/bin/env python3

from icecream import ic
import sys
import time
import os
from numpy import interp
import threading
import subprocess
import logging
from dotenv import load_dotenv, find_dotenv
import argparse
import random
from scipy.interpolate import interp1d
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject
from functools import reduce
from radio import Radio

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
logger.debug('debug')
logger.info('info')

# Load environment variables from the .env file if exists
load_dotenv(find_dotenv())

# If the machine doesn't have encoders wired in, the auto mode simulate frequency encoder rotation
parser = argparse.ArgumentParser(description='Plays virtual radio stations.')
parser.add_argument('-a', '--auto', action='store_true', help='Move through the stations at a regular pace, ignoring encoders input if any. Useful when testing without encoders.')
args = parser.parse_args()

# Initialize the radio: read settings, load files
radio = Radio().init()