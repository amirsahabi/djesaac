#
#author      Conner Brown
#file        djezak.py
#date        04/02/2017
#update      04/02/2017
#brief       Transcribed code from djezak.m. Takes audio file as mp3, analyzes frequency components, writes to Arduino pins as the song is played
#

import numpy as np
import math as m
from scipy.io import wavfile as wf

counter = 1             # counter of samples
window = 0.02           # window size = 0.02 seconds
song = "Heaven.wav"     # example song
trigger=0               # used to end a while loop
maxpower=0              # modifier for rgb values
Fs=44100                # default frequency for audio files
winsamples=window*Fs    # number of samples per window

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
trigger=0
counter=songstart









#####               ######
##### Testing Below ######
#####               ######

#testarray=np.array([[1,1],[1,1]])
#print(1)
#print("hello")
#print(counter)
#print(testarray.shape)
