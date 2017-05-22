# constants.py
# define some constants to be used in the program

UUID_LENGTH = 36
ARD_PORT_LENGTH = 25
ARD_PIN_LENGTH = 10

PORT = 3000
DEBUGMODE = True
EMPTY_UUID = ' ' * UUID_LENGTH
FAILED_UUID_STR = '-1'

SONG_FORMAT = 'ogg'
SONG_FORMAT_EXTENSION = '.ogg'
SONG_BITRATE = '128k'
ARDUINO_WINDOWS_LOC_DEFAULT = 'COM4'
ARDUINO_OSX_LOC_DEFAULT = '/dev/tty.usbmodem1421'
ARDUINO_UBUNTU_LOC_DEFAULT = '/dev/ttyACM0'
ARDUINO_DEFAULT_RED_PIN = 'd:3:p'
ARDUINO_DEFAULT_GREEN_PIN = 'd:5:p'
ARDUINO_DEFAULT_BLUE_PIN = 'd:6:p'
BOARD_UNINITIALIZED = ' ' * ARD_PORT_LENGTH
PIN_UNINITIALIZED = ' ' * ARD_PIN_LENGTH
EMPTY_INPUT = ''
ACT_HIST_ADD = 'add'
ACT_HIST_NEXT = 'next'
ACT_HIST_REM = 'rem'
ACT_HIST_PLAY_STOP = 'playstop'
START_STOP = 'startstop'

DB_NAME = 'djesaac.db'
DB_PREPROC_PROCESS = 'process'
DB_PREPROC_DECOMISSION = 'decomission'
UNKNOWN_COMMAND = 'unknown command'

RESPONSE = 'response'
ERROR = 'error'
SUCCESS = 'success'
FAILURE = 'failure'

WINDOW_SIZE_MSEC = 0.02
WINDOW_SIZE_SEC = int(WINDOW_SIZE_MSEC * 1000)
LOG_LEVEL = 20 # 0: NOT, 10: DEBUG, 20: INFO, 30: WARNING, 40: ERROR, 50: CRITICAL

PLAY = 1
STOP = 0
SONG_BEGINNING_TIME = 0.0

YOUTUBE = 'youtube.com'
SOUNDCLOUD = 'soundcloud.com'
CONTENT_LINK = 'content-link'
SIDE_BAR = 'soundBadge__avatarLink'
HTTPS = 'https://www.'

YDL_OPTIONS = {
            'format': 'bestaudio',
            'extractaudio': True,
            'audioformat': 'wav',
            'outtmpl': 'music/%(id)s',
            'noplaylist': True,
        }


ARDUINO_BOARD = 'board'
ARDUINO_RED = 'red'
ARDUINO_BLUE = 'blue'
ARDUINO_GREEN = 'green'
AUTOPLAY = 'autoplay'
LATENCY = 'latency'
