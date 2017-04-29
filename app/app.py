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
import constants

logging.basicConfig(level=constants.LOG_LEVEL)

# create app
app = Flask(__name__)

musicIsPlaying      = Value('d' , 1)
songPlaying         = Array(ctypes.c_char_p, constants.UUID_LENGTH)
skipSongRequest     = Array(ctypes.c_char_p, constants.UUID_LENGTH)
arduinoPortLoc      = Array(ctypes.c_char_p, constants.ARD_PORT_LENGTH)
arduinoBluePin      = Array(ctypes.c_char_p, constants.ARD_PIN_LENGTH)
arduinoGreenPin     = Array(ctypes.c_char_p, constants.ARD_PIN_LENGTH)
arduinoRedPin       = Array(ctypes.c_char_p, constants.ARD_PIN_LENGTH)
latency             = Value('d', 0)
songPlaying[:]      = constants.EMPTY_UUID
skipSongRequest[:]  = constants.EMPTY_UUID
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

        return render_template('home.html', songs=songsInQueue, musicIsPlaying=musicIsPlaying.value == constants.PLAY)
    else:
        responseData = {}
        command = request.form['command']
        if command == "remove":
            #do delete
            uuid = str(request.form['songID'])

            #verify the song isn't playing
            if ''.join(songPlaying) == uuid and musicIsPlaying.value == constants.PLAY:
                responseData[constants.RESPONSE] = constants.FAILURE
                responseData[constants.ERROR]    = "Song can't be deleted, is currently playing"
            else:
                #delete from queue
                try:
                    databases.SongInQueue.delete().where(databases.SongInQueue.uuid == uuid).execute()
                    databases.PreprocessRequest.delete().where(databases.PreprocessRequest.songUUID == uuid).execute()
                    responseData[constants.RESPONSE] = constants.SUCCESS
                except:
                    responseData[constants.RESPONSE] = constants.FAILURE
                    responseData[constants.ERROR]    = "Failed to remove from database"
        elif command == "startstop":
            try:
                musicIsPlaying.value = (musicIsPlaying.value + 1) % 2
                responseData[constants.RESPONSE] = constants.SUCCESS
            except:
                responseData[constants.RESPONSE] = constants.FAILURE
                responseData[constants.ERROR]    = "Can't stop this beat"
        elif command == "next":
            uuid = str(request.form['songID'])

            # verify song is playing
            if ''.join(songPlaying) == uuid:
                # send next signal
                skipSongRequest[:] = uuid
            responseData[constants.RESPONSE] = constants.SUCCESS
        else:
            responseData[constants.RESPONSE] = constants.FAILURE
            responseData[constants.ERROR]    = "unknown command"
        return jsonify(responseData)


@app.route('/add/', methods=['POST'])
def add():
    responseData = {}
    songUUID = str(addSongToQueue(request.form['link']))
    if songUUID == constants.FAILED_UUID_STR:
        responseData[constants.RESPONSE]    = constants.FAILURE
        responseData["error"]       = "Could not add to database"
    else:
        responseData[constants.RESPONSE]    = constants.SUCCESS
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
        newSongUUID = constants.FAILED_UUID_STR
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
                responseData[constants.RESPONSE] = constants.SUCCESS
                responseData["songID"]   = str(newSongUUID)
            except:
                responseData[constants.RESPONSE] = constants.FAILURE
                responseData["error"]    = "Failed to insert new request into database"
        else:
            responseData[constants.RESPONSE] = constants.FAILURE
            responseData["error"]    = "Invalid song ID"
        return jsonify(responseData)

@app.route('/updater/')
def listener():
    def listenForSongIsFinished():
        flaskThreadSongPlaying      = str(''.join(songPlaying))
        flaskThreadSongObject       = databases.SongInQueue.select().where(databases.SongInQueue.uuid == flaskThreadSongPlaying).get() if flaskThreadSongPlaying != constants.EMPTY_UUID else None
        flaskThreadSongPlayingTitle = str(flaskThreadSongObject.songTitle) if flaskThreadSongPlaying != constants.EMPTY_UUID else ''
        flaskThreadSongPlayingLink  = str(flaskThreadSongObject.songLink)  if flaskThreadSongPlaying != constants.EMPTY_UUID else ''
        while True:
            if(databases.SongInQueue.select().wrapped_count() > 0):
                # check to see if previous song is current song
                if(flaskThreadSongPlaying != ''.join(songPlaying)):
                    # get new variables
                    newSongID       = str(''.join(songPlaying))
                    newSongObject   = databases.SongInQueue.select().where(databases.SongInQueue.uuid == newSongID).get()
                    newSongTitle    = str(newSongObject.songTitle)
                    newSongLink     = str(newSongObject.songLink)

                    #song playing has changed, send data request
                    # there's got to be a cleaner way to do this
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
            elif(flaskThreadSongPlaying != constants.EMPTY_UUID):
                # no more songs playing but the last one finished, send an event
                newSongID = constants.EMPTY_UUID
                newSongObject = None
                newSongTitle = ''
                newSongLink = ''

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

@app.route("/settings/", methods=['GET','POST'])
def settings():
    if request.method == 'GET':
        responseData = {}
        responseData['board']   = ''.join(boardLoc)
        responseData['red']     = ''.join(redLoc)
        responseData['green']   = ''.join(greenLoc)
        responseData['blue']    = ''.join(blueLoc)
        responseData['latency'] = str(latency.value)
        responseData[constants.RESPONSE] = constants.SUCCESS

    elif request.method == 'POST':
        responseData = {}
        newBoardLocation = request.form['board']
        newRedLocation   = request.form['red']
        newGreenLocation = request.form['green']
        newBlueLocation  = request.form['blue']
        newLatency       = request.form['latency']

        # adjust lengths
        if(len(newBoardLocation) > constants.ARD_PORT_LENGTH):
            newBoardLocation = newBoardLocation[:constants.ARD_PORT_LENGTH]
        else:
            newBoardLocation = newBoardLocation + ' ' * (constants.ARD_PORT_LENGTH - len(newBoardLocation))
        if(len(newRedLocation) > constants.ARD_PIN_LENGTH):
            newRedLocation = newRedLocation[:constants.ARD_PIN_LENGTH]
        else:
            newRedLocation = newRedLocation + ' ' * (constants.ARD_PIN_LENGTH - len(newRedLocation))
        if(len(newGreenLocation) > constants.ARD_PIN_LENGTH):
            newGreenLocation = newGreenLocation[:constants.ARD_PIN_LENGTH]
        else:
            newGreenLocation = newGreenLocation + ' ' * (constants.ARD_PIN_LENGTH - len(newGreenLocation))
        if(len(newBlueLocation) > constants.ARD_PIN_LENGTH):
            newBlueLocation = newBlueLocation[:constants.ARD_PIN_LENGTH]
        else:
            newBlueLocation = newBlueLocation + ' ' * (constants.ARD_PIN_LENGTH - len(newBlueLocation))

        boardLoc[:]   = newBoardLocation[:]
        redLoc[:]     = newRedLocation[:]
        greenLoc[:]   = newGreenLocation[:]
        blueLoc[:]    = newBlueLocation[:]
        latency.value = float(newLatency)

        responseData['board']   = newBoardLocation
        responseData['red']     = newRedLocation
        responseData['green']   = newGreenLocation
        responseData['blue']    = newBlueLocation
        responseData['latency'] = newLatency
        responseData[constants.RESPONSE] = constants.SUCCESS

    return jsonify(responseData)

def addSongToQueue(songLink):
    songUUID = constants.FAILED_UUID_STR
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

        if songUUID != constants.FAILED_UUID_STR:
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
    databases.dropTables()
    databases.initTables()

    monitor = DBMonitor(None, None, None, None, None, None, None, None, True)
    monitorProc = Process(target=monitor.run, args=(musicIsPlaying, songPlaying, skipSongRequest, arduinoPortLoc, arduinoBluePin, arduinoGreenPin, arduinoRedPin, latency, False))
    monitorProc.start()

    app.debug = constants.DEBUGMODE
    app.run(threaded=True, port=constants.PORT, host='0.0.0.0', use_reloader=False)
