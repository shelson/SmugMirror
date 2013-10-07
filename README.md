SmugMirror
==========

Python script to mirror a Smugmug library back to local storage.

This uses smugpy as an API library - created by Chris Hoffman
https://github.com/chrishoffman/smugpy

Requests is used for the actual download actions.

You can put API key details and other things in a .smugmirror 
file in your home dir and it'll read it, otherwise it asks
interactively.

Note that it uses the image filename as the filename - this works
fine for syncing, but it means if you've edited a file in the
SmugMug web interface (cropped, etc) you won't download the 
edited version right now. I need to work out some logic for that.

