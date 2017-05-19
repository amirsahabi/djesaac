from app import databases, constants
import unittest
import constants_testing as ct
import logging
import uuid
import datetime
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

    def test_new_bad_preprocess_request(self):
        response_one = databases.PreprocessRequest.newPreProcessRequest(None, None)
        response_two = databases.PreprocessRequest.newPreProcessRequest("junk", None)

        assert response_one == constants.FAILED_UUID_STR
        assert response_two == constants.FAILED_UUID_STR

    def test_new_good_preprocess_request(self):
        use_uuid = uuid.uuid1()
        response = databases.PreprocessRequest.newPreProcessRequest(ct.VALID_DATABASE_STRING, use_uuid)
        assert response != constants.FAILED_UUID_STR

        verify_response = databases.PreprocessRequest.select().where(databases.PreprocessRequest.uuid == response).get()
        assert verify_response.uuid == response
        assert verify_response.songPath == ct.VALID_DATABASE_STRING
        assert verify_response.songUUID == use_uuid
        assert verify_response.requestType == constants.DB_PREPROC_PROCESS

    def test_new_bad_decomission_request(self):

        response_one = databases.PreprocessRequest.newDecomissionRequest(None)
        assert response_one == constants.FAILED_UUID_STR

    def test_new_good_decomission_request(self):

        use_uuid = uuid.uuid1()
        response = databases.PreprocessRequest.newDecomissionRequest(use_uuid)
        assert response != constants.FAILED_UUID_STR

        verify_response = databases.PreprocessRequest.select().where(databases.PreprocessRequest.uuid == response).get()
        assert verify_response.uuid == response
        assert verify_response.songUUID == use_uuid
        assert verify_response.songPath is None
        assert verify_response.requestType == constants.DB_PREPROC_DECOMISSION

    def test_check_processing_request(self):

        # test empty
        use_uuid = uuid.uuid1()
        response_one = databases.PreprocessRequest.hasntBeenProcessed(None)
        response_two = databases.PreprocessRequest.hasntBeenProcessed(use_uuid)

        assert response_one is False
        assert response_two is False

        # insert and check
        req_id = databases.PreprocessRequest.newPreProcessRequest(ct.VALID_DATABASE_STRING, use_uuid)

        response = databases.PreprocessRequest.hasntBeenProcessed(req_id)
        assert response is True

        # remove from db
        databases.PreprocessRequest.delete().where(databases.PreprocessRequest.uuid == req_id).execute()

        # verify has been processed
        response = databases.PreprocessRequest.hasntBeenProcessed(req_id)
        assert response is False

    def test_action_history_valid_startup(self):

        init_obj = databases.ActionHistory.select().get()
        assert init_obj is not None
        assert init_obj.newTitle == constants.EMPTY_INPUT
        assert init_obj.newLink == constants.EMPTY_INPUT
        assert init_obj.oldTitle == constants.EMPTY_INPUT
        assert init_obj.oldLink == constants.EMPTY_INPUT
        assert init_obj.canBeRemoved is False

    def test_action_history_test_new_start_stop(self):

        response = databases.ActionHistory.newPlayStop()
        assert response != constants.FAILED_UUID_STR

        verify_obj = databases.ActionHistory.select().where(databases.ActionHistory.uuid == response).get()
        assert verify_obj.uuid == response
        assert verify_obj.newTitle == constants.EMPTY_INPUT
        assert verify_obj.newLink == constants.EMPTY_INPUT
        assert verify_obj.oldTitle == constants.EMPTY_INPUT
        assert verify_obj.oldLink == constants.EMPTY_INPUT
        assert verify_obj.eventType == constants.ACT_HIST_PLAY_STOP
        assert verify_obj.canBeRemoved is True

    def test_action_history_cleanup(self):

        # insert a few elements
        clear_elements = 3
        insert_elements = 10
        for iterator in range(insert_elements):
            if iterator == clear_elements:
                clear_datetime = datetime.datetime.now()
            databases.ActionHistory.newPlayStop()

        # verify there are 10 elements added
        count = databases.ActionHistory.select().wrapped_count()
        assert count == insert_elements + 1

        # cleanup
        databases.ActionHistory.cleanup(clear_datetime)
        count = databases.ActionHistory.select().wrapped_count()
        assert count == (insert_elements - clear_elements + 1)

    def test_bad_add_song(self):

        response_one = databases.ActionHistory.newAddSong(None, None, None)
        response_two = databases.ActionHistory.newAddSong("junk", None, None)
        response_three = databases.ActionHistory.newAddSong(None, "junk", None)
        response_four = databases.ActionHistory.newAddSong(None, None, "junk")
        response_five = databases.ActionHistory.newAddSong(None, "junk", "junk")
        response_six = databases.ActionHistory.newAddSong("junk", None, "junk")
        response_seven = databases.ActionHistory.newAddSong("junk", "junk", None)

        assert response_one == constants.FAILED_UUID_STR
        assert response_two == constants.FAILED_UUID_STR
        assert response_three == constants.FAILED_UUID_STR
        assert response_four == constants.FAILED_UUID_STR
        assert response_five == constants.FAILED_UUID_STR
        assert response_six == constants.FAILED_UUID_STR
        assert response_seven == constants.FAILED_UUID_STR


    def test_good_add_song(self):
        use_uuid = str(uuid.uuid1())
        response_uuid = databases.ActionHistory.newAddSong(ct.VALID_DATABASE_STRING, use_uuid, ct.VALID_DATABASE_STRING)

        assert response_uuid != constants.FAILED_UUID_STR

        response = databases.ActionHistory.select().where(databases.ActionHistory.uuid == response_uuid).get()

        assert str(response.newID) == use_uuid
        assert response.newTitle == ct.VALID_DATABASE_STRING
        assert response.newLink == ct.VALID_DATABASE_STRING
        assert response.oldID is None
        assert response.oldTitle == constants.EMPTY_INPUT
        assert response.oldLink == constants.EMPTY_INPUT
        assert response.eventType == constants.ACT_HIST_ADD

    def test_bad_remove_song(self):
        response_one = databases.ActionHistory.newRemoveSong(None, None, None)
        response_two = databases.ActionHistory.newRemoveSong("junk", None, None)
        response_three = databases.ActionHistory.newRemoveSong(None, "junk", None)
        response_four = databases.ActionHistory.newRemoveSong(None, None, "junk")
        response_five = databases.ActionHistory.newRemoveSong(None, "junk", "junk")
        response_six = databases.ActionHistory.newRemoveSong("junk", None, "junk")
        response_seven = databases.ActionHistory.newRemoveSong("junk", "junk", None)

        assert response_one == constants.FAILED_UUID_STR
        assert response_two == constants.FAILED_UUID_STR
        assert response_three == constants.FAILED_UUID_STR
        assert response_four == constants.FAILED_UUID_STR
        assert response_five == constants.FAILED_UUID_STR
        assert response_six == constants.FAILED_UUID_STR
        assert response_seven == constants.FAILED_UUID_STR

    def test_good_remove_song(self):
        use_uuid = str(uuid.uuid1())
        response_uuid = databases.ActionHistory.newRemoveSong(ct.VALID_DATABASE_STRING, use_uuid, ct.VALID_DATABASE_STRING)
        assert response_uuid != constants.FAILED_UUID_STR

        response = databases.ActionHistory.select().where(databases.ActionHistory.uuid == response_uuid).get()

        assert response.newID is None
        assert response.oldTitle == ct.VALID_DATABASE_STRING
        assert response.oldLink == ct.VALID_DATABASE_STRING
        assert str(response.oldID) == use_uuid
        assert response.newTitle == constants.EMPTY_INPUT
        assert response.newLink == constants.EMPTY_INPUT
        assert response.eventType == constants.ACT_HIST_REM

    def test_bad_next_song(self):

        responses = []
        use_items = [None, "junk"]
        for a in range(2):
            for b in range(2):
                for c in range(2):
                    for d in range(2):
                        for e in range(2):
                            for f in range(2):
                                responses.insert(len(responses),
                                    databases.ActionHistory.newNextSong(
                                        use_items[a],
                                        use_items[b],
                                        use_items[c],
                                        use_items[d],
                                        use_items[e],
                                        use_items[f]
                                    )
                                )
        for iterator in range(len(responses)):
            assert responses[iterator] == constants.FAILED_UUID_STR

    def test_good_next_song(self):
        old_uuid = uuid.uuid1()
        new_uuid = uuid.uuid1()

        resp_uuid = databases.ActionHistory.newNextSong(ct.VALID_DATABASE_STRING,
                                                        str(new_uuid),
                                                        ct.VALID_DATABASE_STRING,
                                                        ct.VALID_DATABASE_STRING,
                                                        str(old_uuid),
                                                        ct.VALID_DATABASE_STRING)

        assert resp_uuid != constants.FAILED_UUID_STR
        # get the object and validate inputs

        response = databases.ActionHistory.select().where(databases.ActionHistory.uuid == resp_uuid).get()
        assert response.uuid == resp_uuid
        assert response.oldLink == ct.VALID_DATABASE_STRING
        assert response.oldTitle == ct.VALID_DATABASE_STRING
        assert response.oldID == old_uuid
        assert response.newLink == ct.VALID_DATABASE_STRING
        assert response.newLink == ct.VALID_DATABASE_STRING
        assert response.newID == new_uuid
        assert response.eventType == constants.ACT_HIST_NEXT


if __name__ == "__main__":
    unittest.main()
    os.remove(constants.DB_NAME)