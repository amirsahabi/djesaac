import threading
import wave
import numpy as np
import math as m
from scipy.io import wavfile as wf

class SongPreprocessor(threading.Thread):
    def __init__(self):
        super(SongPreprocessor, self).__init__()
        self.lovals = {}
        self.mdvals = {}
        self.hivals = {}
        print("Started preprocessor thread")

    def preprocessSong(self, songPath, songUUID):
        counter = 0             # counter of samples
        window = 0.02           # window size = 0.02 seconds
        trigger=0               # used to end a while loop
        maxpower=0              # modifier for rgb values
        Fs=wave.open(songPath).getframerate()                # default frequency for audio files


        winsamples=window*Fs    # number of samples per window

        # Import sound file using scipy
        raw= wf.read(songPath)    # raw comes in default format
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

            if loval[i] < 0.04:
                loval[i] = 0
            if mdval[i] < 0.04:
                mdval[i] = 0
            if hival[i] < 0.04:
                hival[i] = 0
        self.lovals[songUUID] = loval
        self.mdvals[songUUID] = mdval
        self.hivals[songUUID] = hival
