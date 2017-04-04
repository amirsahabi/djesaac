# dbmonitor.py
import time
import threading
import databases
import utility

class DBMonitor(threading.Thread):
    def run(self):
        while(True):
            while(databases.SongInQueue.select().wrapped_count() > 0):
                song = databases.SongInQueue.select().order_by(databases.SongInQueue.dateAdded).get()

                utility.playSong(song.songPath)

                # add to History
                databases.History.addSongToHistory(song.songTitle, song.songLink)

                # remove song from queue
                databases.SongInQueue.delete().where(databases.SongInQueue.uuid == song.uuid).execute()
            time.sleep(3)
