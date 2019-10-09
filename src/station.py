from audio_engine import AudioEngine, AudioTrack
import logging
import hashlib

logger = logging.getLogger("virtual_fm_band")


class Station:

    ID = None
    URI = None
    NAME = None

    VFREQ = None
    AUDIOTRACK = None

    def __repr__(self):
        return "<{}> [F:{}] [V:{}]".format(self.NAME, self.VFREQ, self.get_volume())

    def __init__(self, source=None, audio_engine=None):

        assert audio_engine is not None
        assert source is not None

        self.URI = source["uri"]
        self.NAME = source["name"]
        self.ID = hashlib.md5(self.URI.encode("utf-8")).hexdigest()[:8]
        self.AUDIOTRACK = AudioTrack(
            id=self.ID, uri=self.URI, audio_engine=audio_engine
        )

        logger.info(
            "Initialized station <{name}> ({id})".format(name=self.NAME, id=self.ID)
        )

    def set_volume(self, *args, **kwargs):
        self.AUDIOTRACK.set_volume(*args, **kwargs)
        logger.debug("Changed volume of <{}> to {}".format(self.NAME, args[0]))

    def get_volume(self, *args, **kwargs):
        self.AUDIOTRACK.get_volume(*args, **kwargs)

    def play(self):
        self.AUDIOTRACK.play()
        logger.debug("Changed state of <{}> to PLAYING".format(self.NAME))
