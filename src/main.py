import swmixer
import os.path

try:
    swmixer.init(stereo=True)
    swmixer.start()
    print("Started swmixer")
except BaseException:
    print("Couldn't start swmixer")


RESSOURCES_PATH = "../ressources/audio"
MIN_FREQ=88.7
MAX_FREQ=108.0

# TODO: scan the audio directory intead of hardcoding the filenames
FILENAMES = map(lambda path: os.path.abspath(RESSOURCES_PATH + "/" + path), [
    "1.mp3",
    "2.mp3",
    "3.mp3",
    "4.mp3",
    "5.mp3"
])

CHANNELS = []

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
            step = MAX_FREQ / (len(FILENAMES) - 1)
            freq = CHANNELS[-1][1] + step
        CHANNELS.append((chn, freq))
        print("Assigned to virtual frequency " + str(freq))


##
## @brief      Gets the volume for a given virtual frequency.
##
## @param      vfreq  The virtual frequency
##
## @return     A list of volumes to apply to each channel.
##
def get_volume_for_vfreq(vfreq):
    pass


##
## @brief      Sets the volumes given a list of volumes.
##
## @param      channels_list  The channels list to apply the volumes to
## @param      volumes_list   The volumes list
##
def set_volumes(channels_list, volumes_list):
    pass


while True:
    pass
