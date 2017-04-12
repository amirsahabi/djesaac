# constants.py
# define some constants to be used in the program

PORT                        = 3000
DEBUGMODE                   = True
EMPTY_UUID                  = ' ' * 36
FAILED_UUID_STR             = '-1'

ARDUINO_WINDOWS_LOC_DEFAULT = 'COM4'
ARDUINO_OSX_LOC_DEFAULT     = '/dev/tty.usbmodem1421'
ARDUINO_UBUNTU_LOC_DEFAULT  = '/dev/ttyACM0'
ARDUINO_PIN1                = 'd:3:p'
ARDUINO_PIN2                = 'd:5:p'
ARDUINO_PIN3                = 'd:6:p'

DB_NAME                     = 'djesaac.db'
DB_PREPROC_PROCESS          = 'process'
DB_PREPROC_DECOMISSION      = 'decomission'

RESPONSE                    = 'response'
ERROR                       = 'error'
SUCCESS                     = 'success'
FAILURE                     = 'failure'

WINDOW_SIZE_MSEC            = 0.02
WINDOW_SIZE_SEC             = int(WINDOW_SIZE_MSEC * 1000)
