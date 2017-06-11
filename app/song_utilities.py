from __future__ import unicode_literals
from bs4 import BeautifulSoup as bs
from pydub import AudioSegment
from pydub.utils import which
import datetime
import requests
import constants
import databases
import youtube_dl
import os
import logging

AudioSegment.converter = which("ffmpeg")

logging.basicConfig(level=constants.LOG_LEVEL)
logger = logging.getLogger(__name__)


def get_related_video_url(input_url):
    logger.info('autoplaying next song from ' + input_url)
    # check if is youtube or soundcloud link
    return_link = constants.EMPTY_INPUT

    # get link
    page = requests.get(input_url)
    soup = bs(page.content, 'html.parser')

    if constants.YOUTUBE in input_url:
        search_class = constants.CONTENT_LINK
        send_url = constants.YOUTUBE
    elif constants.SOUNDCLOUD in input_url:
        search_class = constants.SIDE_BAR
        send_url = constants.SOUNDCLOUD
    else:
        return return_link

    # get list of related links
    related_links = soup.find_all('a', {'class': search_class})

    # get the first
    if related_links is not None and len(related_links) > 0:
        for link in related_links:
            http_link = constants.HTTP + send_url + link.get('href')
            https_link = constants.HTTPS + send_url + link.get('href')

            # make sure that link hasn't been already used
            if(databases.History.select().where(databases.History.songLink == http_link).wrapped_count() > 0 or
               databases.History.select().where(databases.History.songLink == https_link).wrapped_count() > 0 or
               databases.SongInQueue.select().where(databases.SongInQueue.songLink == http_link).wrapped_count() > 0 or
               databases.SongInQueue.select().where(databases.SongInQueue.songLink == https_link).wrapped_count() > 0):
                continue
            return_link = constants.HTTPS + send_url + link.get('href')

        if return_link == constants.EMPTY_INPUT:
            # all the related songs have been played, it's fine just play the first one
            return_link = constants.HTTPS + send_url + related_links[0].get('href')

    return return_link


def addSongToQueue(songLink):
    songUUID = constants.FAILED_UUID_STR
    try:
        # given songlink, use youtubedl to download it
        # set options

        # create youtubedl object
        ydl = youtube_dl.YoutubeDL(constants.YDL_OPTIONS)

        if not songHasBeenDownloaded(songLink):

            # get metadata and download song while we're at it
            metadata = ydl.extract_info(songLink, download=True)

            # log
            logger.info('Finished downloading song, converting to designated format')
            start_time = datetime.datetime.now()

            # convert the song from mp3 to wav for reasons
            AudioSegment.from_file('./music/'+metadata['id']).export('./music/'+metadata['id']+constants.SONG_FORMAT_EXTENSION, format=constants.SONG_FORMAT, bitrate=constants.SONG_BITRATE)

            # remove original
            os.remove('./music/'+metadata['id'])

            # log finished
            logger.info('Finished converting song in ' + str(datetime.datetime.now() - start_time) + 'seconds')
        else:
            logger.info("Song existed, no need to redownload")

            metadata = ydl.extract_info(songLink, download=False)

        # given metadata, log to database
        songUUID = str(databases.SongInQueue.addSongToQueue('./music/'+metadata['id']+constants.SONG_FORMAT_EXTENSION, metadata['title'], songLink, metadata['duration']))

        if songUUID != constants.FAILED_UUID_STR:
            # tell the preprocessor in the dbmonitor to preprocess it
            databases.PreprocessRequest.newPreProcessRequest('./music/'+metadata['id']+constants.SONG_FORMAT_EXTENSION, songUUID)
            # add a new action event
            databases.ActionHistory.newAddSong(metadata['title'], songUUID, songLink, metadata['duration'])
        else:
            return songUUID

    except:
        return songUUID

    return songUUID


def songHasBeenDownloaded(songLink):
    # check both history and songqueue for the song
    songs = databases.SongInQueue.select().where(databases.SongInQueue.songLink == songLink)
    for song in songs:
        if os.path.isfile(song.songPath):
            # has been downloaded
            return True

    songs = databases.History.select().where(databases.History.songLink == songLink)
    for song in songs:
        if os.path.isfile(song.songPath):
            return True

    return False
