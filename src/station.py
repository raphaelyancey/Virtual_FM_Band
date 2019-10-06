from audio_engine import AudioEngine, AudioTrack
import logging

logger = logging.getLogger("virtual_fm_band")


class Station:

    URI = None
    NAME = None

    VFREQ = None
    AUDIOTRACK = None

    def __repr__(self):
        return "<{}> [F:{}] [V:{}]".format(self.NAME, self.VFREQ, self.get_volume())

    def __init__(self, source, audio_engine=None):

        assert audio_engine is not None

        self.URI = source["uri"]
        self.NAME = source["name"]
        self.AUDIOTRACK = AudioTrack(uri=self.URI, audio_engine=audio_engine)

        logger.info("Initialized station <{}>".format(self.NAME))

    def set_volume(self, *args, **kwargs):
        self.AUDIOTRACK.set_volume(*args, **kwargs)
        logger.debug("Changed volume of <{}> to {}".format(self.NAME, args[0]))

    def get_volume(self, *args, **kwargs):
        self.AUDIOTRACK.get_volume(*args, **kwargs)

    def play(self):
        self.AUDIOTRACK.play()
        logger.debug("Changed state of <{}> to PLAYING".format(self.NAME))
