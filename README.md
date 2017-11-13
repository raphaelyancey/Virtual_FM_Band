# Virtual_FM_Band
A virtual FM band playing simultaneous sounds over virtual frequencies.

```
                                                                        
Track 1        Track 2        Track 3        Track 4       Track n        
   |              |              |              |             |         
   |--------------|--------------|--------------|-------------|         
                                                                        
   <---------------------------------------------------------->         
88.7Mhz                  virtual frequency                108.0Mhz      
                                                                        
```

Technically, it's a mixer with multiple tracks that takes care of the volume of each track (fade in / fade out) while moving along the virtual frequency.

## Installation

In the project root:
* `brew install portaudio mad` (OSX) or `apt-get install libmad0-dev portaudio19-dev libasound-dev` (Debian)
* `pip install virtualenv` (if not already installed on your machine)
* `virtualenv --python=python2.7` (or whatever Python 2 binary you've got)
* `source bin/activate`
* `pip install -r requirements.txt`
