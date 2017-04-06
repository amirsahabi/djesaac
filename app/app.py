from __future__ import unicode_literals
from flask import Flask, request, render_template
from pydub import AudioSegment
import youtube_dl
import databases
import os
from dbmonitor import *

# create app
app = Flask(__name__)

monitorThread = None

# home
@app.route('/', methods=['GET','POST'])
def home():
    if(request.method == 'GET'):
        # get songs from queue
        songsInQueue = []
        try:
            for song in databases.SongInQueue.select().order_by(databases.SongInQueue.dateAdded):
                songsInQueue.append(song)
        except:
            print("Exception hit in home()")
            return render_template('home.html')

        return render_template('home.html', songs=songsInQueue, musicIsPlaying=monitorThread.musicIsPlaying)
    else:
        command = request.form['command']
        if command == "remove":
            #do delete
            uuid = str(request.form['songID'])

            #verify the song isn't playing
            if monitorThread.songPlaying == uuid and monitorThread.musicIsPlaying:
                return "Song can't be deleted, is currently playing"
            else:
                #delete from queue
                try:
                    databases.SongInQueue.delete().where(databases.SongInQueue.uuid == uuid).execute()
                except:
                    return "failure"
            return "success"
        elif command == "startstop":
            try:
                monitorThread.musicIsPlaying = not monitorThread.musicIsPlaying
            except:
                return "Can't stop this beat"
            return "success"

        else:
            return "unknown command"


@app.route('/add/', methods=['GET','POST'])
def add():
    if(request.method == 'GET'):
        return render_template('add.html')
    else:
        return addSongToQueue(request.form['link'])

@app.route('/history/', methods=['GET','POST'])
def history():
    if request.method == 'GET':
        history = []
        try:
            for event in databases.History.select().order_by(databases.History.dateTimeFinish.desc()):
                history.append(event)
        except:
            print("Exception hit in history()")
            return render_template('history.html')


        return render_template('history.html', history=history)
    else:
        songID = request.form['song']
        if songID != '':
            # check if it's cached
            try:
                song = databases.History.select().where(databases.History.uuid == songID).get()
                if os.path.isfile(song.songPath):
                    # file already downloaded, just
                    databases.SongInQueue.addSongToQueue(song.songPath, song.songTitle, song.songLink)
                else:
                    addSongToQueue(song.songLink)
            except:
                return 'failure'
            return 'success'
    return 'failure'


def addSongToQueue(songLink):
    try:
        # given songlink, use youtubedl to download it
        # set options
        dlOptions = {
            'format': 'bestaudio',
            'extractaudio' : True,
            'audioformat' : 'wav',
            'outtmpl' : 'music/%(id)s',
            'noplaylist' : True,
        }

        # create youtubedl object
        ydl = youtube_dl.YoutubeDL(dlOptions)

        if not songHasBeenDownloaded(songLink):

            # get metadata and download song while we're at it
            metadata = ydl.extract_info(songLink, download=True)

            # convert the song from mp3 to wav for reasons
            AudioSegment.from_file('./music/'+metadata['id']).export('./music/'+metadata['id']+'.wav', format='wav')

            # remove original
            os.remove('./music/'+metadata['id'])
        else:
            print("Song existed, no need to redownload")

            metadata = ydl.extract_info(songLink, download=False)

        # given metadata, log to database
        databases.SongInQueue.addSongToQueue('./music/'+metadata['id']+'.wav', metadata['title'], songLink)

    except:
        return "failure"

    return "success"

def songHasBeenDownloaded(songLink):
    #check both history and songqueue for the song
    songs = databases.SongInQueue.select().where(databases.SongInQueue.songLink == songLink)
    for song in songs:
        if os.path.isfile(song.songPath):
            #has been downloaded
            return True

    songs = databases.History.select().where(databases.History.songLink == songLink)
    for song in songs:
        if os.path.isfile(song.songPath):
            return True

    return False


# start server
if __name__ == "__main__":
    #drop and init tables
    # databases.dropTables()
    # databases.initTables()

    monitorThread = DBMonitor()
    monitorThread.start()

    app.debug = True
    app.run(threaded=True, port=3000, host='0.0.0.0', use_reloader=False)
