import sys
import time
import swmixer
import os.path
from rotaryencoder import rotaryencoder
from numpy import interp

try:
    swmixer.init(stereo=True, samplerate=32000)
    swmixer.start()
    print("Started swmixer")
except BaseException as e:
    print("Couldn't start swmixer: " + str(e.message))


RESSOURCES_PATH = "../ressources/audio"
MIN_VFREQ=88
MAX_VFREQ=108

# TODO: scan the audio directory intead of hardcoding the filenames
FILENAMES = map(lambda path: os.path.abspath(RESSOURCES_PATH + "/" + path), [
    "1.mp3",
    "2.mp3",
    "3.mp3"
    # "4.mp3",
    # "5.mp3"
])

CHANNELS = []
CHANNEL_STEP = None

# Initialization
for path in FILENAMES:
    try:
        snd = swmixer.StreamingSound(path)
        print("Loaded " + path)
    except Exception as e:
        snd = None
        print("Couldn't load " + path + ": " + str(e.message))
    if snd is not None:
        freq = None
        if len(CHANNELS) < 1:
            freq = MIN_VFREQ
        elif len(CHANNELS) == (len(FILENAMES) - 1):
            freq = MAX_VFREQ
        else:
            CHANNEL_STEP = (MAX_VFREQ - MIN_VFREQ) / (len(FILENAMES) - 1)
            print("Channel step: {}".format(CHANNEL_STEP))
            # Last channel vfreq + step
            freq = CHANNELS[-1][1] + CHANNEL_STEP
        chn = snd.play(volume=1.0)
        #chn.pause()

        CHANNELS.append((chn, freq, snd))
        print("Assigned to virtual frequency " + str(freq))

##
## @brief      Computes the volume of a channel given a vfreq and the channel vfreq
##
## @param      vfreq      The vfreq
## @param      chn_vfreq  The channel vfreq
##
## @return     The volume for vfreq.
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
        if lower_chn_vfreq == chn_vfreq: scale = [0, 100]
        elif upper_chn_vfreq == chn_vfreq: scale = [-100, 0]
        else: scale = [-100, 100]
        interpolated_vfreq = interp(vfreq, [lower_chn_vfreq, upper_chn_vfreq], scale)
        volume = 100 - abs(interpolated_vfreq)
        return volume/100

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
        print("Set volume for freq " + str(vfreq) + " to " + str(volumes_list[i]))


##
## @brief      Callback called when the vfreq changed.
##
## @param      vfreq  The vfreq
##
def vfreq_changed(vfreq):
    volumes = get_volumes_for_vfreq(vfreq)
    sys.stdout.write("\r")
    for i, volume in enumerate(volumes):
        sys.stdout.write(str(round(volume, 2)) + " - ")
        set_volumes(volumes)

    sys.stdout.flush()

if 'rotaryencoder' in sys.modules:
    rotaryencoder.init(MIN_VFREQ, MAX_VFREQ, step=0.1)
    rotaryencoder.def_chg_callback(vfreq_changed)


if 'rotaryencoder' in sys.modules:
    #pass
    vfreq_changed(88)
    rotaryencoder.loop()

# for chn, _, _ in CHANNELS:
#     chn.unpause()

while True:
    time.sleep(10)
