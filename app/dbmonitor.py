# dbmonitor.py
import time
import threading
import databases
import numpy as np
import math as m
from scipy.io import wavfile as wf
import pyfirmata as pf
import pygame as pg
import wave

class DBMonitor(threading.Thread):
    def __init__(self):
        super(DBMonitor, self).__init__()
        self.songPlaying = None
        self.musicIsPlaying = True
        self.board = None
        self.pin3 = None
        self.pin5 = None
        self.pin6 = None

        # Initialize board and set pins using pyfirmata
        try:
            self.board = pf.Arduino('COM4')      # initialize board
            self.pin3 = self.board.get_pin('d:3:p')   # set pin 3 for red
            self.pin5 = self.board.get_pin('d:5:p')   # set pin 5 for green
            self.pin6 = self.board.get_pin('d:6:p')   # set pin 6 for blue
            print("Board initialized")
        except:
            # failed for windows, try mac
            try:
                self.board = pf.Arduino('/dev/tty.usbmodem1421')      # initialize board
                self.pin3 = self.board.get_pin('d:3:p')   # set pin 3 for red
                self.pin5 = self.board.get_pin('d:5:p')   # set pin 5 for green
                self.pin6 = self.board.get_pin('d:6:p')   # set pin 6 for blue
                print("Board initialized")
            except:
                self.board = None
                print("Failed to initialize board, will only play music")
        print("DBMonitor initialized")

    def run(self):
        while(True):
            while(self.musicIsPlaying and databases.SongInQueue.select().wrapped_count() > 0):
                song = databases.SongInQueue.select().order_by(databases.SongInQueue.dateAdded).get()
                self.songPlaying = str(song.uuid)

                self.playSong(song.songPath)

                if self.musicIsPlaying:
                    # add to History
                    databases.History.addSongToHistory(song.songTitle, song.songLink, song.songPath)

                    # remove song from queue
                    databases.SongInQueue.delete().where(databases.SongInQueue.uuid == song.uuid).execute()
            self.songPlaying = None
            if self.board is not None:
                self.standbyMode()
            else:
                time.sleep(3)

    def preprocess(self,nextsong):
        counter = 0             # counter of samples
        window = 0.02           # window size = 0.02 seconds
        trigger=0               # used to end a while loop
        maxpower=0              # modifier for rgb values
        Fs=wave.open(song).getframerate()                # default frequency for audio files


        winsamples=window*Fs    # number of samples per window

        # Import sound file using scipy
        raw= wf.read(song)        # raw comes in default format
        y=np.array(raw[1])        # convert y to numpy array
        orig=y                    # keep an original copy of y
        songlength = len(y)       # total number of samples in y

        # Find maxpower of the song
        while trigger==0:
            y=orig[counter:counter+winsamples]
            N=len(y)
            if N==0:
                break
            c=np.fft.fft(y)/N
            p=2*abs(c[1:int(m.floor(N/2))])
            f=range(0,int(m.floor(N/2)-1))
            f=f*(Fs/N)
            totalpower=np.sum(p[1:len(f)])
            # check and update maxpower for this window
            if totalpower>maxpower:
                maxpower=totalpower
                # end totalpower if
            counter+=winsamples+1
            if counter>songlength:
                trigger=1
                # end counter if
            # end trigger while
        trigger=0
        counter=0

        # set lo, md, and hi value arrays
        self.loval=[0]
        self.mdval=[0]
        self.hival=[0]
        while trigger==0:
            y=orig[counter:counter+winsamples]
            N=len(y)
            if N==0:
                break
            c=np.fft.fft(y)/N
            p=2*abs(c[1:int(m.floor(N/2))])
            f=range(0,int(m.floor(N/2)-1))
            f*=Fs/N
            totalpower=np.sum(p[1:len(f)])

            lop = np.sum(p[:13])
            mdp = np.sum(p[14:30])
            hip = np.sum(p[31:])

            red = [lop*totalpower/maxpower]
            grn = [mdp*totalpower/maxpower]
            blu = [hip*totalpower/maxpower]

            self.loval = np.concatenate((self.loval,red),axis=0)
            self.mdval = np.concatenate((self.mdval,grn),axis=0)
            self.hival = np.concatenate((self.hival,blu),axis=0)
            counter+=winsamples+1
            if counter>songlength:
                trigger = 1
                # end counter if
            # end trigger while
        # Adjust light values
        self.loval = self.loval/max(self.loval)
        self.mdval = self.mdval/max(self.mdval)
        self.hival = self.hival/max(self.hival)

        for i in range(1,len(self.loval)):
            if self.loval[i] > .90:
                self.hival[i]=0
                self.mdval[i]=0
                self.loval[i]=1
                # end loval if
            elif self.mdval[i] > .90:
                self.loval[i]=0
                self.mdval[i]=1
                self.hival[i]=0
                # end mdval if
            elif self.hival[i] > .90:
                self.loval[i]=0
                self.mdval[i]=0
                self.hival[i]=1
                # end hival if
            # end value for loop

            if self.loval[i] < 0.04:
                self.loval[i] = 0
            if self.mdval[i] < 0.04:
                self.mdval[i] = 0
            if self.hival[i] < 0.04:
                self.hival[i] = 0

    def playSong(self, song):
        print("Received song request")
        self.preprocess(song)
        loval=self.loval
        mdval=self.mdval
        hival=self.hival
        print("Finished analysis, playing song")

        # Play audio and sync up light values
        pg.mixer.init(frequency=wave.open(song).getframerate())
        pg.mixer.music.load(song)
        pg.mixer.music.play()
        first = True
        initVal = 0
        while pg.mixer.music.get_busy() == True and self.musicIsPlaying:
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
                    print('Don\'t go places you don\'t belong')
        if not self.musicIsPlaying:
            # music could've been stopped while song still playing, stop mixer
            pg.mixer.music.stop()

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
