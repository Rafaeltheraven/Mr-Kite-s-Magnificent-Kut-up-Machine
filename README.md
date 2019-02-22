# Mr-Kite-s-Magnificent-Kut-up-Machine
Mr Kite's Magnificent Kut-up Machine (MKMKM) is a python program that creates a random sound collage from your music. 
Start the program by running `python gui.py`. There are a couple of requirements though.

MKMKM requires: 
* PyQt5 (GUI)
* fleep (Check file type)
* pydub (Manipulating audio)
* eyed3 (Checking tags for mp3)
* mutagen (Checking tags for other files)
* FFMPEG OR LibAv (Playing audio)

If you are noticing errors in playback it is recommended to install one of the following
* simpleaudio
* pyaudio

This is (seemingly) an FFMPEG bug with Windows permissions. Installing one of the above modules will change the way playback is done to circumvent this.

Best experienced by using an Audio visualizer like Milkdrop2
