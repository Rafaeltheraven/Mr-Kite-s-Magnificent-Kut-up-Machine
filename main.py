from pydub import AudioSegment
from pydub.playback import play
from pydub.effects import speedup
from time import sleep
import pickle
import random
import os
import fleep
from threading import Thread
from PyQt5 import QtCore

class SnipSnap(QtCore.QObject):

	NoMusicFoundSignal = QtCore.pyqtSignal()
	MissingDependencySignal = QtCore.pyqtSignal()

	def __init__(self):
		QtCore.QObject.__init__(self)
		self.musicPathsArray = []
		self.probArray = []
		self.audioFileBuffer = []
		self.clip_duration = 10
		self.playing = True
		self.resultFile = ""
		self.resultAudioObject = AudioSegment.empty()

	def playAudio(self, GUI):
		i = 0
		while self.playing:
			if (len(self.audioFileBuffer) - i < 5):
				print("More buffer")
				bufferThread = Thread(target=self.prepareNextTrackLooped, args=(5,))
				bufferThread.start()
			print("Playing next track")
			play(self.audioFileBuffer[i])
			if self.resultFile != "":
				self.resultAudioObject += self.audioFileBuffer[i]
			i += 1
		if self.resultFile != "":
			GUI.playLabel.setText("Writing to disk...")
			self.writeToDisk()
		GUI.playLabel.setText("Stopped")

	def writeToDisk(self):
		fileFormat = os.path.splitext(self.resultFile)[1]
		self.resultAudioObject.export(r'' + self.resultFile, format=fileFormat[1:])

	def readFiles(self, folderPath):
		result = []
		print("Path is: " + folderPath)
		for root, dirs, files in os.walk(folderPath):
			for file in files:
				absolPath = os.path.join(root, file)
				try:
					with open(absolPath, "rb") as f:
						fleepInfo = fleep.get(f.read(128))
					if (fleepInfo.type_matches("audio")):
						print("Found audio: " + absolPath)
						result.append(absolPath)
				except:
					print("got some error for this file: " + absolPath)
		return result

	def prepareNextTrack(self):
		trackNum = random.randint(0, len(self.musicPathsArray) - 1)
		filePath = self.musicPathsArray[trackNum]
		extension = os.path.splitext(filePath)[1]
		try:
			audioFile = AudioSegment.from_file(filePath, extension[1:])
		except FileNotFoundError:
			self.MissingDependencySignal.emit()
		startPos = random.randint(1, len(audioFile))
		endPos = random.randint(startPos, min(len(audioFile), startPos + (self.clip_duration * 1000)))
		truncAudio = audioFile[startPos:endPos]
		print("Adding: " + filePath + " to buffer with length: " + str(endPos - startPos))
		resultAudio = self.applyEffects(truncAudio)
		return resultAudio

	def prepareNextTrackLooped(self, buffer):
		i = 0
		while (i < buffer):
			self.audioFileBuffer.append(self.prepareNextTrack())
			i += 1

	def applyEffects(self, track):
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
			overlayTrack = self.prepareNextTrack()
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
		if random.randint(0, 101) < self.probArray[9] and len(track) > 150:
			print("adding speed effect")
			speed = round(random.uniform(1, 2), 2)
			print("speed: " + str(speed))
			track = speedup(track, playback_speed=speed)
		return track


	def start(self, MUSIC_FOLDER, rescan, probabilities, segmentDuration, resultFile, GUI):
		GUI.playLabel.setText("Scanning...")
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
		GUI.playLabel.setText("Preparing...")
		self.prepareNextTrackLooped(5)
		GUI.playLabel.setText("Playing")
		playerThread = Thread(target=self.playAudio, args=(GUI, ))
		playerThread.start()

	def stop(self):
		self.playing = False