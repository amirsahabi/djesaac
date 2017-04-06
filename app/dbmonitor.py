# dbmonitor.py
import time
import threading
import databases
import utility

class DBMonitor(threading.Thread):
    def __init__(self):
        super(DBMonitor, self).__init__()
        self.songPlaying = None
        print("DBMonitor initialized")

    def run(self):
        while(True):
            while(databases.SongInQueue.select().wrapped_count() > 0):
                song = databases.SongInQueue.select().order_by(databases.SongInQueue.dateAdded).get()
                self.songPlaying = str(song.uuid)

                utility.playSong(song.songPath)

                # add to History
                databases.History.addSongToHistory(song.songTitle, song.songLink, song.songPath)

                # remove song from queue
                databases.SongInQueue.delete().where(databases.SongInQueue.uuid == song.uuid).execute()
            self.songPlaying = None
            time.sleep(3)
