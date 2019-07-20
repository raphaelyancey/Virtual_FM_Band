from icecream import ic
import sys
import time
import swmixer
import os
import logging
from numpy import interp
import threading
import subprocess
from copy import copy, deepcopy
from dotenv import load_dotenv, find_dotenv
import argparse
import random
from scipy.interpolate import interp1d

try:
    from RPi import GPIO
    has_gpio = True
except ImportError:
    has_gpio = False

if has_gpio:
    from pyky040 import pyky040

ic.configureOutput(prefix='> ')

load_dotenv(find_dotenv())

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG if os.getenv('DEBUG', '') == 'True' else logging.INFO)

parser = argparse.ArgumentParser(description='Plays virtual radio stations.')
parser.add_argument('-d', '--debug', action='store_true', help='Load stations and move through them at a regular pace, ignoring encoders input.')
args = parser.parse_args()

# See .env for vars documentation
NOISE_PATH = ic(os.getenv('NOISE_PATH', '{}/audio/noise'.format(os.getenv('HOME'))))
AUDIO_PATH = ic(os.getenv('AUDIO_PATH', '{}/audio'.format(os.getenv('HOME'))))
VOLUME_STEP = ic(os.getenv('VOLUME_STEP', 1))
TUNED_LED_PIN = ic(int(os.getenv('TUNED_LED_PIN', 25)))
VOLUME_PIN_CLK = ic(int(os.getenv('VOLUME_PIN_CLK', 5)))
VOLUME_PIN_DT = ic(int(os.getenv('VOLUME_PIN_DT', 6)))
VOLUME_PIN_SW = ic(int(os.getenv('VOLUME_PIN_SW', 13)))
TUNING_PIN_CLK = ic(int(os.getenv('TUNING_PIN_CLK', 17)))
TUNING_PIN_DT = ic(int(os.getenv('TUNING_PIN_DT', 27)))
TUNING_PIN_SW = ic(int(os.getenv('TUNING_PIN_SW', 22)))
AUDIO_DEVICE_INDEX = ic(int(os.getenv('AUDIO_DEVICE_INDEX', 1)))
NOISE_PATH = os.getenv('NOISE_PATH', '{}/audio/noise'.format(os.getenv('HOME')))
AUDIO_PATH = os.getenv('AUDIO_PATH', '{}/audio'.format(os.getenv('HOME')))
VOLUME_STEP = os.getenv('VOLUME_STEP', 1)
TUNED_LED_PIN = int(os.getenv('TUNED_LED_PIN', 25))
VOLUME_PIN_CLK = int(os.getenv('VOLUME_PIN_CLK', 5))
VOLUME_PIN_DT = int(os.getenv('VOLUME_PIN_DT', 6))
VOLUME_PIN_SW = int(os.getenv('VOLUME_PIN_SW', 13))
TUNING_PIN_CLK = int(os.getenv('TUNING_PIN_CLK', 17))
TUNING_PIN_DT = int(os.getenv('TUNING_PIN_DT', 27))
TUNING_PIN_SW = int(os.getenv('TUNING_PIN_SW', 22))
AUDIO_DEVICE_INDEX = int(os.getenv('AUDIO_DEVICE_INDEX', 1))

MIN_VFREQ = 1
MAX_VFREQ = 300  # TODO: create a user-friendly env var to customize the transition speed from a station to the next?
CURRENT_VFREQ = MIN_VFREQ

try:
    swmixer.init(stereo=True, samplerate=44100, output_device_index=AUDIO_DEVICE_INDEX)  # To list device IDs: https://stackoverflow.com/a/39677871/2544016
    swmixer.start()
    logger.info("Started swmixer")
except BaseException as e:
    logger.error("Couldn't start swmixer: " + str(e))

if has_gpio:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TUNED_LED_PIN, GPIO.OUT)

# TODO: scan the audio directory intead of hardcoding the filenames

FILES = []
for root, dirs, files in os.walk(os.path.abspath(AUDIO_PATH)):
    for file in [f for f in files if f.endswith(".mp3") and root == os.path.abspath(AUDIO_PATH)]:
        logger.debug('Found matching file: {}'.format(file))
        FILES.append((os.path.join(root, file),
                      os.path.basename(file)[:-4]))  # Stripping out '.mp3'

PATHS = map(
    lambda path: os.path.abspath(path),
    map(lambda file: file[0], FILES)  # Returns the filename
)

CHANNELS = []
CHANNEL_STEP = None

# Initialization
logger.info("")
for path in PATHS:
    try:
        snd = swmixer.StreamingSound(path)
        logger.debug("Loaded " + path)
    except Exception as e:
        snd = None
        logger.error("Couldn't load " + path + ": " + str(e))
    if snd is not None:
        freq = None
        if len(CHANNELS) < 1:
            freq = MIN_VFREQ
        elif len(CHANNELS) == (len(PATHS) - 1):
            freq = MAX_VFREQ
        else:
            CHANNEL_STEP = (MAX_VFREQ - MIN_VFREQ) / (len(PATHS) - 1)
            logger.debug("Channel step: {}".format(CHANNEL_STEP))
            # Last channel vfreq + step
            freq = CHANNELS[-1][1] + CHANNEL_STEP
        chn = snd.play(volume=0.0, loops=-1)

        CHANNELS.append((chn, freq, snd))
        logger.debug("Assigned to virtual frequency " + str(freq))
        logger.debug("")

# Setup the noise tracks
NOISE_CHANNELS = []
for root, dirs, files in os.walk(os.path.abspath(NOISE_PATH)):
    for file in [f for f in files if f.endswith(".mp3")]:
        path = os.path.join(root, file)
        try:
            snd = swmixer.StreamingSound(path)
            logger.debug("Loaded noise " + path)
        except Exception as e:
            snd = None
            logger.error("Couldn't load noise " + path + ": " + str(e.message))
        if snd is not None:
            chn = snd.play(volume=0.0, loops=-1)
            NOISE_CHANNELS.append((chn, snd))

##
## @brief      Computes the volume of a channel given a vfreq and the channel vfreq
##
## @param      vfreq      The vfreq
## @param      chn_vfreq  The channel vfreq
##
## @return     The volume for chn_vfreq between 0 and 1.
##
def get_chn_volume_for_vfreq(vfreq, chn_vfreq=None):

    lower_chn, upper_chn = get_channels_boundaries(vfreq)
    lower_chn_vfreq = lower_chn[1]
    upper_chn_vfreq = upper_chn[1]

    if chn_vfreq < lower_chn_vfreq or chn_vfreq > upper_chn_vfreq:
        # The channel vfreq is outside the boundaries = null volume
        return 0
    else:
        # Inside boundaries, compute with `vol = 100 - abs(x)` with x between -100 and 100
        # When x = -100, y = 0
        # When x = 0, y = 100
        # When x = 100, y = 0
        # |/|\| (poor ASCII art)
        #   0
        if lower_chn_vfreq == chn_vfreq:
            scale = [0, 100]
        elif upper_chn_vfreq == chn_vfreq:
            scale = [-100, 0]
        else:
            scale = [-100, 100]

        # Translating the vfreq on a scale of [-100, 100] (except when first or last station) for easy calculations
        interpolated_vfreq = interp(vfreq, [lower_chn_vfreq, upper_chn_vfreq], scale)

        # Creating the volume curve (x = vfreq, y = volume)
        # https://docs.scipy.org/doc/scipy/reference/tutorial/interpolate.html#d-interpolation-interp1d for infos
        x = [-100, -10, 0, 10, 100]
        y = [0, 10, 100, 10, 0]
        f = interp1d(x, y)

        volume = f(interpolated_vfreq)
        return volume / 100

##
## @brief      Computes the channel volumes for a given virtual frequency.
##
## @param      vfreq  The virtual frequency
##
## @return     A list of volumes to apply to each channel.
##
def get_volumes_for_vfreq(vfreq, channels_list=CHANNELS, MIN_VFREQ=MIN_VFREQ, MAX_VFREQ=MAX_VFREQ):
    volumes = []
    for i, (_, chn_vfreq, _) in enumerate(channels_list):
        vol = get_chn_volume_for_vfreq(vfreq, chn_vfreq=chn_vfreq)
        volumes.append(vol)
    return volumes


##
## @brief      Gets the channels boundaries (the channels around the vfreq) for a given vfreq.
##
## @param      vfreq  The virtual frequency from which to get the surrounding channels
##
## @return     Two (channel, freq) in between which the vfreq is.
##
def get_channels_boundaries(vfreq, channels_list=CHANNELS):

    # By default, the boundaries are [first channels] > vfreq > [last station]
    lower_chn = channels_list[0]
    upper_chn = channels_list[-1]

    # Then for each channel we update them by comparing their vfreq to the requested vfreq
    for i, (_, chn_vfreq, _) in enumerate(channels_list):
        if i < len(channels_list) - 1:
            _, next_chn_vfreq, _ = channels_list[i + 1]
            if vfreq >= chn_vfreq and vfreq <= next_chn_vfreq:
                lower_chn = channels_list[i]
                upper_chn = channels_list[i + 1]
                break
        else:
            # If there isn't any more channel, the boundaries are the two last channels
            lower_chn = channels_list[-2]
            upper_chn = channels_list[-1]
    return (lower_chn, upper_chn)



##
## @brief      Sets the volumes given a list of volumes.
##
## @param      channels_list  The channels list to apply the volumes to
## @param      volumes_list   The volumes list
##
def set_volumes(volumes_list, channels_list=CHANNELS):
    for i, (channel, vfreq, _) in enumerate(channels_list):
        channel.set_volume(volumes_list[i])


def set_noise(volumes_list, noise_channels_list=NOISE_CHANNELS):

    if len(noise_channels_list) == 0:
        return

    def no_noise():
        for noise_channel, _ in noise_channels_list:
            noise_channel.set_volume(0)

    # Only triggers when in-between stations, i.e. when none of the volumes is over 0.9 (keeping a padding of 0.1)
    if len([v for v in volumes_list if v > 0.9]) == 0:
        no_noise()
        index = random.randint(0, (len(noise_channels_list) - 1))  # Select a random noise track
        volume = round(random.uniform(0.8, 1.0), 1) # And a random volume
        noise_channels_list[index][0].set_volume(volume)
    else:
        no_noise()


##
## @brief      Draws a band visualisation on the logger
##
## @param      volumes  The ordered volumes
## @param      files    The ordered files
##
## @return     None
##
def draw(volumes, files=FILES):
    formatted_stations_names = []
    formatted_volumes = []
    for station in files:
        formatted_stations_names.append(station[1])
    for i, volume in enumerate(volumes):
        volume = round(volume, 1)
        formatted_volumes.append(("{:^" + str(len(files[i][1])) + "}").format(volume))
    logger.info(formatted_stations_names)
    logger.info(formatted_volumes)


##
## @brief      Gets the volumes from the given channels list.
##
## @param      channels_list  The channels list
##
## @return     The volumes.
##
def get_volumes(channels_list=CHANNELS):
    volumes = []
    for i, (channel, vfreq, _) in enumerate(channels_list):
        vol = channel.get_volume()
        volumes.append(vol)
    return volumes


##
## @brief      Callback for when the vfreq changes.
##
## @param      vfreq  The vfreq
##
def vfreq_changed(vfreq, channels_list=CHANNELS):

    logger.info("Virtual frequency changed to {}".format(vfreq))
    volumes = get_volumes_for_vfreq(vfreq)
    draw(volumes)
    set_volumes(volumes)
    set_noise(volumes)

    # If all volumes < 1.0, no vfreq is tuned. Else, a vfreq is tuned.
    detuned = reduce(lambda a, v: a and v < 1.0, volumes, True)
    if not detuned:
        GPIO.output(TUNED_LED_PIN, GPIO.HIGH) if has_gpio else None
    else:
        GPIO.output(TUNED_LED_PIN, GPIO.LOW) if has_gpio else None


##
## @brief      Callback for when the global volume increments.
##
def inc_global_volume(count):
    logger.info("Incrementing global volume")
    # Using Popoen for async (we do not want to perturbate the audio)
    subprocess.Popen(["pactl", "set-sink-volume", "0", "+" + str(VOLUME_STEP) + "%"])


##
## @brief      Callback for when the global volume decrements.
##
def dec_global_volume(count):
    logger.info("Decrementing global volume")
    subprocess.Popen(["pactl", "set-sink-volume", "0", "-" + str(VOLUME_STEP) + "%"])


##
## @brief      Toggles mute state of the global volume
##
def toggle_mute():
    # Using call because we don't need async (the audio will be muted or unmuted)
    subprocess.call(["pactl", "set-sink-mute", "0", "toggle"])
    logger.info("Toggling mute")


vfreq_changed(CURRENT_VFREQ)

if has_gpio and 'pyky040' in sys.modules and not args.debug:

    tuning_encoder = pyky040.Encoder(CLK=TUNING_PIN_CLK, DT=TUNING_PIN_DT, SW=TUNING_PIN_SW)
    tuning_encoder.setup(scale_min=MIN_VFREQ, scale_max=MAX_VFREQ, step=1, chg_callback=vfreq_changed)
    tuning_thread = threading.Thread(target=tuning_encoder.watch)

    volume_encoder = pyky040.Encoder(CLK=VOLUME_PIN_CLK, DT=VOLUME_PIN_DT, SW=VOLUME_PIN_SW)
    volume_encoder.setup(scale_min=0, scale_max=10, step=1, inc_callback=inc_global_volume, dec_callback=dec_global_volume, sw_callback=toggle_mute)
    global_volume_thread = threading.Thread(target=volume_encoder.watch)

    tuning_thread.start()
    global_volume_thread.start()

while True:
    if args.debug:
        time.sleep(1)
        direction = 'up'
        if direction == 'up':
            if CURRENT_VFREQ == MAX_VFREQ:
                direction = 'down'
            else:
                CURRENT_VFREQ += 5
        elif direction == 'down':
            if CURRENT_VFREQ == MIN_VFREQ:
                direction = 'up'
            else:
                CURRENT_VFREQ -= 5
        vfreq_changed(CURRENT_VFREQ)
    else:
        try:
            time.sleep(10)
        except BaseException:
            break

logger.info("Exiting main thread...")
