from app import databases, constants
import unittest
import constants_testing as ct
import logging
import os

logging.basicConfig(level=ct.LOG_LEVEL)
logger = logging.getLogger(__name__)


class TestDatabasesMethods(unittest.TestCase):

    def setUp(self):
        databases.dropTables()
        databases.initTables()

    def test_add_bad_song_to_history(self):

        # test empty args
        response_one = databases.History.addSongToHistory(None, None, None)
        response_two = databases.History.addSongToHistory("junk", None, None)
        response_three = databases.History.addSongToHistory(None, "junk", None)
        response_four = databases.History.addSongToHistory(None, None, "junk")
        response_five = databases.History.addSongToHistory("junk", "junk", None)
        response_six = databases.History.addSongToHistory("junk", None, "junk")
        response_seven = databases.History.addSongToHistory(None, "junk", "junk")
        assert response_one == constants.FAILED_UUID_STR
        assert response_two == constants.FAILED_UUID_STR
        assert response_three == constants.FAILED_UUID_STR
        assert response_four == constants.FAILED_UUID_STR
        assert response_five == constants.FAILED_UUID_STR
        assert response_six == constants.FAILED_UUID_STR
        assert response_seven == constants.FAILED_UUID_STR

    def test_add_good_song_to_history(self):
        # test solid args
        response = databases.History.addSongToHistory(ct.VALID_DATABASE_STRING, ct.VALID_DATABASE_STRING, ct.VALID_DATABASE_STRING)
        assert response != constants.FAILED_UUID_STR

        response_verified = databases.History.select().where(databases.History.uuid == response).get()
        assert response_verified.uuid == response
        assert response_verified.songLink == ct.VALID_DATABASE_STRING
        assert response_verified.songPath == ct.VALID_DATABASE_STRING
        assert response_verified.songTitle == ct.VALID_DATABASE_STRING

    def test_add_bad_song_to_queue(self):

        # test bad args
        response_one = databases.SongInQueue.addSongToQueue(None, None, None)
        response_two = databases.SongInQueue.addSongToQueue("junk", None, None)
        response_three = databases.SongInQueue.addSongToQueue(None, "junk", None)
        response_four = databases.SongInQueue.addSongToQueue(None, None, "junk")
        response_five = databases.SongInQueue.addSongToQueue("junk", "junk", None)
        response_six = databases.SongInQueue.addSongToQueue("junk", None, "junk")
        response_seven = databases.SongInQueue.addSongToQueue(None, "junk", "junk")

        assert response_one == constants.FAILED_UUID_STR
        assert response_two == constants.FAILED_UUID_STR
        assert response_three == constants.FAILED_UUID_STR
        assert response_four == constants.FAILED_UUID_STR
        assert response_five == constants.FAILED_UUID_STR
        assert response_six == constants.FAILED_UUID_STR
        assert response_seven == constants.FAILED_UUID_STR

    def test_add_good_song_to_queue(self):
        # test solid args
        response = databases.SongInQueue.addSongToQueue(ct.VALID_DATABASE_STRING, ct.VALID_DATABASE_STRING, ct.VALID_DATABASE_STRING)
        assert response != constants.FAILED_UUID_STR

        response_verified = databases.SongInQueue.select().where(databases.SongInQueue.uuid == response).get()
        assert response_verified.uuid == response
        assert response_verified.songLink == ct.VALID_DATABASE_STRING
        assert response_verified.songPath == ct.VALID_DATABASE_STRING
        assert response_verified.songTitle == ct.VALID_DATABASE_STRING

if __name__ == "__main__":
    unittest.main()
    os.remove(constants.DB_NAME)