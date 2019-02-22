from pydub import AudioSegment
from pydub.effects import *
from pydub.playback import play
import random
import pickle
import os

def repeat(track):
	track = track * random.randint(2, 5)
	return track

def shuffle(track):
	splitted = track[::1000]
	splitList = list(splitted)
	random.shuffle(splitList)
	result = AudioSegment.empty()
	for segment in splitList:
		result += segment
	track = result
	return track

def overlay(track):
	overlayTrack = random_track()
	loop = bool(random.getrandbits(1))
	position = random.randint(0, len(track))
	gain = random.randint(-8, 9)
	track = track.overlay(overlayTrack, position=position, loop=loop, gain_during_overlay=gain)
	return track

def fade(track):
	fromGain = round(random.uniform(-8, 0), 2)
	toGain = round(random.uniform(0.1, 10), 2)
	start = random.randint(0, len(track))
	end = random.randint(start, len(track) + 1)
	track = track.fade(to_gain=toGain, from_gain=fromGain, start=start, end=end)
	return track

def gain(track):
	gain_var = round(random.uniform(-20, 21), 2)
	track = track + gain_var
	return track

def rev(track):
	track = track.reverse()
	return track

def pann(track):
	pan = round(random.uniform(-1.0, 1.0), 2)
	track = track.pan(pan)
	return track

def invert(track):
	track = track.invert_phase()
	return track

def quality(track):
	track.set_sample_width(1)
	track.set_channels(1)
	track.set_frame_rate(11025)
	return track

def speed(track):
	speed = round(random.uniform(1, 2), 2)
	print("speed: " + str(speed))
	track = speedup(track, playback_speed=speed)
	return track

def random_track():
	with open('fileNames', 'rb') as fp:
		musicPathsArray = pickle.load(fp)
	path = random.choice(musicPathsArray)
	extension = os.path.splitext(path)[1]
	audioFile = AudioSegment.from_file(path, extension[1:])
	startPos = random.randint(1, len(audioFile))
	endPos = random.randint(startPos, min(len(audioFile), startPos + (10 * 1000)))
	truncAudio = audioFile[startPos:endPos]
	print("Got a track object of: " + str(path) + " with length: " + str(len(truncAudio)))
	return truncAudio

def default_track():
	path = r"D:\Torrents\Music\Others\Scott Walker\Scott Walker - Scott 3  1969\05 - We Came Through.flac"
	extension = os.path.splitext(path)[1]
	audioFile = AudioSegment.from_file(path, extension[1:])
	startPos = 1
	endPos = 10000
	return audioFile[startPos:endPos]

def doall(track):
	track = repeat(track)
	track = shuffle(track)
	track = overlay(track)
	track = fade(track)
	track = gain(track)
	track = rev(track)
	track = pann(track)
	track = invert(track)
	track = quality(track)
	track = speed(track)
	return track

def testall():
	try:
		play(doall(random_track()))
	except:
		play(doall(default_track()))