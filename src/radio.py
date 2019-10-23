import logging
from icecream import ic
import os
from typing import Sequence
from audio_engine import AudioEngine, AudioTrack
import hashlib
from scipy.interpolate import interp1d
from numpy import interp
import random
from functools import reduce

logger = logging.getLogger("virtual_fm_band")


class Radio:

    """
    This class handles only the logic : stations, static noise, volumes.
    All of the "hardware" interface should be outside of it.
    """

    SETTINGS = {
        "NOISE_PATH": None,
        "AUDIO_PATH": None,
        "NOISE_TRIGGER_THRESHOLD": None,
        "MIN_VFREQ": None,
        "MAX_VFREQ": None,  # TODO: create a user-friendly, computed env var to customize the transition speed from a station to the next?
    }

    STATE = {"CURRENT_VFREQ": SETTINGS["MIN_VFREQ"]}

    STATION_SOURCES = []
    STATIC_NOISE_SOURCES = []

    STATIONS = []
    STATIC_NOISES = []

    ALLOWED_FILE_EXTENSIONS = (".mp3",)

    _AUDIO_ENGINE = None

    # These callbacks can just be passed as kwarg when instantiating the class
    CALLBACKS = {
        'on_tuned_station': None,
        'on_detuned_station': None
    }

    def __init__(self, settings=None, *args, **kwargs):
        """
        Discovers audio sources and creates stations
        """

        assert settings is not None

        logger.debug("Settings:")
        self.SETTINGS.update(settings)
        ic(self.SETTINGS)

        logger.debug("Looking for station and noise sources...")
        self.discover_files()
        # self.discover_streams()

        logger.debug("Starting audio engine...")
        self._AUDIO_ENGINE = AudioEngine()

        logger.debug("Creating stations...")
        self.create_stations()

        logger.debug("Creating static noise tracks...")
        self.create_static_noise()

        logger.info(
            "Stations and static noise are ready, signaling the audio engine..."
        )
        self._AUDIO_ENGINE.run()

        # Handling callbacks
        for kwarg in kwargs:
            if kwarg in self.CALLBACKS and callable(kwargs[kwarg]):
                self.CALLBACKS[kwarg] = kwargs[kwarg]


    def discover_files(self):

        """
        Discovers audio files (to create stations and static noise sources)
        """

        audio_path = os.path.abspath(self.SETTINGS["AUDIO_PATH"])
        static_noise_path = os.path.abspath(self.SETTINGS["NOISE_PATH"])

        for path in [audio_path, static_noise_path]:

            if path == audio_path:
                target = self.STATION_SOURCES
            elif path == static_noise_path:
                target = self.STATIC_NOISE_SOURCES

            for file in [
                f for f in os.listdir(path) if f.endswith(self.ALLOWED_FILE_EXTENSIONS)
            ]:

                logger.debug("Found a source file: {}".format(file))

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
                    "uri": "file://{}".format(os.path.join(path, file)),
                    "name": os.path.basename(file)[:-4],
                }

                # Adds it to the sources list, given its type
                target.append(source)

    def discover_streams(self):
        pass

    def create_stations(self):

        for src in self.STATION_SOURCES:

            station_vfreq = None

            # If it is the first station to be created...
            if len(self.STATIONS) == 0:
                station_vfreq = self.SETTINGS["MIN_VFREQ"]

            # If it is the last one...
            elif len(self.STATIONS) == (len(self.STATION_SOURCES) - 1):
                station_vfreq = self.SETTINGS["MAX_VFREQ"]

            else:
                # Computing the number of vfreq units to put between each station, given the number of sources and the min/max vfreqs
                STATION_STEP = (
                    self.SETTINGS["MAX_VFREQ"] - self.SETTINGS["MIN_VFREQ"]
                ) / (len(self.STATION_SOURCES) - 1)

                # The station vfreq we want is the last channel vfreq + the step
                # we computed earlier (rounded to prevent decimal vfreqs!)
                station_vfreq = self.STATIONS[-1].VFREQ + round(STATION_STEP)

            station = Station(
                vfreq=station_vfreq, source=src, audio_engine=self._AUDIO_ENGINE
            )

            self.STATIONS.append(station)

    def create_static_noise(self):

        for src in self.STATIC_NOISE_SOURCES:
            noise = StaticNoise(source=src, audio_engine=self._AUDIO_ENGINE)
            self.STATIC_NOISES.append(noise)

    def get_stations_volumes_for_vfreq(self, vfreq):

        """
        Computes and returns the volumes of the stations for a given vfreq
        """

        volumes = []

        for station in self.STATIONS:
            station_volume = self.get_station_volume_for_vfreq(station, vfreq)
            volumes.append((station, round(station_volume, 1)))

        return volumes

    def get_station_volume_for_vfreq(self, station, vfreq):

        """
        Returns the volume a station should be set at, given a vfreq
        """

        lower_station, upper_station = self.get_neighbor_stations_for_vfreq(vfreq)

        if station.VFREQ < lower_station.VFREQ or station.VFREQ > upper_station.VFREQ:
            # The station vfreq is outside the boundaries = null volume
            return 0
        else:
            # Inside boundaries, compute with `vol = 100 - abs(x)` with x between -100 and 100
            # When x = -100, vol = 0
            # When x = 0, vol = 100
            # When x = 100, vol = 0
            # |/|\| (poor ASCII art)
            #   0
            #   
            # NOTE: `station` can only be one of `lower_station` or 
            #       `upper_station` because we return 0 before if it's not.
            # 
            if station == lower_station:
                scale = [0, 100]
            elif station == upper_station:
                scale = [-100, 0]

            # Translating the vfreq on a scale of [-100, 100] (except when first or last station) for easy calculations
            interpolated_vfreq = interp(
                vfreq, [lower_station.VFREQ, upper_station.VFREQ], scale
            )

            # Creating the volume curve (x = vfreq, y = volume)
            # https://docs.scipy.org/doc/scipy/reference/tutorial/interpolate.html#d-interpolation-interp1d for infos
            x = [-100, -10, 0, 10, 100]
            y = [0, 10, 100, 10, 0]
            f = interp1d(x, y)

            volume = f(interpolated_vfreq)
            return volume / 100

    def get_neighbor_stations_for_vfreq(self, vfreq):

        # By default, the boundaries are [first stations] > vfreq > [last station]
        lower_station = self.STATIONS[0]
        upper_station = self.STATIONS[-1]

        # Then for each channel we update them by comparing their vfreq to the requested vfreq
        for i, station in enumerate(self.STATIONS):
            if i < len(self.STATIONS) - 1:
                next_station_vfreq = self.STATIONS[i + 1].VFREQ
                if vfreq >= station.VFREQ and vfreq <= next_station_vfreq:
                    lower_station = self.STATIONS[i]
                    upper_station = self.STATIONS[i + 1]
                    break
            else:
                # If there isn't any more channel, the boundaries are the two last channels
                lower_station = self.STATIONS[-2]
                upper_station = self.STATIONS[-1]

        return (lower_station, upper_station)

    def set_stations_volumes(self, stations_volumes):
        for station, volume in stations_volumes:
            station.set_volume(volume)

    def compute_static_noise_volume(self, stations_volumes):

        if len(self.STATIC_NOISES) == 0:
            return

        def no_noise():
            for noise in self.STATIC_NOISES:
                noise.set_volume(0)

        # Only triggers when in-between stations, i.e. when none of the volumes is over NOISE_TRIGGER_THRESHOLD
        if len([v for _, v in stations_volumes if v > self.SETTINGS['NOISE_TRIGGER_THRESHOLD']]) == 0:
            no_noise()
            index = random.randint(0, (len(self.STATIC_NOISES) - 1))  # Select a random noise track
            volume = round(random.uniform(0.5, 0.8), 1) # And a random volume
            self.STATIC_NOISES[index].set_volume(volume)
        else:
            no_noise()

    def set_vfreq(self, vfreq):

        logger.info("Virtual frequency changed to <{}>".format(vfreq))

        stations_volumes = self.get_stations_volumes_for_vfreq(vfreq)
        ic(stations_volumes)
        # self.draw(stations_volumes)
        self.set_stations_volumes(stations_volumes)
        self.compute_static_noise_volume(stations_volumes)

        # If all volumes < 1.0, no vfreq is tuned. Else, a vfreq is tuned.
        detuned = reduce(lambda a, v: a and v < 1.0, [v for s, v in stations_volumes], True)
        if not detuned:
            if self.CALLBACKS['on_tuned_station'] is not None:
                self.CALLBACKS['on_tuned_station']()
        else:
            if self.CALLBACKS['on_detuned_station'] is not None:
                self.CALLBACKS['on_detuned_station']()


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


class StaticNoise:

    ID = None
    URI = None

    AUDIOTRACK = None

    def __init__(self, source=None, audio_engine=None):

        assert audio_engine is not None
        assert source is not None

        self.URI = source["uri"]
        self.ID = hashlib.md5(self.URI.encode("utf-8")).hexdigest()[:8]
        self.AUDIOTRACK = AudioTrack(
            id=self.ID, uri=self.URI, audio_engine=audio_engine
        )

        logger.info("Initialized static noise ({id})".format(id=self.ID))

    def set_volume(self, *args, **kwargs):
        self.AUDIOTRACK.set_volume(*args, **kwargs)
        logger.debug(
            "Changed volume of static noise ({}) to {}".format(self.ID, args[0])
        )

    def get_volume(self, *args, **kwargs):
        return self.AUDIOTRACK.get_volume(*args, **kwargs)
