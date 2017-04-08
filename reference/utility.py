#
#author      Conner Brown
#file        utility.py
#date        04/02/2017
#update      04/02/2017
#brief       Transcribed code from djezak.m. Takes audio file as mp3, analyzes frequency components, writes to Arduino pins as the song is played
#

import numpy as np
import math as m
from scipy.io import wavfile as wf
import pyfirmata as pf
import pygame as pg
import wave


# Declare some useful variables


board = None
pin3 = None
pin5 = None
pin6 = None

# Initialize board and set pins using pyfirmata
try:
    board = pf.Arduino('COM4')      # initialize board
    pin3 = board.get_pin('d:3:p')   # set pin 3 for red
    pin5 = board.get_pin('d:5:p')   # set pin 5 for green
    pin6 = board.get_pin('d:6:p')   # set pin 6 for blue
    print("Board initialized")
except:
    # failed for windows, try mac
    try:
        board = pf.Arduino('/dev/tty.usbmodem1421')      # initialize board
        pin3 = board.get_pin('d:3:p')   # set pin 3 for red
        pin5 = board.get_pin('d:5:p')   # set pin 5 for green
        pin6 = board.get_pin('d:6:p')   # set pin 6 for blue
        print("Board initialized")
    except:
        print("Failed to initialize board, will only play music")

def playSong(song):
    print("Received song request")

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
    loval=[0]
    mdval=[0]
    hival=[0]
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

        loval = np.concatenate((loval,red),axis=0)
        mdval = np.concatenate((mdval,grn),axis=0)
        hival = np.concatenate((hival,blu),axis=0)
        counter+=winsamples+1
        if counter>songlength:
            trigger = 1
            # end counter if
        # end trigger while
    # Adjust light values
    loval = loval/max(loval)
    mdval = mdval/max(mdval)
    hival = hival/max(hival)

    for i in range(1,len(loval)):
        if loval[i] > .90:
            hival[i]=0
            mdval[i]=0
            loval[i]=1
            # end loval if
        elif mdval[i] > .90:
            loval[i]=0
            mdval[i]=1
            hival[i]=0
            # end mdval if
        elif hival[i] > .90:
            loval[i]=0
            mdval[i]=0
            hival[i]=1
            # end hival if
        # end value for loop

        if loval[i] < 0.08:
            loval[i] = 0
        if mdval[i] < 0.08:
            mdval[i] = 0
        if hival[i] < 0.08:
            hival[i] = 0

    print("Finished analysis, playing song")

    # Play audio and sync up light values
    pg.mixer.init(frequency=wave.open(song).getframerate())
    pg.mixer.music.load(song)
    pg.mixer.music.play()
    first = True
    initVal = 0
    while pg.mixer.music.get_busy() == True:
        if(board is not None):
            try:
                pos = pg.mixer.music.get_pos()
                if first:
                    initVal = pos
                    first = False
                pin3.write(loval[(pos - initVal)/20])
                pin5.write(mdval[(pos - initVal)/20])
                pin6.write(hival[(pos - initVal)/20])
            except:
                print('Don\'t go places you don\'t belong')

    if(board is not None):
        pin3.write(0)
        pin5.write(0)
        pin6.write(0)
