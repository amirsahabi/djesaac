import unittest
import constants_testing as ct
# from app import app, databases, constants
from app import app, constants, databases
import logging
import json


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

    def tearDown(self):
        pass

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



if __name__ == "__main__":
    unittest.main()
