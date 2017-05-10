from scipy.io import wavfile as wf
import threading
import wave
import soundfile
import databases
import numpy as np
import math as m
import logging
import time
import constants

logging.basicConfig(level=constants.LOG_LEVEL)


class SongPreprocessor(threading.Thread):
    def __init__(self):
        super(SongPreprocessor, self).__init__()
        self.lovals = {}
        self.mdvals = {}
        self.hivals = {}
        self.logger = logging.getLogger(__name__)

    def run(self):
        while True:
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
        if songUUID in self.lovals.keys():
            del self.lovals[songUUID]
        if songUUID in self.mdvals.keys():
            del self.mdvals[songUUID]
        if songUUID in self.hivals.keys():
            del self.hivals[songUUID]

    def preprocessSong(self, songPath, songUUID):
        # defensive check
        if songUUID == constants.FAILED_UUID_STR:
            return

        # dont preprocess song if its already been processed
        if(songUUID in self.lovals.keys() and
            songUUID in self.mdvals.keys() and
            songUUID in self.hivals.keys()):
            # do not print
            self.logger.info("Do not have to preprocess song")
            return

        self.logger.info("Preprocessing " + songUUID)
        startTime = time.time()
        counter = 0             # counter of samples
        window = constants.WINDOW_SIZE_MSEC # window size = 0.02 seconds
        y, Fs = soundfile.read(songPath)                # default frequency for audio files
        winsamples = int(window*Fs)    # number of samples per window

        # Import sound file using scipy
        orig = y                  # keep an original copy of y
        songlength = len(y)       # total number of samples in y
        numsamps = int(songlength/winsamples)
        # auto determine frequency binning variables
        lopow = 0
        lofreq = np.zeros(numsamps)
        mdpow = 0
        mdfreq = np.zeros(numsamps)
        hipow = 0
        hifreq = np.zeros(numsamps)
        # relative thresholding variables
        totalpowerarr = np.zeros(numsamps)
        powarr = np.zeros((int(winsamples/2)-1, numsamps))
        maxpower = 0
        index = 0

        # populate arrays for calculation later
        while True:
            y = orig[counter:counter+winsamples]
            N = len(y)
            if N < winsamples:
                break
            # fft and power calculation
            c = np.fft.fft(y, axis=0)/N
            p = 2*(abs(c[1:int(m.floor(N/2))])**2)
            psize = p.shape
            psub = p
            if len(psize) > 1:
                psub = p[:, 0]+p[:, 1]
            powarr[:, index] = psub
            totalpower = np.sum(psub)
            totalpowerarr[index] = totalpower
            if totalpower > maxpower:
                maxpower = totalpower
            # auto binning: finding frequencies with max powers
            lopowind = np.argmax(psub[:15])
            lopow += psub[lopowind]
            lofreq[index] = lopowind
            mdpowind = np.argmax(psub[10:30])
            mdpow += psub[mdpowind]
            mdfreq[index] = mdpowind+10
            hipowind = np.argmax(psub[20:])
            hipow += psub[hipowind]
            hifreq[index] = hipowind+20

            counter += winsamples
            if counter > songlength:
                break
            index += 1

        counter = 0
        index = 0

        # auto binning frequency calculation
        lomean = np.mean(lofreq)
        mdmean = np.mean(mdfreq)
        himean = np.mean(hifreq)
        # boundary between lo and mid
        f1 = int(m.ceil(lomean+(mdmean-lomean)*mdpow/(mdpow+lopow)))
        # boundary between mid and hi
        f2 = int(m.ceil(mdmean+(himean-mdmean)*hipow/(hipow+mdpow)))

        # preallocate lo, md, and hi value arrays
        loval = np.zeros(numsamps)
        mdval = np.zeros(numsamps)
        hival = np.zeros(numsamps)
        intfactor = 1
        relthresh = 1


        while True:
            y = orig[counter:counter+winsamples]
            N = len(y)
            if N < winsamples:
                break

            lop = np.sum(powarr[:f1, index])
            mdp = np.sum(powarr[f1:f2, index])
            hip = np.sum(powarr[f2:, index])

            if index > 51:
                if index < numsamps-51:
                    relthresh = np.sum(totalpowerarr[index-50:index+51])/100.0
                else:
                    relthresh = np.sum(totalpowerarr[len(totalpowerarr)-100:])/100.0
            else:
                relthresh = np.sum(totalpowerarr[:101])/100.0

            if relthresh == 0:
                loval[index] = 0
                mdval[index] = 0
                hival[index] = 0
                intfactor = 0
            else:
                # intensity factor
                intfactor = m.log10(maxpower*10.0/relthresh)
            if intfactor == 0:
                loval[index] = 0
                mdval[index] = 0
                hival[index] = 0
            else:
                loval[index] = lop/relthresh/intfactor
                mdval[index] = mdp/relthresh/intfactor
                hival[index] = hip/relthresh/intfactor

            index += 1

            counter += winsamples + 1
            if counter > songlength:
                break

        self.lovals[songUUID] = loval
        self.mdvals[songUUID] = mdval
        self.hivals[songUUID] = hival
        self.logger.info("Finished preprocessing {} in {} seconds".format(songUUID, time.time() - startTime))
