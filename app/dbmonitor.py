# dbmonitor.py
from scipy.io import wavfile as wf
from multiprocessing import Value
import time
import databases
import numpy as np
import math as m
import pyfirmata as pf
import pygame as pg
import wave
import preprocessor
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DBMonitor:
    def __init__(self, musicIsPlayingValue, songPlayingValue, skipSongRequest, threadIssue):
        # I like the idea of encapsulation for all these functions and variables
        # but when the object is instantiated in the main thread, it instantiates
        # an object before the run() function is called in its new process
        # (by multiprocessing.Process). To prevent creating redundant connections
        # (or even dual spawning threads), this variable prevents the object
        # from instantiating. Note that the run() function also calls __init__()
        if threadIssue:
            return

        self.songPlaying    = songPlayingValue         # multiprocessing.Array object
        self.musicIsPlaying = musicIsPlayingValue   # multiprocessing.Value object
        self.skipSong       = skipSongRequest
        self.board          = None
        self.pin3           = None
        self.pin5           = None
        self.pin6           = None

        self.preprocessor = preprocessor.SongPreprocessor()
        self.preprocessor.start()

        # Initialize board and set pins using pyfirmata
        try:
            self.board = pf.Arduino('COM4')      # initialize board
            self.pin3 = self.board.get_pin('d:3:p')   # set pin 3 for red
            self.pin5 = self.board.get_pin('d:5:p')   # set pin 5 for green
            self.pin6 = self.board.get_pin('d:6:p')   # set pin 6 for blue
            logger.info("Board initialized")
        except:
            # failed for windows, try mac
            try:
                self.board = pf.Arduino('/dev/tty.usbmodem1421')      # initialize board
                self.pin3 = self.board.get_pin('d:3:p')   # set pin 3 for red
                self.pin5 = self.board.get_pin('d:5:p')   # set pin 5 for green
                self.pin6 = self.board.get_pin('d:6:p')   # set pin 6 for blue
                logger.info("Board initialized")
            except:
                self.board = None
                logger.info("Failed to initialize board, will only play music")
        logger.info("DBMonitor initialized")

    def run(self, musicIsPlayingMultiProcVal, songIsPlayingMultiProcVal, skipSongRequestArr, threadIssue):
        logger.info("Running DBMonitor")
        self.__init__(musicIsPlayingMultiProcVal, songIsPlayingMultiProcVal, skipSongRequestArr, threadIssue)

        while(True):
            while(self.musicIsPlaying.value == 1 and databases.SongInQueue.select().wrapped_count() > 0):
                song = databases.SongInQueue.select().order_by(databases.SongInQueue.dateAdded).get()
                self.songPlaying[:] = str(song.uuid)

                self.playSong(song.songPath, ''.join(self.songPlaying[:]))

                if self.musicIsPlaying.value == 1:
                    # add to History
                    databases.History.addSongToHistory(song.songTitle, song.songLink, song.songPath)

                    # remove song from queue
                    databases.SongInQueue.delete().where(databases.SongInQueue.uuid == song.uuid).execute()
            self.songPlaying[:] = ' ' * 36
            if self.board is not None:
                self.standbyMode()
            else:
                time.sleep(3)

    def playSong(self, song, songUUID):
        logger.info("Received song request")

        procID = -1
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

        # Play audio and sync up light values
        pg.mixer.init(frequency=wave.open(song).getframerate())
        pg.mixer.music.load(song)
        pg.mixer.music.play()
        first = True
        initVal = 0
        while(pg.mixer.music.get_busy() == True and self.musicIsPlaying.value == 1):
            # check for skip
            if(self.skipSong[0] != ' '):
                # skip song requested verify it's this song
                if(''.join(self.skipSong[:]) == ''.join(self.songPlaying[:])):
                    pg.mixer.music.stop()       # turn off music
                    self.skipSong[:] = ' ' * 36 # clear song to skip
                    break                       # exit loop
                else:
                    self.skipSong[:] = ' ' * 36

            if(self.board is not None):
                try:
                    pos = pg.mixer.music.get_pos()
                    if first:
                        initVal = pos
                        first = False
                    self.pin3.write(loval[(pos - initVal)/20])
                    self.pin5.write(mdval[(pos - initVal)/20])
                    self.pin6.write(hival[(pos - initVal)/20])
                except:
                    logger.info('Don\'t go places you don\'t belong')
        if not (self.musicIsPlaying.value == 1):
            # music could've been stopped while song still playing, stop mixer
            pg.mixer.music.stop()
        else:
            # music stopped naturally, remove the preprocessing
            databases.PreprocessRequest.newDecomissionRequest(songUUID)

        if(self.board is not None):
            self.pin3.write(0)
            self.pin5.write(0)
            self.pin6.write(0)

    def standbyMode(self):
        cycles=20
        while(databases.SongInQueue.select().wrapped_count()==0):
            if(cycles<20):
                #sine wave
                for i in range(0,314,2):
                    self.pin3.write(m.sin(i/100.0)/2.0)
                    self.pin5.write(m.sin(i/100.0)/2.0)
                    self.pin6.write(m.sin(i/100.0)/2.0)
                    time.sleep(.025)
                    #end up for
            if(cycles>19 and cycles<40):
                #heartbeat
                for i in range(0,120,2):
                    self.pin5.write(m.sin(i/100.0)/2.0)
                    self.pin6.write(m.sin(i/100.0)/2.0)
                    time.sleep(.025)
                #beat
                self.pin3.write(.3)
                time.sleep(.04)
                self.pin3.write(0)
                time.sleep(.5)
                #beat
                self.pin3.write(.3)
                time.sleep(.04)
                self.pin3.write(0)
                time.sleep(.5)
                for i in range(120,0,-2):
                    self.pin5.write(m.sin(i/100.0)/2.0)
                    self.pin6.write(m.sin(i/100.0)/2.0)
                    time.sleep(.025)

            if(cycles>39 and cycles<60):
                #color wheel
                #red up
                for i in range(30,60,2):
                    self.pin3.write(i/100.0)
                    time.sleep(.05)
                #green down
                for i in range(60,30,2):
                    self.pin5.write(i/100.0)
                    time.sleep(.05)
                #blue up
                for i in range(30,60,2):
                    self.pin6.write(i/100.0)
                    time.sleep(.05)
                #red down
                for i in range(60,30,2):
                    self.pin3.write(i/100.0)
                    time.sleep(.05)
                #green up
                for i in range(30,60,2):
                    self.pin5.write(i/100.0)
                    time.sleep(.05)
                #blue down
                for i in range(60,30,2):
                    self.pin6.write(i/100.0)
                    time.sleep(.05)
            if(cycles>59):
                cycles=0
            cycles+=1
            #end wrapped_count while
        #end standbyMode definition
