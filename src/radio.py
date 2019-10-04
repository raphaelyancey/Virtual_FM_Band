import logging
from icecream import ic
import os

logger = logging.getLogger('virtual_fm_band')


class Radio():

    SETTINGS = {
        'NOISE_PATH': os.getenv('NOISE_PATH', '{}/audio/noise'.format(os.getenv('HOME'))),
        'AUDIO_PATH': os.getenv('AUDIO_PATH', '{}/audio'.format(os.getenv('HOME'))),
        'VOLUME_STEP': os.getenv('VOLUME_STEP', 1),
        'TUNED_LED_PIN': int(os.getenv('TUNED_LED_PIN', 25)),
        'VOLUME_PIN_CLK': int(os.getenv('VOLUME_PIN_CLK', 5)),
        'VOLUME_PIN_DT': int(os.getenv('VOLUME_PIN_DT', 6)),
        'VOLUME_PIN_SW': int(os.getenv('VOLUME_PIN_SW', 13)),
        'TUNING_PIN_CLK': int(os.getenv('TUNING_PIN_CLK', 17)),
        'TUNING_PIN_DT': int(os.getenv('TUNING_PIN_DT', 27)),
        'TUNING_PIN_SW': int(os.getenv('TUNING_PIN_SW', 22)),
        'NOISE_TRIGGER_THRESHOLD': float(os.getenv('NOISE_TRIGGER_THRESHOLD', 0.9)),
        'MIN_VFREQ': 1,
        'MAX_VFREQ': 300,  # TODO: create a user-friendly, computed env var to customize the transition speed from a station to the next?
    }

    STATE = {
        'CURRENT_VFREQ': SETTINGS['MIN_VFREQ'],
    }

    SOURCES = []

    ALLOWED_FILE_EXTENSIONS = ('.mp3',)

    def init(self):

        logger.debug('Settings:')
        ic(self.SETTINGS)

        logger.debug('Looking for station sources...')
        self.discover_files()
        #self.discover_streams()

        self.create_stations()

        return self

    def discover_files(self):

        audio_path_tree = os.walk(os.path.abspath(self.SETTINGS['AUDIO_PATH']))

        for root, dirs, files in audio_path_tree:

            # Only keeps MP3 files in the root dir of the audio path
            # TODO: handle other files
            for file in [f for f in files if f.endswith(self.ALLOWED_FILE_EXTENSIONS) and root == os.path.abspath(self.SETTINGS['AUDIO_PATH'])]:

                logger.debug('Found a source file:')

                # Remove the extension, whatever it is
                source_name = os.path.basename(file)
                for ext in self.ALLOWED_FILE_EXTENSIONS:
                    # It is a suffix if the index it's found at + the length of the extension equals the whole length
                    # (already includes the 0-offset)
                    is_suffix = source_name.rfind(ext) + len(ext) == len(source_name)
                    source_name = source_name.replace(ext, '') if is_suffix else source_name

                source = {
                    'type': 'file',
                    'uri': os.path.join(root, file),
                    'name': os.path.basename(file)[:-4]
                }

                logger.debug(source)

                # Adds it to the sources list
                self.SOURCES.append(source)

        return [src for src in self.SOURCES if src.type == 'file']

    def discover_streams(self):
        pass

    def create_stations(self):
        pass
