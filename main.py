from pydub import AudioSegment
from pydub.playback import play
from pydub.effects import speedup
from time import sleep
import eyed3
import mutagen
import pickle
import random
import os
import fleep
from threading import Thread, Timer
from PyQt5 import QtCore

# Object used to control the player
class SnipSnap(QtCore.QObject):

	# Signals to communicate with GUI
	NoMusicFoundSignal = QtCore.pyqtSignal()
	MissingDependencySignal = QtCore.pyqtSignal()
	ChangeLabelSignal = QtCore.pyqtSignal(object)

	# Initialize object
	def __init__(self):
		QtCore.QObject.__init__(self)
		# Array contains absolute paths to every audio file found
		self.musicPathsArray = []
		# Array containing probabilities for all effects
		self.probArray = []
		# Buffer for smoother transitioning between audio segments
		self.audioFileBuffer = []
		# Max duration of audio segment
		self.clip_duration = 10
		# Boolean to check if we should continue playing
		self.playing = True
		# Where to save resulting audio file
		self.resultFile = ""
		# Initialize result audio object
		self.resultAudioObject = AudioSegment.empty()
		# Pointer to pick which file in the buffer to play
		self.bufferPointer = 0

	# Function that plays audio
	def playAudio(self):
		# Check if we should actually be playing
		if self.playing:
			# Check if we need to add some files to buffer (just to be sure)
			if (len(self.audioFileBuffer) - self.bufferPointer < 5):
				print("More buffer")
				# Create thread to add 5 new segments to buffer
				bufferThread = Thread(target=self.prepareNextTrackLooped, args=(5,))
				# Start thread
				bufferThread.start()
			# Get audio object, and name of track from the buffer
			audioFile, title = self.audioFileBuffer[self.bufferPointer]
			# Increment pointer
			self.bufferPointer += 1
			# Start a new thread to start playing a new audio object 2 seconds before this one ends (for smoother transitions).
			newThread = Timer((len(audioFile) - 200) / 1000, self.playAudio)
			newThread.start()
			print("Playing next track")
			# Set status label to show what track(s) we are playing
			self.ChangeLabelSignal.emit("Playing: " + title)
			# Actually play the segment
			play(audioFile)
			# When done
			if self.resultFile != "":
				# If we want to save the audio, append segment to result audio object
				self.resultAudioObject += audioFile
		# If we should no longer be playing audio
		if not self.playing:
			# Check if users wants to save audio
			if self.resultFile != "":
				# If they do, notify the user that you are writing to disk
				self.ChangeLabelSignal.emit("Writing to disk...")
				# And write to disk
				self.writeToDisk()
			# Tell user the player has stopped.
			self.ChangeLabelSignal.emit("Stopped")

	# Write result audio to file
	def writeToDisk(self):
		# Check what file format to write to
		fileFormat = os.path.splitext(self.resultFile)[1]
		# And write the file
		self.resultAudioObject.export(r'' + self.resultFile, format=fileFormat[1:])

	# Find all audio files in given path
	def readFiles(self, folderPath):
		# Array holding all the paths
		result = []
		print("Path is: " + folderPath)
		# Recursively walk through folders
		for root, dirs, files in os.walk(folderPath):
			for file in files:
				# Get the absolute path
				absolPath = os.path.join(root, file)
				try:
					# Check whether the file is an audio file
					with open(absolPath, "rb") as f:
						fleepInfo = fleep.get(f.read(128))
					# If it is
					if (fleepInfo.type_matches("audio")):
						print("Found audio: " + absolPath)
						# Add to result array
						result.append(absolPath)
				except:
					# Check for potential errors
					print("got some error for this file: " + absolPath)
		# Return array with all paths.
		return result

	# Prepare a track to add to the buffer.
	def prepareNextTrack(self):
		# Get a random track from the list of audio files
		trackNum = random.randint(0, len(self.musicPathsArray) - 1)
		# Get it's file path
		filePath = self.musicPathsArray[trackNum]
		# Get it's extension
		extension = os.path.splitext(filePath)[1]
		# Depending on mp3 or other, get the title of the track through either eyed3 or mutagen
		if extension == ".mp3":
			title = eyed3.load(filePath).tag.title
		else:
			title = mutagen.File(filePath)['title'][0]
		# Try loading the file as a pydub object
		try:
			audioFile = AudioSegment.from_file(filePath, extension[1:])
		except FileNotFoundError:
			# If we fail, we're probably missing FFMPEG/LibAv
			self.MissingDependencySignal.emit()
		startPos = random.randint(1, len(audioFile))
		endPos = random.randint(startPos, min(len(audioFile), startPos + (self.clip_duration * 1000)))
		truncAudio = audioFile[startPos:endPos]
		print("Adding: " + filePath + " to buffer with length: " + str(endPos - startPos))
		resultAudio, title = self.applyEffects(truncAudio, title)
		return [resultAudio, title]

	def prepareNextTrackLooped(self, buffer):
		i = 0
		while (i < buffer):
			self.audioFileBuffer.append(self.prepareNextTrack())
			i += 1

	def applyEffects(self, track, title):
		if random.randint(0, 101) < self.probArray[0]:
			track = track * random.randint(2, 5)
			print("added repeat effect")
		if random.randint(0, 101) < self.probArray[1]:
			print("Doing shuffle")
			splitted = track[::1000]
			splitList = list(splitted)
			random.shuffle(splitList)
			result = AudioSegment.empty()
			for segment in splitList:
				result += segment
			track = result
			# random.shuffle(splitted)
			# track = splitted
		if random.randint(0, 101) < self.probArray[2]:
			print("adding overlay effect")
			overlayTrack, new_title = self.prepareNextTrack()
			title = title + " + " + new_title  
			loop = bool(random.getrandbits(1))
			position = random.randint(0, len(track))
			gain = random.randint(-8, 9)
			track = track.overlay(overlayTrack, position=position, loop=loop, gain_during_overlay=gain)
		if random.randint(0, 101) < self.probArray[3]:
			print("adding fade effect")
			fromGain = round(random.uniform(-8, 0), 2)
			toGain = round(random.uniform(0.1, 10), 2)
			start = random.randint(0, len(track))
			end = random.randint(start, len(track) + 1)
			track = track.fade(to_gain=toGain, from_gain=fromGain, start=start, end=end)
		if random.randint(0, 101) < self.probArray[4]:
			print("adding gain effect")
			gain = round(random.uniform(-20, 21), 2)
			track = track + gain
		if random.randint(0, 101) < self.probArray[5]:
			print("adding reverse effect")
			track = track.reverse()
		if random.randint(0, 101) < self.probArray[6]:
			print("adding pan effect")
			pan = round(random.uniform(-1.0, 1.1), 2)
			track = track.pan(pan)
		if random.randint(0, 101) < self.probArray[7]:
			print("adding invert phase effect")
			track = track.invert_phase()
		if random.randint(0, 101) < self.probArray[8]:
			#Look into this later
			print("should be doing lower quality")
			track.set_sample_width(1)
			track.set_channels(1)
			track.set_frame_rate(11025)
		if random.randint(0, 101) < self.probArray[9] and len(track) > 150:
			print("adding speed effect")
			speed = round(random.uniform(1, 2), 2)
			print("speed: " + str(speed))
			track = speedup(track, playback_speed=speed)
		return track, title


	def start(self, MUSIC_FOLDER, rescan, probabilities, segmentDuration, resultFile):
		self.ChangeLabelSignal.emit("Scanning...")
		self.audioFileBuffer = []
		self.resultAudioObject = AudioSegment.empty()
		self.playing = True
		self.clip_duration = segmentDuration
		self.probArray = probabilities
		self.resultFile = resultFile
		print("Scanning: " + MUSIC_FOLDER)
		if rescan or not os.path.isfile('fileNames'):
			self.musicPathsArray = self.readFiles(MUSIC_FOLDER)
			with open('fileNames', 'wb') as fp:
				pickle.dump(self.musicPathsArray, fp)
		else:
			with open('fileNames', 'rb') as fp:
				self.musicPathsArray = pickle.load(fp)

		if len(self.musicPathsArray) == 0 and not rescan:
			self.musicPathsArray = self.readFiles(MUSIC_FOLDER)
			with open('fileNames', 'wb') as fp:
				pickle.dump(self.musicPathsArray, fp)
		elif len(self.musicPathsArray) == 0:
			self.NoMusicFoundSignal.emit()
		self.ChangeLabelSignal.emit("Preparing...")
		self.prepareNextTrackLooped(5)
		self.ChangeLabelSignal.emit("Playing")
		self.playAudio()

	def stop(self):
		self.playing = False
		self.bufferPointer = 0