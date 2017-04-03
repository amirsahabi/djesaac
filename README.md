# DJESAAC

## About

This is a small web app designed to take music requests from users and play a lightshow
controlled by an arduino along to the music

## Installation

### Server

The server is written in python and depends on the libraries
[flask](http://flask.pocoo.org/), [peewee](https://pypi.python.org/pypi/peewee),
and [youtube_dl](https://pypi.python.org/pypi/youtube_dl) (all of which are
available to install through pip).

## How to Run

From the app folder, start the server from a command line with the following command
```
$ python app.py
```

The servers default location is at port 3000 so you can navigate in a browser to
localhost:3000 to be sure the server is up and running
