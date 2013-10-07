#!/usr/bin/env python

import os
import sys
import smugpy
import shutil
import getpass
import requests

SCRIPT_NAME = 'SmugMirror'
API_KEY = '<enter api key here>'
RESTORE_PATH="./restore"

def downloadImage(url, destFile):
    sys.stdout.write("Downloading: %s.... " % url)
    sys.stdout.flush()

    response = requests.get(url, stream=True)
    with open(destFile, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
    del response

    print "Done."
    sys.stdout.flush()


# using the old API (1.2.2), which is easier to use for one shot scripts (avoids OAuth)
smugmug = smugpy.SmugMug(api_key=API_KEY, api_version="1.2.2", app_name=SCRIPT_NAME)

# signon
USER_NAME = raw_input('Email address: ')
PASSWORD = getpass.getpass('Password: ')
smugmug.login_withPassword(EmailAddress=USER_NAME, Password=PASSWORD)

# Get all albums
albums = smugmug.albums_get()

# Work through albums, listing category / album name

for album in albums['Albums']:
    print "About to download the contents of %s" % album['Title']

    destPath = os.path.join(RESTORE_PATH, album['Category']['Name'], album['Title'])

    try:
        os.makedirs(destPath)
    except OSError, e:
        if e.errno != 17:
            print e
            sys.exit(1)

    images = smugmug.images_get(AlbumID=album['id'], AlbumKey=album['Key'])

    for image in images['Album']['Images']:
        print "[image: %s] [info]" % image['id'],
        sys.stdout.flush()
        info = smugmug.images_getInfo(ImageID=image['id'], ImageKey=image['Key'])
        imgSize = info['Image']['Size']
        print "[urls] ",
        sys.stdout.flush()
        urls = smugmug.images_getURLs(ImageID=image['id'], ImageKey=image['Key'])
        # download image
        imgName = urls['Image']['OriginalURL'].split('/')[-1]

        destFile = os.path.join(destPath, imgName)

        # we need the file size, so we can use exceptions to see if
        # it also exists ;-)
        try:
            fstats = os.stat(destFile)
        except:
            downloadImage(urls['Image']['OriginalURL'], destFile)
        else:
            if fstats.st_size == imgSize:
                print "%s already exists, skipping" % destFile
            else:
                print "%s doesn't match file size, re-downloading" % destFile
                downloadImage(urls['Image']['OriginalURL'], destFile)


