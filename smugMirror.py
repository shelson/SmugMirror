#!/usr/bin/env python

import os
import sys
import shutil
import requests
from smuploader import SmugMug

class ImageDownloader:
    def __init__(self):
        self.s = requests.Session()

    def getImage(self, url, destFile):
        response = self.s.get(url, stream=True)
        with open(destFile, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
        del response

RESTORE_PATH=os.environ["RESTORE_PATH"]

if __name__ == "__main__":
    sm = SmugMug()

    # Get all albums
    try:
        albums = sm.get_albums()
    except Exception as e:
        print("Couldn't get the list of albums, this isn't going to end well.")
        print(e.message)
        sys.exit(1)

    # Work through albums, listing category / album name

    # Create an instance of our downloader class, this means we can use keep-alives
    id = ImageDownloader()

    for album in albums:
        info = sm.get_album_info(album['AlbumKey'])

        print("About to download the contents of %s" % album['Title'])

        destPath = os.path.join(RESTORE_PATH, info['category_name'], album['Title'])

        try:
            os.makedirs(destPath)
        except OSError as e:
            # if the directory exists (errno 17) ignore it, else bail
            if e.errno != 17:
                print(e)
                sys.exit(1)

        images = sm.get_album_images(album_id=album['AlbumKey'])

        filesSeen = []

        for image in images:
            
            imgPrefix = ""
            imgName = image["FileName"]
            imgSize = image["ArchivedSize"]

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
                    print("%s already exists, skipping" % destFile)
                else:
                    print("%s doesn't match file size, re-downloading" % destFile)
                    needsDownloading = True

            if needsDownloading:
                print("Downloading %s to %s..." % (image["FileName"], destFile))
                sys.stdout.flush()
                sm.download_image(image, destFile)


