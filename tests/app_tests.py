import unittest
import constants_testing as ct
from app import app, constants, databases
import logging
import json
import os


logging.basicConfig(level=ct.LOG_LEVEL)
logger = logging.getLogger(__name__)


class TestAppMethods(unittest.TestCase):

    def setUp(self):
        # create testing app
        app.app.config['TESTING'] = True
        self.app = app.app.test_client()
        # create database relation
        databases.dropTables()
        databases.initTables()

        app.musicIsPlaying.value = -1
        app.init_background_procs()

        # wait for dbmonitor to init
        while app.musicIsPlaying.value == -1:
            pass

    def tearDown(self):
        app.monitorProc.terminate()

    def test_get_home_page(self):
        logger.info('test_get_home_page')

        # test empty get
        response = self.app.get('/')
        assert response.status == ct.RESPONSE_OK

    def test_post_home_page(self):
        logger.info('test_post_home_page')

        # test empty post
        response = self.app.post('/')
        assert response.status == ct.RESPONSE_BAD

        # test invalid post
        response = self.app.post('/', data={
            'command': ct.INVALID_COMMAND
        })

        response_data = json.loads(response.data)
        assert response.status == ct.RESPONSE_OK
        assert response_data[constants.RESPONSE] == constants.FAILURE
        assert response_data[constants.ERROR] == constants.UNKNOWN_COMMAND

        # test start/stop request
        initial_music_playing = app.musicIsPlaying.value

        response = self.app.post('/', data={
            'command' : constants.START_STOP
        })

        response_data = json.loads(response.data)
        assert response.status == ct.RESPONSE_OK
        assert response_data[constants.RESPONSE] == constants.SUCCESS
        assert initial_music_playing != app.musicIsPlaying.value
        assert initial_music_playing == (1 + app.musicIsPlaying.value) % 2

    def test_get_settings(self):
        logger.info('test_get_settings')

        # test empty get
        init_board = ''.join(app.arduinoPortLoc[:])
        init_red = ''.join(app.arduinoRedPin[:])
        init_blue = ''.join(app.arduinoBluePin[:])
        init_green = ''.join(app.arduinoGreenPin[:])
        init_latency = app.latency.value
        init_autoplay = app.autoPlayMusic.value

        response = self.app.get('/settings/')
        response_data = json.loads(response.data)

        assert response.status == ct.RESPONSE_OK
        assert response_data[constants.ARDUINO_BOARD] == init_board
        assert response_data[constants.ARDUINO_RED] == init_red
        assert response_data[constants.ARDUINO_BLUE] == init_blue
        assert response_data[constants.ARDUINO_GREEN] == init_green
        assert response_data[constants.AUTOPLAY] == str(init_autoplay)
        assert response_data[constants.LATENCY] == str(init_latency)

    def test_post_settings(self):
        logger.info('test_post_settings')

        # test empty post
        response = self.app.post('/settings/')
        assert response.status == ct.RESPONSE_BAD

        # test a good post
        init_board = ''.join(app.arduinoPortLoc[:])
        init_red = ''.join(app.arduinoRedPin[:])
        init_blue = ''.join(app.arduinoBluePin[:])
        init_green = ''.join(app.arduinoGreenPin[:])
        init_latency = app.latency.value
        init_autoplay = app.autoPlayMusic.value

        set_string = 'asdfsa'
        new_board = set_string
        new_red = set_string
        new_blue = set_string
        new_green = set_string
        new_latency = 123.0
        new_autoplay = 'false' if init_autoplay == 1.0 else 'true'

        response = self.app.post('/settings/', data={
            constants.ARDUINO_BOARD: new_board,
            constants.ARDUINO_RED: new_red,
            constants.ARDUINO_BLUE: new_blue,
            constants.ARDUINO_GREEN: new_green,
            constants.LATENCY: new_latency,
            constants.AUTOPLAY: new_autoplay
        })

        response_data = json.loads(response.data)

        changed_board = ''.join(app.arduinoPortLoc[:])
        changed_red = ''.join(app.arduinoRedPin[:])
        changed_blue = ''.join(app.arduinoBluePin[:])
        changed_green = ''.join(app.arduinoGreenPin[:])
        changed_latency = app.latency.value
        changed_autoplay = app.autoPlayMusic.value

        assert response.status == ct.RESPONSE_OK
        assert response_data[constants.ARDUINO_BOARD] != init_board
        assert response_data[constants.ARDUINO_BOARD] == changed_board
        assert response_data[constants.ARDUINO_BLUE] != init_blue
        assert response_data[constants.ARDUINO_BLUE] == changed_blue
        assert response_data[constants.ARDUINO_RED] != init_red
        assert response_data[constants.ARDUINO_RED] == changed_red
        assert response_data[constants.ARDUINO_GREEN] != init_green
        assert response_data[constants.ARDUINO_GREEN] == changed_green
        assert response_data[constants.LATENCY] != init_latency
        assert response_data[constants.LATENCY] == changed_latency
        assert response_data[constants.AUTOPLAY] != init_autoplay
        assert response_data[constants.AUTOPLAY] == changed_autoplay

    def test_invalid_latency_settings_post(self):

        # test a bad post (invalid latency)
        init_board = ''.join(app.arduinoPortLoc[:])
        init_red = ''.join(app.arduinoRedPin[:])
        init_blue = ''.join(app.arduinoBluePin[:])
        init_green = ''.join(app.arduinoGreenPin[:])
        init_latency = app.latency.value
        init_autoplay = app.autoPlayMusic.value

        set_string = 'asdfsa'
        new_board = set_string
        new_red = set_string
        new_blue = set_string
        new_green = set_string
        new_latency = set_string
        new_autoplay = set_string

        response = self.app.post('/settings/', data={
            constants.ARDUINO_BOARD: new_board,
            constants.ARDUINO_RED: new_red,
            constants.ARDUINO_BLUE: new_blue,
            constants.ARDUINO_GREEN: new_green,
            constants.LATENCY: new_latency,
            constants.AUTOPLAY: new_autoplay
        })

        response_data = json.loads(response.data)

        assert response.status == ct.RESPONSE_OK
        assert response_data[constants.RESPONSE] == constants.FAILURE
        assert ''.join(app.arduinoPortLoc[:]) == init_board
        assert ''.join(app.arduinoRedPin[:]) == init_red
        assert ''.join(app.arduinoBluePin[:]) == init_blue
        assert ''.join(app.arduinoGreenPin[:]) == init_green
        assert app.autoPlayMusic.value == init_autoplay
        assert app.latency.value == init_latency


if __name__ == "__main__":
    unittest.main()
    os.remove(constants.DB_NAME)
