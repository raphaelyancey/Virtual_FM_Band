import sys
import swmixer
import os.path
try:
    from rotaryencoder import rotaryencoder
except:
    pass
from numpy import interp

try:
    swmixer.init(stereo=True)
    swmixer.start()
    print("Started swmixer")
except BaseException as e:
    print("Couldn't start swmixer: " + str(e.message))


RESSOURCES_PATH = "../ressources/audio"
MIN_FREQ=0
MAX_FREQ=100

# TODO: scan the audio directory intead of hardcoding the filenames
FILENAMES = map(lambda path: os.path.abspath(RESSOURCES_PATH + "/" + path), [
    "1.mp3",
    "2.mp3",
    "3.mp3",
    "4.mp3",
    "5.mp3"
])

CHANNELS = []
CHANNEL_STEP = None

def foo(**params):
    sys.stdout.write("\r"+str(params['count']))
    sys.stdout.flush()

def bar(**params):
    sys.stdout.write("\r"+str(params['count']))
    sys.stdout.flush()

if 'rotaryencoder' in sys.modules:
    rotaryencoder.def_inc_callback(foo)
    rotaryencoder.def_dec_callback(bar)

# Initialization
for path in FILENAMES:
    try:
        chn = swmixer.StreamingSound(path)
        print("Loaded " + path)
    except Exception as e:
        chn = None
        print("Couldn't load " + path + ": " + str(e.message))
    if chn is not None:
        freq = None
        if len(CHANNELS) < 1:
            freq = MIN_FREQ
        elif len(CHANNELS) == (len(FILENAMES) - 1):
            freq = MAX_FREQ
        else:
            CHANNEL_STEP = MAX_FREQ / (len(FILENAMES) - 1)
            freq = CHANNELS[-1][1] + CHANNEL_STEP

        CHANNELS.append((chn, freq))
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

    print(" Channel vfreq: {}".format(chn_vfreq))
    
    lower_chn, upper_chn = get_channels_boundaries(vfreq)
    lower_chn_vfreq = lower_chn[1]
    upper_chn_vfreq = upper_chn[1]

    print(" Lower vfreq: {}".format(lower_chn_vfreq))
    print(" Upper vfreq: {}".format(upper_chn_vfreq))

    if chn_vfreq < lower_chn_vfreq or chn_vfreq > upper_chn_vfreq:
        # The channel vfreq is outside the boundaries = null volume
        print(" {} is outside boundaries.".format(chn_vfreq))
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
        print(" Interpolated vfreq {} from [{}, {}] to {}: {}".format(vfreq, lower_chn_vfreq, upper_chn_vfreq, scale, interpolated_vfreq))
        volume = 100 - abs(interpolated_vfreq)
        return volume
        # TODO: call this function for each channel


##
## @brief      Computes the channel volumes for a given virtual frequency.
##
## @param      vfreq  The virtual frequency
##
## @return     A list of volumes to apply to each channel.
##
def get_volumes_for_vfreq(vfreq, channels_list=CHANNELS, MIN_FREQ=MIN_FREQ, MAX_FREQ=MAX_FREQ):
    print("-- Volumes for vfreq {}\n".format(vfreq))
    for i, (channel, chn_vfreq) in enumerate(channels_list):
        vol = get_chn_volume_for_vfreq(vfreq, chn_vfreq=chn_vfreq)
        print("> Volume for channel {} (vfreq {}) : {}\n".format(i, chn_vfreq, vol))
    print("\n")



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
    for i, (channel, chn_vfreq) in enumerate(channels_list):
        if i < len(channels_list) - 1:
            next_channel, next_chn_vfreq = channels_list[i + 1]
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
    for i, (channel, vfreq) in enumerate(channels_list):
        channel.set_volume(volumes_list[i])
        print("Set volume for freq " + str(vfreq) + " to " + volumes_list[i])


# get_volumes_for_vfreq(0)
# get_volumes_for_vfreq(0+3.5)
# get_volumes_for_vfreq(25+6.5)
# get_volumes_for_vfreq(50+2.5)
# get_volumes_for_vfreq(75+10.5)
# get_volumes_for_vfreq(100)

if 'rotaryencoder' in sys.modules:
    print('yup')
    rotaryencoder.loop()

# while True:
#     pass
