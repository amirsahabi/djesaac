from scipy.io import wavfile as wf
import threading
import wave
import os
import databases
import numpy as np
import math as m
import logging
import time
import constants

logging.basicConfig(level=logging.INFO)

class SongPreprocessor(threading.Thread):
    def __init__(self):
        super(SongPreprocessor, self).__init__()
        self.lovals = {}
        self.mdvals = {}
        self.hivals = {}
        self.logger = logging.getLogger(__name__)

    def run(self):
        while(True):
            # yet another db monitor
            while databases.PreprocessRequest.select().wrapped_count() > 0:
                # get longest waiting request
                topRequest = databases.PreprocessRequest.select().order_by(databases.PreprocessRequest.datetime).get()

                # get request type
                if topRequest.requestType == constants.DB_PREPROC_PROCESS:
                    self.preprocessSong(topRequest.songPath, str(topRequest.songUUID))
                elif topRequest.requestType == constants.DB_PREPROC_DECOMISSION:
                    self.decomissionSong(str(topRequest.songUUID))
                else:
                    self.logger.info("Unknown request type")

                # remove the request
                databases.PreprocessRequest.delete().where(databases.PreprocessRequest.uuid == topRequest.uuid).execute()
            time.sleep(1.5)


    def decomissionSong(self, songUUID):
        if(songUUID in self.lovals.keys()):
            del self.lovals[songUUID]
        if(songUUID in self.mdvals.keys()):
            del self.mdvals[songUUID]
        if(songUUID in self.hivals.keys()):
            del self.hivals[songUUID]

    def preprocessSong(self, songPath, songUUID):
        # defensive check
        if(songUUID == constants.FAILED_UUID_STR):
            return

        # dont preprocess song if its already been processed
        if( songUUID in self.lovals.keys() and
            songUUID in self.mdvals.keys() and
            songUUID in self.hivals.keys()):
            # do not print
            self.logger.info("Do not have to preprocess song")
            return

        self.logger.info("Preprocessing " + songUUID)
        startTime = time.time()
        counter = 0             # counter of samples
        window = 0.02           # window size = 0.02 seconds
        trigger=0               # used to end a while loop
        Fs=wave.open(songPath).getframerate()                # default frequency for audio files
        winsamples=int(window*Fs)    # number of samples per window

        # Import sound file using scipy
        raw= wf.read(songPath)    # raw comes in default format
        y=np.array(raw[1])        # convert y to numpy array
        orig=y                    # keep an original copy of y
        songlength = len(y)       # total number of samples in y
        numsamps=int(songlength/winsamples)
        #auto determine frequency binning variables
        lopow=0
        lofreq=np.zeros(numsamps)
        mdpow=0
        mdfreq=np.zeros(numsamps)
        hipow=0
        hifreq=np.zeros(numsamps)
        #relative thresholding variables
        totalpowerarr=np.zeros(numsamps)
        powarr=np.zeros((int(winsamples/2)-1,numsamps))
        maxpower=0
        index=0

        # populate arrays for calculation later
        while trigger==0:
            y=orig[counter:counter+winsamples]
            N=len(y)
            if N < winsamples:
                break
            #fft and power calculation
            c=np.fft.fft(y)/N
            p=2*(abs(c[1:int(m.floor(N/2))])**2)
            p[:,0]=p[:,0]+p[:,1]
            powarr[:,index]=p[:,0]
            totalpower=np.sum(p[:,0])
            totalpowerarr[index]=totalpower
            if totalpower>maxpower:
                maxpower=totalpower
            #auto binning: finding frequencies with max powers
            lopowind=np.argmax(p[:15,0])
            lopow+=p[lopowind,0]
            lofreq[index]=lopowind
            mdpowind=np.argmax(p[10:30,0])
            mdpow+=p[mdpowind,0]
            mdfreq[index]=mdpowind+10
            hipowind=np.argmax(p[20:,0])
            hipow+=p[hipowind,0]
            hifreq[index]=hipowind+20

            counter+=winsamples
            if counter>songlength:
                trigger=1
                # end counter if
            index+=1
            # end trigger while
        trigger=0
        counter=0
        index=0

        #auto binning frequency calculation
        lomean=np.mean(lofreq)
        mdmean=np.mean(mdfreq)
        himean=np.mean(hifreq)
        #boundary between lo and mid
        f1=int(m.ceil(lomean+(mdmean-lomean)*mdpow/(mdpow+lopow)))
        #boundary between mid and hi
        f2=int(m.ceil(mdmean+(himean-mdmean)*hipow/(hipow+mdpow)))

        # preallocate lo, md, and hi value arrays
        loval=np.zeros(numsamps)
        mdval=np.zeros(numsamps)
        hival=np.zeros(numsamps)
        intfactor=1
        relthresh=1


        while trigger==0:
            y=orig[counter:counter+winsamples]
            N=len(y)
            if N<winsamples:
                break

            lop = np.sum(powarr[:f1,index])
            mdp = np.sum(powarr[f1:f2,index])
            hip = np.sum(powarr[f2:,index])

            if index>51 and index<numsamps-51:
                relthresh=np.sum(totalpowerarr[index-50:index+51])/100.0
            elif index>51:
                relthresh=np.sum(totalpowerarr[len(totalpowerarr)-100:])/100.0
            else:
                relthresh=np.sum(totalpowerarr[:101])/100.0

            #intensity factor
            intfactor=m.log10(maxpower*10.0/relthresh)

            loval[index]=lop/relthresh/intfactor
            mdval[index]=mdp/relthresh/intfactor
            hival[index]=hip/relthresh/intfactor

            index+=1

            counter+=winsamples+1
            if counter>songlength:
                trigger = 1
                # end counter if
            # end trigger while

        self.lovals[songUUID] = loval
        self.mdvals[songUUID] = mdval
        self.hivals[songUUID] = hival
        self.logger.info("Finished preprocessing {} in {} seconds".format(songUUID, time.time() - startTime))
        #end preprocessSong(self, songPath, songUUID)
