# dbmonitor.py
from multiprocessing import Value
import time
from serial import SerialException
import math as m
import pyfirmata as pf
import pygame as pg
import preprocessor
import logging
import soundfile
import constants
import databases
import song_utilities

logging.basicConfig(level=constants.LOG_LEVEL)
logger = logging.getLogger(__name__)


class DBMonitor:
    def __init__(self, musicIsPlayingValue, songPlayingValue, skipSongRequest, port, blue, green, red, latencyVal, auto_play, threadIssue):
        # I like the idea of encapsulation for all these functions and variables
        # but when the object is instantiated in the main thread, it instantiates
        # an object before the run() function is called in its new process
        # (by multiprocessing.Process). To prevent creating redundant connections
        # (or even dual spawning threads), this variable prevents the object
        # from instantiating. Note that the run() function also calls __init__()
        if threadIssue:
            return

        self.songPlaying = songPlayingValue         # multiprocessing.Array object
        self.musicIsPlaying = musicIsPlayingValue      # multiprocessing.Value object
        self.skipSong = skipSongRequest
        self.board = None
        self.redPin = None
        self.greenPin = None
        self.bluePin = None
        self.boardLoc = port
        self.redLoc = red
        self.greenLoc = green
        self.blueLoc = blue
        self.latency = latencyVal
        self.autoplay_music = auto_play
        self.song_position = constants.SONG_BEGINNING_TIME

        self.preprocessor = preprocessor.SongPreprocessor()
        self.preprocessor.start()

        defaultPorts = [constants.ARDUINO_WINDOWS_LOC_DEFAULT, constants.ARDUINO_OSX_LOC_DEFAULT, constants.ARDUINO_UBUNTU_LOC_DEFAULT]

        for defaultPort in defaultPorts:
            try:
                self.boardLoc[:] = defaultPort + ' ' * (constants.ARD_PORT_LENGTH - len(defaultPort))
                self.redLoc[:] = constants.ARDUINO_DEFAULT_RED_PIN + ' ' * (constants.ARD_PIN_LENGTH - len(constants.ARDUINO_DEFAULT_RED_PIN))
                self.greenLoc[:] = constants.ARDUINO_DEFAULT_GREEN_PIN + ' ' * (constants.ARD_PIN_LENGTH - len(constants.ARDUINO_DEFAULT_GREEN_PIN))
                self.blueLoc[:] = constants.ARDUINO_DEFAULT_BLUE_PIN + ' ' * (constants.ARD_PIN_LENGTH - len(constants.ARDUINO_DEFAULT_BLUE_PIN))
                self.initBoard()
                logger.info('Board initialized')

                break
            except SerialException:
                pass
        else:
            logger.info('Failed to initialize board')
            self.board = None
            self.boardLoc[:] = constants.BOARD_UNINITIALIZED
            self.redLoc[:] = constants.PIN_UNINITIALIZED
            self.greenLoc[:] = constants.PIN_UNINITIALIZED
            self.blueLoc[:] = constants.PIN_UNINITIALIZED

        self.musicIsPlaying.value = 1.0

        logger.info("DBMonitor initialized")

    def run(self, musicIsPlayingMultiProcVal, songIsPlayingMultiProcVal, skipSongRequestArr, portProcArr, blueProcArr, greenProcArr, redProcArr, latencyProcVal, auto_play_val, threadIssue):
        logger.info("Running DBMonitor")
        self.__init__(musicIsPlayingMultiProcVal, songIsPlayingMultiProcVal, skipSongRequestArr, portProcArr, blueProcArr, greenProcArr, redProcArr, latencyProcVal, auto_play_val, threadIssue)
        instanceRed = ''.join(self.redLoc[:])
        instanceGreen = ''.join(self.greenLoc[:])
        instanceBlue = ''.join(self.blueLoc[:])
        instanceBoard = ''.join(self.boardLoc[:])

        oldSongTitle = constants.EMPTY_INPUT
        oldSongLink = constants.EMPTY_INPUT
        last_song_played = None
        while True:
            while self.musicIsPlaying.value == constants.PLAY and databases.SongInQueue.select().wrapped_count() > 0:
                if(instanceRed != ''.join(self.redLoc) or instanceBlue != ''.join(self.blueLoc) or
                instanceGreen != ''.join(self.greenLoc) or instanceBoard != ''.join(self.boardLoc)):
                    try:
                        instanceRed = ''.join(self.redLoc[:])
                        instanceGreen = ''.join(self.greenLoc[:])
                        instanceBlue = ''.join(self.blueLoc[:])
                        instanceBoard = ''.join(self.boardLoc[:])
                        self.initBoard()
                    except SerialException:
                        self.board = None

                song = databases.SongInQueue.select().order_by(databases.SongInQueue.dateAdded).get()
                if ''.join(self.songPlaying[:]) != str(song.uuid) and oldSongTitle != constants.EMPTY_INPUT and oldSongLink != constants.EMPTY_INPUT:
                    databases.ActionHistory.newNextSong(song.songTitle, str(song.uuid), song.songLink, song.songLength, oldSongTitle, ''.join(self.songPlaying[:]), oldSongLink)

                self.songPlaying[:] = str(song.uuid)
                oldSongTitle = song.songTitle
                oldSongLink = song.songLink
                last_song_played = song.songLink

                self.playSong(song.songPath, ''.join(self.songPlaying[:]))

                if self.musicIsPlaying.value == constants.PLAY:
                    # add to History
                    databases.History.addSongToHistory(song.songTitle, song.songLink, song.songPath, song.songLength)

                    # remove song from queue
                    databases.SongInQueue.delete().where(databases.SongInQueue.uuid == song.uuid).execute()

            if oldSongTitle != constants.EMPTY_INPUT and oldSongLink != constants.EMPTY_INPUT and self.musicIsPlaying.value == constants.PLAY:
                databases.ActionHistory.newNextSong(constants.EMPTY_INPUT, None, constants.EMPTY_INPUT, None, oldSongTitle, ''.join(self.songPlaying[:]), oldSongLink)
                oldSongTitle = constants.EMPTY_INPUT
                oldSongLink = constants.EMPTY_INPUT
                self.songPlaying[:] = constants.EMPTY_UUID

            if self.autoplay_music.value == 1.0 and last_song_played is not None:
                # autoplay music
                new_song_link = song_utilities.get_related_video_url(last_song_played)
                song_utilities.addSongToQueue(new_song_link)
            else:
                if self.board is not None:
                    self.standbyMode()
                else:
                    time.sleep(0.2)

    def playSong(self, song, songUUID):
        logger.info("Received song request")

        procID = constants.FAILED_UUID_STR
        # dont preprocess song if it's already preprocessed
        if(songUUID not in self.preprocessor.lovals.keys() or
        songUUID not in self.preprocessor.mdvals.keys() or
        songUUID not in self.preprocessor.hivals.keys()):
            # second thread to preprocess the song
            procID = databases.PreprocessRequest.newPreProcessRequest(song, songUUID)

        # wait for the preprocessor to finish the song
        while databases.PreprocessRequest.hasntBeenProcessed(procID):
            time.sleep(0.3)

        loval = self.preprocessor.lovals[songUUID]
        mdval = self.preprocessor.mdvals[songUUID]
        hival = self.preprocessor.hivals[songUUID]

        logger.info("Finished analysis, playing song")
        _, frame_rate = soundfile.read(song)
        # Play audio and sync up light values
        pg.mixer.init(frequency=frame_rate)
        pg.mixer.music.load(song)
        pg.mixer.music.play(0, self.song_position / 1000.0)

        while pg.mixer.music.get_busy() == constants.PLAY and self.musicIsPlaying.value == constants.PLAY:
            # check for skip
            if self.skipSong[0] != ' ':
                # skip song requested verify it's this song
                if ''.join(self.skipSong[:]) == ''.join(self.songPlaying[:]):
                    pg.mixer.music.stop()       # turn off music
                    self.skipSong[:] = constants.EMPTY_UUID # clear song to skip
                    break                       # exit loop
                else:
                    self.skipSong[:] = constants.EMPTY_UUID

            self.song_position = pg.mixer.music.get_pos()
            if self.board is not None:
                try:
                    pos = self.song_position
                    self.redPin.write(loval[int((pos - self.latency.value)/constants.WINDOW_SIZE_SEC)])
                    self.greenPin.write(mdval[int((pos - self.latency.value)/constants.WINDOW_SIZE_SEC)])
                    self.bluePin.write(hival[int((pos - self.latency.value)/constants.WINDOW_SIZE_SEC)])
                except IndexError:
                    logger.info('Don\'t go places you don\'t belong')
            else:
                time.sleep(0.1)
        if self.musicIsPlaying.value == constants.STOP:
            # music could've been stopped while song still playing, stop mixer
            pg.mixer.music.stop()
        else:
            # music stopped naturally, remove the preprocessing
            databases.PreprocessRequest.newDecomissionRequest(songUUID)
            self.song_position = 0

        if self.board is not None:
            self.redPin.write(0)
            self.greenPin.write(0)
            self.bluePin.write(0)
        pg.mixer.quit()

    def standbyMode(self):
        logger.info('Standby Mode')
        cycles = 20
        while self.autoplay_music != 1.0 and (databases.SongInQueue.select().wrapped_count() == 0 or self.musicIsPlaying.value == constants.STOP):
            if cycles < 20:
                # sine wave
                for i in range(0, 314, 2):
                    writeVal = m.sin(i/100.0)/2.0
                    self.writeToPinsAndSleep(writeVal, writeVal, writeVal, 0.025)
                    # end up for
            elif cycles < 40:
                # heartbeat
                for i in range(0, 120, 2):
                    writeVal = m.sin(i/100.0)/3.0+.01
                    self.writeToPinsAndSleep(None, None, writeVal, 0.025)
                # beat
                self.writeToPinsAndSleep(0.3, None, writeVal, 0.04)
                self.writeToPinsAndSleep(0.0, None, writeVal, 0.5)
                self.writeToPinsAndSleep(0.3, None, writeVal, 0.04)
                self.writeToPinsAndSleep(0.0, None, writeVal, 0.5)

                for i in range(120, 0, -2):
                    writeVal = m.sin(i/100.0)/3.0+.01
                    self.writeToPinsAndSleep(None, None, writeVal, 0.025)

            elif cycles < 60:
                # color wheel
                # red
                self.colorwheel(False, True, True)
                # green/red
                self.colorwheel(False, False, True)
                # green
                self.colorwheel(True, False, True)
                # green/blue
                self.colorwheel(True, False, False)
                # blue
                self.colorwheel(True, True, False)
                # blue/red
                self.colorwheel(False, True, False)
            cycles = (cycles + 1) % 60

    def colorwheel(self, red, green, blue):
        maxval = 260
        d = 2.0
        s = .01
        for i in range(260, 368, 1):
            iter_red = i if red else maxval
            iter_green = i if green else maxval
            iter_blue = i if blue else maxval

            self.writeToPinsAndSleep(abs(m.sin(iter_red/100.0))/d+s, abs(m.sin(iter_green/100.0))/d+s, abs(m.sin(iter_blue/100.0))/d+s, 0.03)

    def writeToPinsAndSleep(self, pin1, pin2, pin3, sleepTime):
        if pin1 is not None:
            self.redPin.write(pin1)
        if pin2 is not None:
            self.greenPin.write(pin2)
        if pin3 is not None:
            self.bluePin.write(pin3)
        if sleepTime is not None:
            time.sleep(sleepTime)

    def initBoard(self):
        self.board = pf.Arduino(''.join(self.boardLoc[:]).strip())             # init board
        self.redPin = self.board.get_pin(''.join(self.redLoc[:]).strip())      # R
        self.greenPin = self.board.get_pin(''.join(self.greenLoc[:]).strip())  # G
        self.bluePin = self.board.get_pin(''.join(self.blueLoc[:]).strip())    # B
