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
