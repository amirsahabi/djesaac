from peewee import *
import uuid
import datetime
from playhouse.sqlite_ext import SqliteExtDatabase
import logging

logging.basicConfig(level=logging.INFO)

# create database
db = SqliteExtDatabase('djesaac.db')
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
            return -1


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
            return -1

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
            npp.requestType = "process"
            npp.datetime = datetime.datetime.now()
            npp.save()

            return npp.uuid
        except:
            return -1

    @staticmethod
    def newDecomissionRequest(songUUID):
        try:
            nd = PreprocessRequest()
            nd.uuid = uuid.uuid1()
            nd.songUUID = songUUID
            nd.requestType = "decomission"
            nd.datetime = datetime.datetime.now()
            nd.save()

            return nd.uuid
        except:
            return -1

    @staticmethod
    def hasntBeenProcessed(reqID):
        if reqID == -1:
            return False
        else:
            return PreprocessRequest.select().where(PreprocessRequest.uuid == reqID).wrapped_count() > 0

TABLE_LIST = [SongInQueue, History, PreprocessRequest]

def initTables():
    db.create_tables(TABLE_LIST)
def dropTables():
    try:
        db.drop_tables(TABLE_LIST)
    except:
        logger.info("couldn't drop tables")
