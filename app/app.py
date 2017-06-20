from __future__ import unicode_literals
from flask import Flask, request, render_template, Response, jsonify
from multiprocessing import Process, Value, Array
from dbmonitor import *
import databases
import datetime
import os
import logging
import ctypes
import constants
import song_utilities

logging.basicConfig(level=constants.LOG_LEVEL)

# create app
app = Flask(__name__)

musicIsPlaying = Value('d', -1)
songPlaying = Array(ctypes.c_char_p, constants.UUID_LENGTH)
skipSongRequest = Array(ctypes.c_char_p, constants.UUID_LENGTH)
arduinoPortLoc = Array(ctypes.c_char_p, constants.ARD_PORT_LENGTH)
arduinoBluePin = Array(ctypes.c_char_p, constants.ARD_PIN_LENGTH)
arduinoGreenPin = Array(ctypes.c_char_p, constants.ARD_PIN_LENGTH)
arduinoRedPin = Array(ctypes.c_char_p, constants.ARD_PIN_LENGTH)
latency = Value('d', 0)
autoPlayMusic = Value('d', 0)
songPlaying[:] = constants.EMPTY_UUID
skipSongRequest[:] = constants.EMPTY_UUID
monitor = None
monitorProc = None
logger = logging.getLogger(__name__)
# home

openConnections = []


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
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
            # do delete
            uuid = str(request.form['songID'])

            # verify the song isn't playing
            if ''.join(songPlaying) == uuid and musicIsPlaying.value == constants.PLAY:
                responseData[constants.RESPONSE] = constants.FAILURE
                responseData[constants.ERROR] = "Song can't be deleted, is currently playing"
            else:
                # delete from queue
                try:
                    songToDelete = databases.SongInQueue.select().where(databases.SongInQueue.uuid == uuid).get()
                    databases.ActionHistory.newRemoveSong(songToDelete.songTitle, uuid, songToDelete.songLink)

                    databases.SongInQueue.delete().where(databases.SongInQueue.uuid == uuid).execute()
                    databases.PreprocessRequest.delete().where(databases.PreprocessRequest.songUUID == uuid).execute()
                    responseData[constants.RESPONSE] = constants.SUCCESS
                except:
                    responseData[constants.RESPONSE] = constants.FAILURE
                    responseData[constants.ERROR] = "Failed to remove from database"
        elif command == constants.START_STOP:
            try:
                musicIsPlaying.value = (musicIsPlaying.value + 1) % 2
                responseData[constants.RESPONSE] = constants.SUCCESS
                databases.ActionHistory.newPlayStop()
            except:
                responseData[constants.RESPONSE] = constants.FAILURE
                responseData[constants.ERROR] = "Can't stop this beat"
        elif command == "next":
            uuid = str(request.form['songID'])

            # verify song is playing
            if ''.join(songPlaying) == uuid:
                # send next signal
                skipSongRequest[:] = uuid
                # add a new action event
            responseData[constants.RESPONSE] = constants.SUCCESS
        else:
            responseData[constants.RESPONSE] = constants.FAILURE
            responseData[constants.ERROR] = constants.UNKNOWN_COMMAND
        return jsonify(responseData)


@app.route('/add/', methods=['POST'])
def add():
    responseData = {}
    songUUID = str(song_utilities.addSongToQueue(request.form['link']))
    if songUUID == constants.FAILED_UUID_STR:
        responseData[constants.RESPONSE] = constants.FAILURE
        responseData["error"] = "Could not add to database"
    else:
        responseData[constants.RESPONSE] = constants.SUCCESS
        responseData["songID"] = songUUID
    return jsonify(responseData)


@app.route('/history/', methods=['GET', 'POST'])
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
                    newSongUUID = databases.SongInQueue.addSongToQueue(song.songPath, song.songTitle, song.songLink, song.songLength)
                    # needs to be reprocessed
                    databases.PreprocessRequest.newPreProcessRequest(song.songPath, str(newSongUUID))
                    #send update to client
                    databases.ActionHistory.newAddSong(song.songTitle, str(newSongUUID), song.songLink,  song.songLength)
                else:
                    newSongUUID = song_utilities.addSongToQueue(song.songLink)

                responseData[constants.RESPONSE] = constants.SUCCESS
                responseData["songID"] = str(newSongUUID)
            except:
                responseData[constants.RESPONSE] = constants.FAILURE
                responseData["error"] = "Failed to insert new request into database"
        else:
            responseData[constants.RESPONSE] = constants.FAILURE
            responseData["error"] = "Invalid song ID"
        return jsonify(responseData)


@app.route('/updater/')
def listener():
    minDT = datetime.datetime.now()
    curDT = minDT
    for conn in openConnections:
        if minDT > conn:
            minDT = conn

    if minDT != curDT:
        databases.ActionHistory.cleanup(minDT)

    def listenForSongIsFinished():
        entryDateTime = datetime.datetime.now()
        openConnections.append(entryDateTime)
        latestEvent = databases.ActionHistory.select().order_by(databases.ActionHistory.datetime.desc()).get().datetime

        try:
            while True:
                if databases.ActionHistory.select().where(databases.ActionHistory.datetime > datetime).wrapped_count > 0:
                    newEvents = databases.ActionHistory.select().where(databases.ActionHistory.datetime > latestEvent).order_by(databases.ActionHistory.datetime)
                    for ev in newEvents:
                        if ev.eventType == constants.ACT_HIST_ADD:
                            yield "data: NEWSONG\n\n"
                        elif ev.eventType == constants.ACT_HIST_REM:
                            yield "data: REMSONG\n\n"
                        elif ev.eventType == constants.ACT_HIST_NEXT:
                            yield "data: STARTUPDATE\n\n"
                        elif ev.eventType == constants.ACT_HIST_PLAY_STOP:
                            yield "data: PLAYSTOP\n\n"
                        else:
                            # unknown event type
                            continue
                        yield "data: newID: {}\n\n".format(ev.newID if ev.newID is not None else constants.EMPTY_UUID)
                        yield "data: newTitle: {}\n\n".format(ev.newTitle)
                        yield "data: newLink: {}\n\n".format(ev.newLink)
                        yield "data: newLength: {}\n\n".format(ev.newSongLength)
                        yield "data: oldID: {}\n\n".format(ev.oldID)
                        yield "data: oldLink: {}\n\n".format(ev.oldLink)
                        yield "data: oldTitle: {}\n\n".format(ev.oldTitle)
                        yield "data: currentlyPlaying: {}\n\n".format(musicIsPlaying.value)
                        if ev.eventType == constants.ACT_HIST_ADD:
                            yield "data: ENDSONG\n\n"
                        elif ev.eventType == constants.ACT_HIST_REM:
                            yield "data: ENDREM\n\n"
                        elif ev.eventType == constants.ACT_HIST_NEXT:
                            yield "data: ENDUPDATE\n\n"
                        elif ev.eventType == constants.ACT_HIST_PLAY_STOP:
                            yield "data: ENDPLAYSTOP\n\n"
                        latestEvent = ev.datetime

                else:
                    time.sleep(0.5)
        except:
            openConnections.remove(entryDateTime)
            return

    return Response(listenForSongIsFinished(), mimetype="text/event-stream")


@app.route("/settings/", methods=['GET', 'POST'])
def settings():
    if request.method == 'GET':
        responseData = {}
        responseData[constants.ARDUINO_BOARD] = ''.join(arduinoPortLoc[:])
        responseData[constants.ARDUINO_RED] = ''.join(arduinoRedPin[:])
        responseData[constants.ARDUINO_GREEN] = ''.join(arduinoGreenPin[:])
        responseData[constants.ARDUINO_BLUE] = ''.join(arduinoBluePin[:])
        responseData[constants.LATENCY] = str(latency.value)
        responseData[constants.AUTOPLAY] = str(autoPlayMusic.value)
        responseData[constants.RESPONSE] = constants.SUCCESS

    elif request.method == 'POST':
        def checkLength(checkString, checkLength):
            if len(checkString) > checkLength:
                return checkString[:checkLength]
            else:
                return checkString + ' ' * (checkLength - len(checkString))
        try:
            responseData = {}
            newBoardLocation = checkLength(request.form[constants.ARDUINO_BOARD], constants.ARD_PORT_LENGTH)
            newRedLocation = checkLength(request.form[constants.ARDUINO_RED], constants.ARD_PIN_LENGTH)
            newGreenLocation = checkLength(request.form[constants.ARDUINO_GREEN], constants.ARD_PIN_LENGTH)
            newBlueLocation = checkLength(request.form[constants.ARDUINO_BLUE], constants.ARD_PIN_LENGTH)
            newLatency = float(request.form[constants.LATENCY])
            new_autoplay = float(str(request.form[constants.AUTOPLAY]) == 'true')

            arduinoPortLoc[:] = newBoardLocation[:]
            arduinoRedPin[:] = newRedLocation[:]
            arduinoGreenPin[:] = newGreenLocation[:]
            arduinoBluePin[:] = newBlueLocation[:]
            latency.value = newLatency
            autoPlayMusic.value = new_autoplay

            responseData[constants.ARDUINO_BOARD] = newBoardLocation
            responseData[constants.ARDUINO_RED] = newRedLocation
            responseData[constants.ARDUINO_GREEN] = newGreenLocation
            responseData[constants.ARDUINO_BLUE] = newBlueLocation
            responseData[constants.LATENCY] = newLatency
            responseData[constants.AUTOPLAY] = new_autoplay
            responseData[constants.RESPONSE] = constants.SUCCESS
        except ValueError:
            # bad arguments for latency or autoplay
            responseData[constants.RESPONSE] = constants.FAILURE

    return jsonify(responseData)


def init_background_procs():
    global monitor, monitorProc
    monitor = DBMonitor(None, None, None, None, None, None, None, None, None, True)
    monitorProc = Process(target=monitor.run, args=(musicIsPlaying, songPlaying, skipSongRequest, arduinoPortLoc, arduinoBluePin, arduinoGreenPin, arduinoRedPin, latency, autoPlayMusic, False))
    monitorProc.start()


# start server
if __name__ == "__main__":
    # drop and init tables
    databases.dropTables()
    databases.initTables()

    init_background_procs()

    app.debug = constants.DEBUGMODE
    app.run(threaded=True, port=constants.PORT, host='0.0.0.0', use_reloader=False)
