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

# Declare some useful variables
counter = 1             # counter of samples
window = 0.02           # window size = 0.02 seconds
song = "Heaven.wav"     # example song
trigger=0               # used to end a while loop
maxpower=0              # modifier for rgb values
Fs=44100                # default frequency for audio files
winsamples=window*Fs    # number of samples per window

# Initialize board and set pins using pyfirmata
board = pf.Arduino('COM4')      # initialize board
pin3 = board.get_pin('d:3:p')   # set pin 3 for red
pin5 = board.get_pin('d:5:p')   # set pin 3 for green
pin6 = board.get_pin('d:6:p')   # set pin 3 for blue
print("Board initialized")

# Import sound file using scipy
raw= wf.read(song)        # raw comes in default format
y=np.array(raw[1])        # convert y to numpy array
orig=y                    # keep an original copy of y
songlength = len(y)       # total number of samples in y

# Find the start of the song
while y[counter][0]==0 and y[counter][1]==0:
    counter+=1
songstart=counter
print(songstart)

# Find maxpower of the song
while trigger==0:
    y=orig[counter:counter+winsamples]
    np.transpose(y)
    N=len(y)
    c=np.fft.fft(y)/N
    p=2*abs(c[2:int(m.floor(N/2))])
    f=range(1,int(m.floor(N/2)-1))
    f*=Fs/N
    totalpower=sum(sum(p[1:len(f)]))
    # check and update maxpower for this window
    if totalpower>maxpower:
        maxpower=totalpower
        # end totalpower if
    counter+=winsamples+1
    if counter>songlength:
        trigger=1
        # end counter if
    # end trigger while
print(maxpower)
print(totalpower)
print(p.shape)
print(len(f))
print(y.shape)
print(c.shape)
trigger=0
counter=songstart

# set lo, md, and hi value arrays
loval=[0]
mdval=[0]
hival=[0]
while trigger==0:
    y=orig[counter:counter+winsamples]
    np.transpose(y)
    N=len(y)
    c=np.fft.fft(y)/N
    p=2*abs(c[2:int(m.floor(N/2))])
    f=range(1,int(m.floor(N/2)-1))
    f*=Fs/N
    totalpower=sum(sum(p[1:len(f)]))

    lop = sum(sum(p[:13]))
    mdp = sum(sum(p[14:30]))
    hip = sum(sum(p[31:]))

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
print(len(loval))
print(loval[1000:1100])
print(max(loval))
print(max(mdval))
print(max(hival))
print("Done")



# Adjust light values
loval = loval/max(loval)
mdval = mdval/max(mdval)
hival = hival/max(hival)

print(loval[1000:1100])
print(mdval[1000:1100])
print(hival[1000:1100])


for i in range(1,len(loval)):
    if loval[i] > .95:
        hival[i]=0
        mdval[i]=0
        loval[i]=1
        # end loval if
    elif mdval[i] > .95:
        loval[i]=0
        mdval[i]=1
        hival[i]=0
        # end mdval if
    elif hival[i] > .95:
        loval[i]=0
        mdval[i]=0
        hival[i]=1
        # end hival if
    # end value for loop


# Play audio and sync up light values
pg.mixer.init()
pg.mixer.music.load(song)
pg.mixer.music.play()
i=0
while pg.mixer.music.get_busy() == True:
    if pg.mixer.music.get_pos() == 1:
        print("start!")
    if pg.mixer.music.get_pos()%20 == 0:
        print("20 milliseconds have elapsed")
        pin3.write(loval[i])
        pin5.write(mdval[i])
        pin6.write(hival[i])
        i+=1
    continue

pin3.write(0)
pin5.write(0)
pin6.write(0)






#####               ######
##### Testing Below ######
#####               ######

#testarray=np.array([[1,1],[1,1]])
#print(1)
#print("hello")
#print(counter)
#print(testarray.shape)
