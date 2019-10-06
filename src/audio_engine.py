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
    SINK_INSTANCE = None

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

        # Creates the audio sink that all playbins will be connected to
        self.SINK_INSTANCE = Gst.ElementFactory.make("autoaudiosink", None)
        logger.debug("Created audio sink")

    def volume(self, volume):
        """
        Controls the master volume
        """
        pass


class AudioTrack:

    """
    An interface to create and controls audio tracks
    """

    PLAYBIN_INSTANCE = None

    def __init__(self, uri=None, audio_engine=None):
        """
        Creates an audio track (playbin) connected to the audio sink
        """

        assert uri is not None
        assert audio_engine is not None

        # Creates a playbin (= audio track) and connects it to the gstreamer sink
        self.PLAYBIN_INSTANCE = Gst.ElementFactory.make("playbin", None)
        self.PLAYBIN_INSTANCE.set_property("audio-sink", audio_engine.SINK_INSTANCE)
        self.PLAYBIN_INSTANCE.set_property("uri", uri)
        logger.debug("Created audio track with URI <{}>".format(uri))

    def set_volume(self, volume):
        """
        Controls the volume of the playbin
        """
        assert volume >= 0 and volume <= 1.0
        self.PLAYBIN_INSTANCE.set_property("volume", volume)

    def get_volume(self):
        """
        Returns the current volume of the playbin
        """
        self.PLAYBIN_INSTANCE.get_property("volume")

    def play(self):
        self.PLAYBIN_INSTANCE.set_state(Gst.State.PLAYING)
