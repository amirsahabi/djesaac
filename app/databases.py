from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase
import uuid
import datetime
import logging
import constants

logging.basicConfig(level=constants.LOG_LEVEL)

# create database
db = SqliteExtDatabase(constants.DB_NAME)
logger = logging.getLogger(__name__)
# create base class,
# all further database classes should extend this one
class Base(Model):
    class Meta:
        database = db

class History(Base):
    uuid            = UUIDField()
    songTitle       = CharField()
    songLink        = CharField()
    songPath        = CharField()
    dateTimeFinish  = DateTimeField()

    @staticmethod
    def addSongToHistory(title, link, path):
        try:
            eventInHistory = History()
            eventInHistory.uuid = uuid.uuid1()
            eventInHistory.songTitle = title
            eventInHistory.songLink = link
            eventInHistory.songPath = path
            eventInHistory.dateTimeFinish = datetime.datetime.now()
            eventInHistory.save()

            return eventInHistory.uuid
        except:
            logger.info('Failed to insert into history table')
            return constants.FAILED_UUID_STR


class SongInQueue(Base):
    uuid        = UUIDField()
    songTitle   = CharField()
    songLink    = CharField()
    songPath    = CharField()
    dateAdded   = DateTimeField()

    @staticmethod
    def addSongToQueue(path, title, link):
        try:
            newSong = SongInQueue()
            newSong.uuid = uuid.uuid1()
            newSong.songTitle = title
            newSong.songPath = path
            newSong.songLink = link
            newSong.dateAdded = datetime.datetime.now()
            newSong.save()

            return newSong.uuid
        except:
            logger.info("Failed to insert to queue table")
            return constants.FAILED_UUID_STR

class PreprocessRequest(Base):
    uuid        = UUIDField()
    songPath    = CharField(null=True)
    songUUID    = UUIDField()
    requestType = CharField()
    datetime    = DateTimeField()

    @staticmethod
    def newPreProcessRequest(songPath, songUUID):
        try:
            npp = PreprocessRequest()
            npp.uuid = uuid.uuid1()
            npp.songPath = songPath
            npp.songUUID = songUUID
            npp.requestType = constants.DB_PREPROC_PROCESS
            npp.datetime = datetime.datetime.now()
            npp.save()

            return npp.uuid
        except:
            return constants.FAILED_UUID_STR

    @staticmethod
    def newDecomissionRequest(songUUID):
        try:
            nd = PreprocessRequest()
            nd.uuid = uuid.uuid1()
            nd.songUUID = songUUID
            nd.requestType = constants.DB_PREPROC_DECOMISSION
            nd.datetime = datetime.datetime.now()
            nd.save()

            return nd.uuid
        except:
            return constants.FAILED_UUID_STR

    @staticmethod
    def hasntBeenProcessed(reqID):
        if reqID == constants.FAILED_UUID_STR:
            return False
        else:
            return PreprocessRequest.select().where(PreprocessRequest.uuid == reqID).wrapped_count() > 0

class ActionHistory(Base):
    uuid        = UUIDField()
    newTitle    = CharField()
    newID       = UUIDField(null=True)
    newLink     = CharField()
    oldTitle    = CharField()
    oldID       = UUIDField(null=True)
    oldLink     = CharField()
    eventType   = CharField()
    datetime    = DateTimeField()
    canBeRemoved= BooleanField(default=True)

    @staticmethod
    def onStartUp():
        try:
            newAction           = ActionHistory()
            newAction.uuid      = uuid.uuid1()
            newAction.newTitle  = constants.EMPTY_INPUT
            newAction.newLink   = constants.EMPTY_INPUT
            newAction.oldTitle  = constants.EMPTY_INPUT
            newAction.oldLink   = constants.EMPTY_INPUT
            newAction.eventType = constants.EMPTY_INPUT
            newAction.datetime = datetime.datetime.now()
            newAction.canBeRemoved = False;
            newAction.save()
            return newAction.uuid
        except:
            return constants.FAILED_UUID_STR


    @staticmethod
    def cleanup(thresholdDateTime):
        query = ActionHistory.delete().where(ActionHistory.datetime < thresholdDateTime, ActionHistory.canBeRemoved == True)
        query.execute()

    @staticmethod
    def newNextSong(_newTitle, _newID, _newLink, _oldTitle, _oldID, _oldLink):
        try:
            newAction           = ActionHistory()
            newAction.uuid      = uuid.uuid1()
            newAction.newTitle  = _newTitle
            if(_newID is not None):
                newAction.newID = uuid.UUID(_newID)
            newAction.newLink   = _newLink
            newAction.oldTitle  = _oldTitle
            newAction.oldID     = uuid.UUID(_oldID)
            newAction.oldLink   = _oldLink
            newAction.datetime  = datetime.datetime.now()
            newAction.eventType = constants.ACT_HIST_NEXT
            newAction.save()
            return newAction.uuid
        except:
            return constants.FAILED_UUID_STR

    @staticmethod
    def newRemoveSong(_remTitle, _remID, _remLink):
        try:
            newAction           = ActionHistory()
            newAction.uuid      = uuid.uuid1()
            newAction.newTitle  = constants.EMPTY_INPUT
            newAction.newLink   = constants.EMPTY_INPUT
            newAction.oldTitle  = _remTitle
            newAction.oldID     = uuid.UUID(_remID)
            newAction.oldLink   = _remLink
            newAction.datetime  = datetime.datetime.now()
            newAction.eventType = constants.ACT_HIST_REM
            newAction.save()
            return newAction.uuid
        except:
            return constants.FAILED_UUID_STR

    @staticmethod
    def newAddSong(_addTitle, _addID, _addLink):
        try:
            newAction           = ActionHistory()
            newAction.uuid      = uuid.uuid1()
            newAction.newTitle  = _addTitle
            newAction.newID     = uuid.UUID(_addID)
            newAction.newLink   = _addLink
            newAction.oldTitle  = constants.EMPTY_INPUT
            newAction.oldLink   = constants.EMPTY_INPUT
            newAction.datetime  = datetime.datetime.now()
            newAction.eventType = constants.ACT_HIST_ADD
            newAction.save()

            return newAction.uuid
        except:
            return constants.FAILED_UUID_STR


TABLE_LIST = [SongInQueue, History, PreprocessRequest, ActionHistory]

def initTables():
    db.create_tables(TABLE_LIST)
    ActionHistory.onStartUp()
def dropTables():
    try:
        db.drop_tables(TABLE_LIST)
    except:
        logger.info("couldn't drop tables")
