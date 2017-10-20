import swmixer
import os.path
from numpy import interp

try:
    swmixer.init(stereo=True)
    swmixer.start()
    print("Started swmixer")
except BaseException:
    print("Couldn't start swmixer")


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

# Initialization
for path in FILENAMES:
    try:
        chn = swmixer.Sound(path)
        print("Loaded " + path)
    except BaseException:
        chn = None
        print("Couldn't load " + path)
    if chn is not None:
        freq = None
        if len(CHANNELS) < 1:
            freq = MIN_FREQ
        elif len(CHANNELS) == (len(FILENAMES) - 1):
            freq = MAX_FREQ
        else:
            CHANNEL_STEP = MAX_FREQ / (len(FILENAMES) - 1)
            freq = CHANNELS[-1][1] + CHANNEL_STEP

        def get_volume_for_vfreq(vfreq):

            lower_vfreq = freq - CHANNEL_STEP # aka previous channel vfreq
            upper_vfreq = freq + CHANNEL_STEP # aka next channel vfreq

            if vfreq < lower_vfreq and vfreq > upper_vfreq:
                # Outside boundaries = null volume
                return 0
            else:
                # Inside boundaries, compute with vol = -abs(x) + 100
                interpolated_vfreq = interp(vfreq, [lower_vfreq, upper_vfreq], [0, 100])
                volume = -abs(interpolated_vfreq) + 100
                print("Volume: " + volume)
                # TODO: call this function for each channel

        CHANNELS.append((chn, freq))
        print("Assigned to virtual frequency " + str(freq))


##
## @brief      Computes the channel volumes for a given virtual frequency.
##
## @param      vfreq  The virtual frequency
##
## @return     A list of volumes to apply to each channel.
##
def get_volumes_for_vfreq(vfreq, channels_list=CHANNELS, MIN_FREQ=MIN_FREQ, MAX_FREQ=MAX_FREQ):
    if vfreq < MIN_FREQ or vfreq > MAX_FREQ:
        print("vfreq not in bandwidth, ignoring.")
        return
    (lower_chn, lower_vfreq), (upper_chn, upper_vfreq) = get_stations_boundaries(vfreq)
    print("Boundaries vfreqs for vfreq = " + str(vfreq) + " : (" + str(lower_vfreq) + ", " + str(upper_vfreq) + ")")
    for i, (channel, chn_vfreq) in enumerate(channels_list):
        prev_channel, prev_chn_vfreq = channels_list[i - 1] if i > 0 else (None, None)
        next_channel, next_chn_vfreq = channels_list[i + 1] if i < len(channels_list - 1) else (None, None)



##
## @brief      Gets the stations boundaries for a given vfreq.
##
## @param      vfreq  The virtual frequency from which to get the surrounding stations
##
## @return     Two (channel, freq) in between which the vfreq is.
##
def get_stations_boundaries(vfreq, channels_list=CHANNELS):
    lower_chn = channels_list[0]
    upper_chn = channels_list[-1]
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


get_volumes_for_vfreq(23)
get_volumes_for_vfreq(0)
get_volumes_for_vfreq(32)
get_volumes_for_vfreq(46)
get_volumes_for_vfreq(100)

# while True:
#     pass
