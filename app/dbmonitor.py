# dbmonitor.py
from scipy.io import wavfile as wf
from multiprocessing import Value
import time
import numpy as np
import math as m
import pyfirmata as pf
import pygame as pg
import wave
import preprocessor
import logging
import os
import constants
import databases

logging.basicConfig(level=constants.LOG_LEVEL)
logger = logging.getLogger(__name__)

class DBMonitor:
    def __init__(self, musicIsPlayingValue, songPlayingValue, skipSongRequest, port, blue, green, red, latencyVal, threadIssue):
        # I like the idea of encapsulation for all these functions and variables
        # but when the object is instantiated in the main thread, it instantiates
        # an object before the run() function is called in its new process
        # (by multiprocessing.Process). To prevent creating redundant connections
        # (or even dual spawning threads), this variable prevents the object
        # from instantiating. Note that the run() function also calls __init__()
        if threadIssue:
            return

        self.songPlaying    = songPlayingValue         # multiprocessing.Array object
        self.musicIsPlaying = musicIsPlayingValue      # multiprocessing.Value object
        self.skipSong       = skipSongRequest
        self.board          = None
        self.redPin         = None
        self.greenPin       = None
        self.bluePin        = None
        self.boardLoc       = port
        self.redLoc         = red
        self.greenLoc       = green
        self.blueLoc        = blue
        self.latency        = latencyVal

        self.preprocessor = preprocessor.SongPreprocessor()
        self.preprocessor.start()

        defaultPorts = [constants.ARDUINO_WINDOWS_LOC_DEFAULT, constants.ARDUINO_OSX_LOC_DEFAULT, constants.ARDUINO_UBUNTU_LOC_DEFAULT]

        for defaultPort in defaultPorts:
            try:
                self.boardLoc[:] = defaultPort + ' ' * len(defaultPort)
                self.blueLoc[:]  = constants.ARDUINO_DEFAULT_RED_PIN   + ' ' * (constants.ARD_PIN_LENGTH - len(constants.ARDUINO_DEFAULT_RED_PIN))
                self.greenLoc[:] = constants.ARDUINO_DEFAULT_GREEN_PIN + ' ' * (constants.ARD_PIN_LENGTH - len(constants.ARDUINO_DEFAULT_GREEN_PIN))
                self.redLoc[:]   = constatns.ARDUINO_DEFAULT_BLUE_PIN  + ' ' * (constants.ARD_PIN_LENGTH - len(constants.ARDUINO_DEFAULT_BLUE_PIN))
                self.initBoard(defaultPort)
                logger.info('Board initialized')

                break
            except:
                pass
        else:
            self.board = None
            self.boardLoc[:] = constants.BOARD_UNINITIALIZED
            self.redLoc[:]   = constants.PIN_UNINITIALIZED
            self.greenLoc[:] = constants.PIN_UNINITIALIZED
            self.blueLoc[:]  = constants.PIN_UNINITIALIZED

        # Initialize board and set pins using pyfirmata
        try:
            self.initBoard(constants.ARDUINO_WINDOWS_LOC_DEFAULT, constants.ARDUINO_PIN1, constants.ARDUINO_PIN2, constants.ARDUINO_PIN3)
            logger.info("Board initialized")
        except:
            # failed for windows, try mac
            try:
                self.initBoard(constants.ARDUINO_OSX_LOC_DEFAULT, constants.ARDUINO_PIN1, constants.ARDUINO_PIN2, constants.ARDUINO_PIN3)
                logger.info("Board initialized")
            except:
                try:
                    # failed for mac, try ubuntu
                    self.initBoard(constants.ARDUINO_UBUNTU_LOC_DEFAULT, constants.ARDUINO_PIN1, constants.ARDUINO_PIN2, constants.ARDUINO_PIN3)
                    logger.info('Board initialized')
                except:
                    self.board = None
                    logger.info("Failed to initialize board, will only play music")
        logger.info("DBMonitor initialized")

    def run(self, musicIsPlayingMultiProcVal, songIsPlayingMultiProcVal, skipSongRequestArr, portProcArr, blueProcArr, greenProcArr, redProcArr, latencyProcVal, threadIssue):
        logger.info("Running DBMonitor")
        self.__init__(musicIsPlayingMultiProcVal, songIsPlayingMultiProcVal, skipSongRequestArr, portProcArr, blueProcArr, greenProcArr, redProcArr, latencyProcVal, threadIssue)

        while(True):
            instanceRed   = ''.join(self.redLoc[:])
            instanceGreen = ''.join(self.greenLoc[:])
            instanceBlue  = ''.join(self.blueLoc[:])
            instanceBoard = ''.join(self.boardLoc[:])

            oldSongTitle = constants.EMPTY_INPUT
            oldSongLink  = constants.EMPTY_INPUT
            while(self.musicIsPlaying.value == constants.PLAY and databases.SongInQueue.select().wrapped_count() > 0):
                if( instanceRed != ''.join(self.redLoc) or instanceBlue != ''.join(self.blueLoc) or
                    instanceGreen != ''.join(self.greenLoc) or instanceBoard != ''.join(self.boardLoc)):
                    try:
                        instanceRed   = ''.join(self.redLoc[:])
                        instanceGreen = ''.join(self.greenLoc[:])
                        instanceBlue  = ''.join(self.blueLoc[:])
                        instanceBoard = ''.join(self.boardLoc[:])
                        self.initBoard()
                    except:
                        self.board = None

                song = databases.SongInQueue.select().order_by(databases.SongInQueue.dateAdded).get()
                if(''.join(self.songPlaying[:]) != str(song.uuid) and oldSongTitle != constants.EMPTY_INPUT and oldSongLink != constants.EMPTY_INPUT):
                    databases.ActionHistory.newNextSong(song.songTitle, str(song.uuid), song.songLink, oldSongTitle, ''.join(self.songPlaying[:]), oldSongLink)

                self.songPlaying[:] = str(song.uuid)
                oldSongTitle = song.songTitle
                oldSongLink  = song.songLink

                self.playSong(song.songPath, ''.join(self.songPlaying[:]))

                if self.musicIsPlaying.value == constants.PLAY:
                    # add to History
                    databases.History.addSongToHistory(song.songTitle, song.songLink, song.songPath)

                    # remove song from queue
                    databases.SongInQueue.delete().where(databases.SongInQueue.uuid == song.uuid).execute()

            if(oldSongTitle != constants.EMPTY_INPUT and oldSongLink != constants.EMPTY_INPUT and self.musicIsPlaying.value == constants.PLAY):
                databases.ActionHistory.newNextSong(constants.EMPTY_INPUT, None, constants.EMPTY_INPUT, oldSongTitle, ''.join(self.songPlaying[:]), oldSongLink)
                oldSongTitle = constants.EMPTY_INPUT
                oldSongLink  = constants.EMPTY_INPUT
                self.songPlaying[:] = constants.EMPTY_UUID

            if self.board is not None:
                self.standbyMode()
            else:
                time.sleep(3)

    def playSong(self, song, songUUID):
        logger.info("Received song request")

        procID = constants.FAILED_UUID_STR
        #dont preprocess song if it's already preprocessed
        if(songUUID not in self.preprocessor.lovals.keys() or
            songUUID not in self.preprocessor.mdvals.keys() or
            songUUID not in self.preprocessor.hivals.keys()):
            # second thread to preprocess the song
            procID = databases.PreprocessRequest.newPreProcessRequest(song, songUUID)

        # wait for the preprocessor to finish the song
        while databases.PreprocessRequest.hasntBeenProcessed(procID):
            time.sleep(0.3)

        loval=self.preprocessor.lovals[songUUID]
        mdval=self.preprocessor.mdvals[songUUID]
        hival=self.preprocessor.hivals[songUUID]

        logger.info("Finished analysis, playing song")
        wavObj = wave.open(song)
        # Play audio and sync up light values
        pg.mixer.init(frequency=wavObj.getframerate(), size=wavObj.getsampwidth()*-8)
        pg.mixer.music.load(song)
        pg.mixer.music.play()

        while(pg.mixer.music.get_busy() == True and self.musicIsPlaying.value == constants.PLAY):
            # check for skip
            if(self.skipSong[0] != ' '):
                # skip song requested verify it's this song
                if(''.join(self.skipSong[:]) == ''.join(self.songPlaying[:])):
                    pg.mixer.music.stop()       # turn off music
                    self.skipSong[:] = constants.EMPTY_UUID # clear song to skip
                    break                       # exit loop
                else:
                    self.skipSong[:] = constants.EMPTY_UUID

            if(self.board is not None):
                try:
                    pos = pg.mixer.music.get_pos()
                    self.redPin.write(loval[(pos - self.latency.value)/constants.WINDOW_SIZE_SEC])
                    self.greenPin.write(mdval[(pos - self.latency.value)/constants.WINDOW_SIZE_SEC])
                    self.bluePin.write(hival[(pos - self.latency.value)/constants.WINDOW_SIZE_SEC])
                except:
                    logger.info('Don\'t go places you don\'t belong')
            else:
                time.sleep(0.1)
        if self.musicIsPlaying.value == constants.STOP:
            # music could've been stopped while song still playing, stop mixer
            pg.mixer.music.stop()
        else:
            # music stopped naturally, remove the preprocessing
            databases.PreprocessRequest.newDecomissionRequest(songUUID)

        if(self.board is not None):
            self.redPin.write(0)
            self.greenPin.write(0)
            self.bluePin.write(0)
        pg.mixer.quit()

    def standbyMode(self):
        logger.info('Standby Mode')
        cycles=20
        while(databases.SongInQueue.select().wrapped_count() == 0 or self.musicIsPlaying.value == constants.PLAY):
            if(cycles<20):
                #sine wave
                for i in range(0,314,2):
                    writeVal = m.sin(i/100.0)/2.0
                    self.writeToPinsAndSleep(writeVal, writeVal, writeVal, 0.025)
                    #end up for
            if(cycles>19 and cycles<40):
                #heartbeat
                for i in range(0,120,2):
                    writeVal = m.sin(i/100.0)/2.0
                    self.writeToPinsAndSleep(None, writeVal, writeVal, 0.025)
                #beat
                self.writeToPinsAndSleep(0.3, None, None, 0.04)
                self.writeToPinsAndSleep(0.0, None, None, 0.5)
                self.writeToPinsAndSleep(0.3, None, None, 0.04)
                self.writeToPinsAndSleep(0.0, None, None, 0.5)

                for i in range(120,0,-2):
                    writeVal = m.sin(i/100.0)/2.0
                    self.writeToPinsAndSleep(None, writeVal, writeVal, 0.025)

            if(cycles>39 and cycles<60):
                #color wheel
                #red up
                for i in range(30,60,2):
                    self.writeToPinsAndSleep(i/100.0, None, None, 0.05)
                #green down
                for i in range(60,30,2):
                    self.writeToPinsAndSleep(i/100.0, None, None, 0.05)
                #blue up
                for i in range(30,60,2):
                    self.writeToPinsAndSleep(None, None, i/100.0, 0.05)
                #red down
                for i in range(60,30,2):
                    self.writeToPinsAndSleep(i/100.0, None, None, 0.05)
                #green up
                for i in range(30,60,2):
                    self.writeToPinsAndSleep(None, i/100.0, None, 0.05)
                #blue down
                for i in range(60,30,2):
                    self.writeToPinsAndSleep(None, None, i/100.0, 0.05)
            cycles = (cycles + 1) % 60
            #end wrapped_count while
        #end standbyMode definition

    def writeToPinsAndSleep(self, pin1, pin2, pin3, sleepTime):
        if(pin1 is not None):
            self.redPin.write(pin1)
        if pin2 is not None:
            self.greenPin.write(pin2)
        if pin3 is not None:
            self.bluePin.write(pin3)
        if sleepTime is not None:
            time.sleep(sleepTime)

    def initBoard(self):
        self.board     = pf.Arduino('',join(self.boardLoc[:]).strip())          # init board
        self.redPin    = self.board.get_pin(''.join(self.redLoc[:]).strip())    # R
        self.greenPin  = self.board.get_pin(''.join(self.greenLoc[:]).strip())  # G
        self.bluePin   = self.board.get_pin(''.join(self.blueLoc[:]).strip())   # B
