from peewee import *
import uuid
import datetime
from playhouse.sqlite_ext import SqliteExtDatabase

# create database
db = SqliteExtDatabase('djesaac.db')

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
            print('Failed to insert into history table')
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
            print("Failed to insert to queue table")
            return -1

TABLE_LIST = [SongInQueue, History]

def initTables():
    db.create_tables(TABLE_LIST)
def dropTables():
    try:
        db.drop_tables(TABLE_LIST)
    except:
        print("couldn't drop tables")
