from __future__ import unicode_literals
from flask import Flask, request, render_template
from pydub import AudioSegment
import youtube_dl
import databases
import os
from dbmonitor import *

# create app
app = Flask(__name__)

# home
@app.route('/')
def home():
    # get songs from queue
    songsInQueue = []
    try:
        for song in databases.SongInQueue.select().order_by(databases.SongInQueue.dateAdded):
            songsInQueue.append(song)
    except:
        print("Exception hit in home()")
        return render_template('home.html')

    return render_template('home.html', songs=songsInQueue)

@app.route('/add/', methods=['GET','POST'])
def add():
    if(request.method == 'GET'):
        return render_template('add.html')
    else:
        return addSongToQueue(request.form['link'])

@app.route('/history/')
def history():
    history = []
    try:
        for event in databases.History.select().order_by(databases.History.dateTimeFinish.desc()):
            history.append(event)
    except:
        print("Exception hit in history()")
        return render_template('history.html')


    return render_template('history.html', history=history)


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

        # get metadata and download song while we're at it
        metadata = ydl.extract_info(songLink, download=True)

        # convert the song from mp3 to wav for reasons
        AudioSegment.from_file('./music/'+metadata['id']).export('./music/'+metadata['id']+'.wav', format='wav')
        # AudioSegment.from_file('./music/'+metadata['id']).export('./music/'+'test'+'.wav', format='wav')

        # remove original
        os.remove('./music/'+metadata['id'])

        # given metadata, log to database
        databases.SongInQueue.addSongToQueue('./music/'+metadata['id']+'.wav', metadata['title'], songLink)

    except:
        return "failure"

    return "success"


# start server
if __name__ == "__main__":
    #drop and init tables
    databases.dropTables()
    databases.initTables()

    DBMonitor().start()

    app.debug = False
    app.run(threaded=False, port=3000, host='0.0.0.0')
