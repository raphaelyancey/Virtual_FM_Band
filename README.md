> 🚸 Currently rewriting from scratch using `gstreamer` (on the `dev` branch)

> Check out the real-life [GTA: San Andreas radio set](https://raphaelyancey.fr/projects/grand-theft-auto-san-andreas-radio-set.html) for an example use of this library

# Virtual_FM_Band

A virtual FM band playing simultaneous sounds over virtual frequencies.

```
                                                                        
Track 0        Track 1        Track 2        Track 3       Track N        
   |              |              |              |             |         
   |--------------|--------------|--------------|---- - - - --|         
                                                                        
   <------------------------------------------------- - - - -->         
                         virtual frequency                     
                                                                        
```

Technically, it's a mixer with multiple tracks that takes care of the volume of each track (fade in / fade out) while moving along the virtual frequency.

## Installation

```bash
curl https://raw.githubusercontent.com/raphaelyancey/Virtual_FM_Band/master/install.sh | bash
```

Read the [install.sh](/install.sh) script for details.

In a nutshell, it:
- Installs required packages
- Clones this repository
- Installs Python dependencies

## TODO
  - [ ] Handle streams as input
  - [ ] Add static noise between stations
  - [ ] Make swmixer play the files in loop
  - [ ] Do not play if the file is not to be heard anyway
  - [ ] Random start position

## List audio device IDs

After installing the required Python packages, execute this script in a Python shell.

```python
import pyaudio
p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')
for i in range(0, numdevices):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxOutputChannels')) > 0:
            print "Output Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name')
```
(inspired by https://stackoverflow.com/a/39677871/2544016)

## Troubleshooting

### `ERROR:root:Couldn't start swmixer:`

Make sure you specified the correct device index in the `.env` file. To list the device indexes, see https://stackoverflow.com/a/39677871/2544016.
