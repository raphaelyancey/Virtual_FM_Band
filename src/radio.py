import logging
from icecream import ic
import os
from dotenv import load_dotenv, find_dotenv
from typing import Sequence
from audio_engine import AudioEngine, AudioTrack
import hashlib

logger = logging.getLogger("virtual_fm_band")


class Radio:

    # Load environment variables from the .env file if exists
    load_dotenv(find_dotenv(), verbose=True)

    SETTINGS = {
        "NOISE_PATH": os.getenv(
            "NOISE_PATH", "{}/audio/noise".format(os.getenv("HOME"))
        ),
        "AUDIO_PATH": os.getenv("AUDIO_PATH", "{}/audio".format(os.getenv("HOME"))),
        "VOLUME_STEP": os.getenv("VOLUME_STEP", 1),
        "TUNED_LED_PIN": int(os.getenv("TUNED_LED_PIN", 25)),
        "VOLUME_PIN_CLK": int(os.getenv("VOLUME_PIN_CLK", 5)),
        "VOLUME_PIN_DT": int(os.getenv("VOLUME_PIN_DT", 6)),
        "VOLUME_PIN_SW": int(os.getenv("VOLUME_PIN_SW", 13)),
        "TUNING_PIN_CLK": int(os.getenv("TUNING_PIN_CLK", 17)),
        "TUNING_PIN_DT": int(os.getenv("TUNING_PIN_DT", 27)),
        "TUNING_PIN_SW": int(os.getenv("TUNING_PIN_SW", 22)),
        "NOISE_TRIGGER_THRESHOLD": float(os.getenv("NOISE_TRIGGER_THRESHOLD", 0.9)),
        "MIN_VFREQ": 1,
        "MAX_VFREQ": 300,  # TODO: create a user-friendly, computed env var to customize the transition speed from a station to the next?
    }

    STATE = {"CURRENT_VFREQ": SETTINGS["MIN_VFREQ"]}

    SOURCES = []
    STATIONS = []

    ALLOWED_FILE_EXTENSIONS = (".mp3",)

    _AUDIO_ENGINE = None

    def __init__(self):
        """
        Discovers audio sources and creates stations
        """

        logger.debug("Settings:")
        ic(self.SETTINGS)

        logger.debug("Looking for station sources...")
        self.discover_files()
        # self.discover_streams()

        logger.debug("Starting audio engine...")
        self._AUDIO_ENGINE = AudioEngine()

        logger.debug("Creating stations...")
        self.create_stations()

        self._AUDIO_ENGINE.run()

        ic(self.STATIONS)

    def discover_files(self):

        audio_path_tree = os.walk(os.path.abspath(self.SETTINGS["AUDIO_PATH"]))

        for root, dirs, files in audio_path_tree:

            # Only keeps MP3 files in the root dir of the audio path
            # TODO: handle other files
            for file in [
                f
                for f in files
                if f.endswith(self.ALLOWED_FILE_EXTENSIONS)
                and root == os.path.abspath(self.SETTINGS["AUDIO_PATH"])
            ]:

                logger.debug("Found a source file:")

                # Remove the extension, whatever it is
                source_name = os.path.basename(file)
                for ext in self.ALLOWED_FILE_EXTENSIONS:
                    # It is a suffix if the index it's found at + the length of the extension equals the whole length
                    # (already includes the 0-offset)
                    is_suffix = source_name.rfind(ext) + len(ext) == len(source_name)
                    source_name = (
                        source_name.replace(ext, "") if is_suffix else source_name
                    )

                source = {
                    "type": "file",
                    "uri": "file://{}".format(os.path.join(root, file)),
                    "name": os.path.basename(file)[:-4],
                }

                logger.debug(source)

                # Adds it to the sources list
                self.SOURCES.append(source)

        return [src for src in self.SOURCES if src["type"] == "file"]

    def discover_streams(self):
        pass

    def create_stations(self):

        for src in self.SOURCES:

            station_vfreq = None

            # If it is the first station to be created...
            if len(self.STATIONS) == 0:
                station_vfreq = self.SETTINGS["MIN_VFREQ"]

            # If it is the last one...
            elif len(self.STATIONS) == (len(self.SOURCES) - 1):
                station_vfreq = self.SETTINGS["MAX_VFREQ"]

            else:
                # Computing the number of vfreq units to put between each station, given the number of sources and the min/max vfreqs
                STATION_STEP = (
                    self.SETTINGS["MAX_VFREQ"] - self.SETTINGS["MIN_VFREQ"]
                ) / (len(self.SOURCES) - 1)

                # The station vfreq we want is the last channel vfreq + the step
                # we computed earlier (rounded to prevent decimal vfreqs!)
                station_vfreq = self.STATIONS[-1].VFREQ + round(STATION_STEP)

            station = Station(
                vfreq=station_vfreq, source=src, audio_engine=self._AUDIO_ENGINE
            )

            self.STATIONS.append(station)


class Station:

    ID = None
    URI = None
    NAME = None

    VFREQ = None
    AUDIOTRACK = None

    def __repr__(self):
        return "<{}> [F:{}] [V:{}]".format(self.NAME, self.VFREQ, self.get_volume())

    def __init__(self, vfreq=None, source=None, audio_engine=None):

        assert audio_engine is not None
        assert source is not None

        self.VFREQ = vfreq
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
        return self.AUDIOTRACK.get_volume(*args, **kwargs)

    def play(self):
        self.AUDIOTRACK.play()
        logger.debug("Changed state of <{}> to PLAYING".format(self.NAME))
