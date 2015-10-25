#!/usr/bin/env python

import os
import sys
import Queue
import smugpy
import shutil
import getpass
import requests
import threading
import ConfigParser

# baked-in defaults
SCRIPT_NAME = 'SmugMirror'
API_KEY = '<enter api key here>'
RESTORE_PATH="./restore"
USER_NAME = ""

# number of albums to try and fetch at once
THREADS = "2"

class ImageDownloader:
    def __init__(self):
        self.s = requests.Session()

    def getImage(self, url, destFile):
        response = self.s.get(url, stream=True)
        with open(destFile, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
        del response




# Check for .smugmirror, read data from there if it exists
config = ConfigParser.RawConfigParser()
try:
    config.read(os.path.join(os.path.expanduser('~'), '.smugmirror'))
except:
    print "No .smugmirror file found in home dir, using script defaults"
    pass
else:
    SCRIPT_NAME = config.get('main', 'script_name')
    API_KEY = config.get('main', 'api_key')
    RESTORE_PATH = config.get('main', 'restore_path')
    USER_NAME = config.get('main', 'user_name')
    PASSWORD = config.get('main', 'password')

if USER_NAME == "":
    # signon
    USER_NAME = raw_input('Email address: ')
    PASSWORD = getpass.getpass('Password: ')

# using the old API (1.2.2), which is easier to use for one shot scripts (avoids OAuth)
smugmug = smugpy.SmugMug(api_key=API_KEY, api_version="1.2.2", app_name=SCRIPT_NAME)

try:
    smugmug.login_withPassword(EmailAddress=USER_NAME, Password=PASSWORD)
except smugpy.SmugMugException, e:
    print "Failed to log in, check the error below and sort it out!"
    print e.message
    sys.exit(1)

# Get all albums
try:
    albums = smugmug.albums_get()
except Exception, e:
    print "Couldn't get the list of albums, this isn't going to end well."
    print e.message
    sys.exit(1)

# Work through albums, listing category / album name

# Create an instance of our downloader class, this means we can use keep-alives
id = ImageDownloader()

for album in albums['Albums']:
    print "About to download the contents of %s" % album['Title']

    destPath = os.path.join(RESTORE_PATH, album['Category']['Name'], album['Title'])

    try:
        os.makedirs(destPath)
    except OSError, e:
        # if the directory exists (errno 17) ignore it, else bail
        if e.errno != 17:
            print e
            sys.exit(1)

    images = smugmug.images_get(AlbumID=album['id'], AlbumKey=album['Key'])

    filesSeen = []

    for image in images['Album']['Images']:
        print "[image: %s] [info]" % image['id'],
        sys.stdout.flush()
        info = smugmug.images_getInfo(ImageID=image['id'], ImageKey=image['Key'])
        imgSize = info['Image']['Size']
        imgName = info['Image']['FileName']
        
        imgPrefix = ""

        if filesSeen.count(imgName) > 0:
            # add it to the list before we mangle it's name in case there are
            # more occurrences!
            filesSeen.append(imgName)
            # make up a name for this image using some logic
            tmpName = ".".join(imgName.split('.')[:-1])
            tmpExt = imgName.split('.')[-1]
            imgName = "".join([tmpName, "_", str(filesSeen.count(imgName) - 1), ".", tmpExt])
        else:
            # simply append it to the list
            filesSeen.append(imgName)

        destFile = os.path.join(destPath, imgName)

        # in the interests of saving an API call, check if the output filename
        # exists now, since if it does and the size matches we don't need to 
        # ask the API for the download URL.

        needsDownloading = False

        try:
            fstats = os.stat(destFile)
        except:
            needsDownloading = True
        else:
            if fstats.st_size == imgSize:
                print "%s already exists, skipping" % destFile
            else:
                print "%s doesn't match file size, re-downloading" % destFile
                needsDownloading = True

        if needsDownloading:
            print "[urls] ",
            sys.stdout.flush()
            urls = smugmug.images_getURLs(ImageID=image['id'], ImageKey=image['Key'])

            print "Downloading %s to %s..." % (info['Image']['OriginalURL'], destFile),
            sys.stdout.flush()
            #id.getImage(urls['Image']['OriginalURL'], destFile)
            print "Done."


