from icecream import ic
import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst, GObject
import logging


logger = logging.getLogger("virtual_fm_band")


class AudioEngine:

    """
    Initializes gstreamer and controls the master volume
    """

    INITIALIZED = False
    PIPELINE = None
    LAUNCH_COMMAND = None

    def __init__(self):
        """
        Initializes gstreamer
        """

        # Initializes gstreamer if not already
        if not self.INITIALIZED:
            Gst.debug_set_active(True)
            Gst.debug_set_default_threshold(3)
            Gst.init(None)
            self.INITIALIZED = True
            logger.info("Started audio engine: gstreamer")

        self.LAUNCH_COMMAND = "audiomixer name=mix !  volume volume=1.0 name=master ! audioconvert ! autoaudiosink"

        logger.debug("Initialized pipeline")

    def run(self):
        logger.info("Running the gstreamer pipeline...")
        self.PIPELINE = Gst.parse_launch(self.LAUNCH_COMMAND)
        self.PIPELINE.set_state(Gst.State.PLAYING)

    def volume(self, volume):
        """
        Controls the master volume
        """
        assert volume >= 0 and volume <= 1.0
        self.PIPELINE.get_by_name("master").set_property("volume", volume)


class AudioTrack:

    """
    An interface to create and controls audio tracks
    """

    ID = None
    _AUDIO_ENGINE_INSTANCE = None

    def __init__(self, id=None, uri=None, audio_engine=None):
        """
        Creates an audio track (playbin) connected to the audio sink
        """

        assert uri is not None
        assert audio_engine is not None
        assert id is not None

        self.ID = id

        self._AUDIO_ENGINE_INSTANCE = audio_engine
        self._AUDIO_ENGINE_INSTANCE.LAUNCH_COMMAND += " "
        self._AUDIO_ENGINE_INSTANCE.LAUNCH_COMMAND += "uridecodebin uri={uri} ! volume volume=1.0 name={name} ! mix.".format(
            uri=uri, name=self.ID
        )

        logger.debug("Created audio track with URI <{}>".format(uri))

    def set_volume(self, volume):
        """
        Controls the volume of the playbin
        """
        assert volume >= 0 and volume <= 1.0
        if self._AUDIO_ENGINE_INSTANCE.PIPELINE:
            self._AUDIO_ENGINE_INSTANCE.PIPELINE.get_by_name(self.ID).set_property(
                "volume", volume
            )

    def get_volume(self):
        """
        Returns the current volume of the playbin
        """
        if not self._AUDIO_ENGINE_INSTANCE.PIPELINE:
            return 0
        return self._AUDIO_ENGINE_INSTANCE.PIPELINE.get_by_name(self.ID).get_property(
            "volume"
        )
