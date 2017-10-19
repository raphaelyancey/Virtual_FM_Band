import swmixer

try:
    swmixer.init(stereo=True)
    swmixer.start()
    print("Started swmixer")
except BaseException:
    print("Couldn't start swmixer")


RESSOURCES_PATH = "../ressources"

FILENAMES = map(lambda path: RESSOURCES_PATH + "/" + path, [
    "1.mp3",
    "2.mp3",
    "3.mp3",
    "4.mp3",
    "5.mp3"
])

print(FILENAMES)

snd = swmixer.Sound("../ressources/audio/1.mp3")
snd.play()

while True:
    pass
