# DJESAAC

## About

This is a small web app designed to take music requests from users and play a lightshow
controlled by an arduino along to the music

## Installation

### Server

The server is written in python and depends on the libraries
[flask](http://flask.pocoo.org/), [peewee](https://pypi.python.org/pypi/peewee),
[numpy](http://www.numpy.org/),
[requests](http://docs.python-requests.org/en/master/),
[youtube_dl](https://pypi.python.org/pypi/youtube_dl), 
[pyfirmata](https://pypi.python.org/pypi/pyFirmata), [pygame](https://www.pygame.org), 
[pysoundfile](https://pysoundfile.readthedocs.io/en/0.9.0/) and [pydub](https://pypi.python.org/pypi/pydub) 
(all of which are available to install through pip). youtube_dl and pydub also rely on [ffmpeg](https://ffmpeg.org/)
which can be installed on OS X through brew, on linux through your favorite package manager.

### Arduino

The Arduino Uno may be programmed through the Arduino IDE (v1.6.3). The sketch StandardFirmata.ino is available in the IDE under  File>Examples>Firmata>StandardFirmata (The sketch is also provided in this repository under Arduino>StandardFirmata.ino). As documented in app>constants.py the pin configuration uses three PWM digital output pins.

## How to Run

From the app folder, start the server from a command line with the following command
```
$ python app.py
```

The servers default location is at port 3000 so you can navigate in a browser to
localhost:3000 to be sure the server is up and running
