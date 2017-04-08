from __future__ import unicode_literals
from flask import Flask, request, render_template, Response, jsonify
from pydub import AudioSegment
from multiprocessing import Process, Value, Array
from dbmonitor import *
import youtube_dl
import databases
import os
import logging
import ctypes

logging.basicConfig(level=logging.INFO)

# create app
app = Flask(__name__)

musicIsPlaying  = Value('d' , 1)
songPlaying     = Array(ctypes.c_char_p, 36)
skipSongRequest = Array(ctypes.c_char_p, 36)
songPlaying[:]      = " " * 36
skipSongRequest[:]  = " " * 36
monitor = None
logger = logging.getLogger(__name__)
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
            logger.info("Exception hit in home()")
            return render_template('home.html')

        return render_template('home.html', songs=songsInQueue, musicIsPlaying=musicIsPlaying.value == 1)
    else:
        responseData = {}
        command = request.form['command']
        if command == "remove":
            #do delete
            uuid = str(request.form['songID'])

            #verify the song isn't playing
            if ''.join(songPlaying) == uuid and musicIsPlaying.value == 1:
                responseData["response"] = "failure"
                responseData["error"]    = "Song can't be deleted, is currently playing"
            else:
                #delete from queue
                try:
                    databases.SongInQueue.delete().where(databases.SongInQueue.uuid == uuid).execute()
                    databases.PreprocessRequest.delete().where(databases.PreprocessRequest.songUUID == uuid).execute()
                    responseData["response"] = "success"
                except:
                    responseData["response"] = "failure"
                    responseData["error"]    = "Failed to remove from database"
        elif command == "startstop":
            try:
                musicIsPlaying.value = (musicIsPlaying.value + 1) % 2
                responseData["response"] = "success"
            except:
                responseData["response"] = "failure"
                responseData["error"]    = "Can't stop this beat"
        elif command == "next":
            uuid = str(request.form['songID'])

            # verify song is playing
            if ''.join(songPlaying) == uuid:
                # send next signal
                skipSongRequest[:] = uuid
            responseData["response"] = "success"
        else:
            responseData["response"] = "failure"
            responseData["error"]    = "unknown command"
        return jsonify(responseData)


@app.route('/add/', methods=['POST'])
def add():
    responseData = {}
    songUUID = str(addSongToQueue(request.form['link']))
    if songUUID == "-1":
        responseData["response"]    = "failure"
        responseData["error"]       = "Could not add to database"
    else:
        responseData["response"]    = "success"
        responseData["songID"]      = songUUID
    return jsonify(responseData)

@app.route('/history/', methods=['GET','POST'])
def history():
    if request.method == 'GET':
        history = []
        try:
            for event in databases.History.select().order_by(databases.History.dateTimeFinish.desc()):
                history.append(event)
        except:
            logger.info("Exception hit in history()")
            return render_template('history.html')


        return render_template('history.html', history=history)
    else:
        responseData = {}
        songID = request.form['song']
        newSongUUID = "-1"
        if songID != '':
            # check if it's cached
            try:
                song = databases.History.select().where(databases.History.uuid == songID).get()
                if os.path.isfile(song.songPath):
                    # file already downloaded, just
                    newSongUUID = databases.SongInQueue.addSongToQueue(song.songPath, song.songTitle, song.songLink)
                    # needs to be reprocessed
                    databases.PreprocessRequest.newPreProcessRequest(song.songPath, str(newSongUUID))
                else:
                    newSongUUID = addSongToQueue(song.songLink)
                responseData["response"] = "success"
                responseData["songID"]   = str(newSongUUID)
            except:
                responseData["response"] = "failure"
                responseData["error"]    = "Failed to insert new request into database"
        else:
            responseData["response"] = "failure"
            responseData["error"]    = "Invalid song ID"
        return jsonify(responseData)

@app.route('/updater/')
def listener():
    def listenForSongIsFinished():
        flaskThreadSongPlaying      = str(''.join(songPlaying))
        flaskThreadSongObject       = databases.SongInQueue.select().where(databases.SongInQueue.uuid == flaskThreadSongPlaying).get() if flaskThreadSongPlaying != ' ' * 36 else None
        flaskThreadSongPlayingTitle = str(flaskThreadSongObject.songTitle) if flaskThreadSongPlaying != ' ' * 36 else ''
        flaskThreadSongPlayingLink  = str(flaskThreadSongObject.songLink)  if flaskThreadSongPlaying != ' ' * 36 else ''
        while True:
            if(databases.SongInQueue.select().wrapped_count() > 0):
                # check to see if previous song is current song
                if(flaskThreadSongPlaying != ''.join(songPlaying)):
                    # get new variables
                    newSongID       = str(''.join(songPlaying))
                    newSongObject   = databases.SongInQueue.select().where(databases.SongInQueue.uuid == newSongID).get()
                    newSongTitle    = str(newSongObject.songTitle)
                    newSongLink     = str(newSongObject.songLink)

                    # create response
                    # responseString =     ("data: response: newsong,"
                    #                         "oldID: {},newID: {},"
                    #                         "oldTitle: {},newTitle: {},"
                    #                         "oldLink: {},newLink: {}\n\n").format(       \
                    #                         flaskThreadSongPlaying, newSongID,          \
                    #                         flaskThreadSongPlayingTitle, newSongTitle,  \
                    #                         flaskThreadSongPlayingLink, newSongLink     \
                    #                         )

                    #song playing has changed, send data request
                    # yield responseString
                    yield "data: STARTUPDATE\n\n"
                    yield "data: oldID: {}\n\n".format(flaskThreadSongPlaying)
                    yield "data: newID: {}\n\n".format(newSongID)
                    yield "data: oldTitle: {}\n\n".format(flaskThreadSongPlayingTitle)
                    yield "data: newTitle: {}\n\n".format(newSongTitle)
                    yield "data: oldLink: {}\n\n".format(flaskThreadSongPlayingLink)
                    yield "data: newLink: {}\n\n".format(newSongLink)
                    yield "data: ENDUPDATE\n\n"
                    # transition listening to data to new data
                    flaskThreadSongPlaying      = newSongID
                    flaskThreadSongObject       = newSongObject
                    flaskThreadSongPlayingTitle = newSongTitle
                    flaskThreadSongPlayingLink  = newSongLink
            elif(flaskThreadSongPlaying != ' ' * 36):
                # no more songs playing but the last one finished, send an event
                newSongID = ' ' * 36
                newSongObject = None
                newSongTitle = ''
                newSongLink = ''

                # responseString =     "data: response: newsong,\
                #                         oldID: {},newID: {},\
                #                         oldTitle: {},newTitle: {},\
                #                         oldLink: {},newLink: {}\n\n".format(       \
                #                         flaskThreadSongPlaying, newSongID,          \
                #                         flaskThreadSongPlayingTitle, newSongTitle,  \
                #                         flaskThreadSongPlayingLink, newSongLink     \
                #                         )
                yield "data: STARTUPDATE\n\n"
                yield "data: oldID: {}\n\n".format(flaskThreadSongPlaying)
                yield "data: newID: {}\n\n".format(newSongID)
                yield "data: oldTitle: {}\n\n".format(flaskThreadSongPlayingTitle)
                yield "data: newTitle: {}\n\n".format(newSongTitle)
                yield "data: oldLink: {}\n\n".format(flaskThreadSongPlayingLink)
                yield "data: newLink: {}\n\n".format(newSongLink)
                yield "data: ENDUPDATE\n\n"

                flaskThreadSongPlaying = newSongID
                flaskThreadSongObject  = newSongObject
                flaskThreadSongPlayingTitle = newSongTitle
                flaskThreadSongPlayingLink  = newSongLink
            time.sleep(0.5)

    return Response(listenForSongIsFinished(), mimetype="text/event-stream")

def addSongToQueue(songLink):
    songUUID = "-1"
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
            logger.info("Song existed, no need to redownload")

            metadata = ydl.extract_info(songLink, download=False)

        # given metadata, log to database
        songUUID = str(databases.SongInQueue.addSongToQueue('./music/'+metadata['id']+'.wav', metadata['title'], songLink))

        if songUUID != "-1":
            # tell the preprocessor in the dbmonitor to preprocess it
            databases.PreprocessRequest.newPreProcessRequest('./music/'+metadata['id']+'.wav', songUUID)
        else:
            return songUUID

    except:
        return songUUID

    return songUUID
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

    monitor = DBMonitor(musicIsPlaying, songPlaying, skipSongRequest, True)
    monitorProc = Process(target=monitor.run, args=(musicIsPlaying, songPlaying, skipSongRequest, False))
    monitorProc.start()

    app.debug = True
    app.run(threaded=True, port=3000, host='0.0.0.0', use_reloader=False)
