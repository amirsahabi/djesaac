from __future__ import unicode_literals
from flask import Flask, request, render_template
import youtube_dl
import databases

# create app
app = Flask(__name__)

# home
@app.route('/')
def home():

    # get songs from queue
    songsInQueue = []
    try:
        for song in databases.SongInQueue.select().order_by(databases.SongInQueue.dateAdded.desc()):
            songsInQueue.append(song)
    except:
        print("Exception hit")
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
    # TODO: add history functionality
    return render_template('history.html')


def addSongToQueue(songLink):
    try:
        # given songlink, use youtubedl to download it
        # set options
        dlOptions = {
            'format': 'bestaudio/best',
            'extractaudio' : True,
            'audioformat' : 'mp3',
            'outtmpl' : 'music/%(id)s',
            'noplaylist' : True,
        }

        # create youtubedl object
        ydl = youtube_dl.YoutubeDL(dlOptions)

        # get metadata and download song while we're at it
        metadata = ydl.extract_info(songLink, download=True)

        # given metadata, log to database
        databases.SongInQueue.addSongToQueue('./music/'+metadata['id'], metadata['title'], songLink)

    except:
        return "failure"

    return "success"


# start server
if __name__ == "__main__":
    #drop and init tables
    databases.dropTables()
    databases.initTables()

    app.debug = True
    app.run(threaded=True, port=3000, host='0.0.0.0')
