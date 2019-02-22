import sys
from PyQt5.QtWidgets import QApplication, QWidget, QToolTip, QPushButton, QAction, QFileDialog, QDesktopWidget, QMessageBox, QVBoxLayout, QLabel, QCheckBox, QGridLayout, QSlider
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt
from main import SnipSnap
import pickle
from os.path import isfile, expanduser
from threading import Thread
from functools import partial

# Standard Probabilities
repeatProb = 5
shuffleProb = 10
overlayProb = 10
fadeProb = 30
gainProb = 10
reverseProb = 20
panProb = 5
invertPhaseProb = 10
lowerQualityProb = 5
speedProb = 20

class GUI(QWidget):

	# Initialize GUI
	def __init__(self):
		super().__init__()

		# Check if we saved the musicDirectory somewhere before
		if isfile("musicDirectory"):
			# If we did, open it and set it as the directory
			with open('musicDirectory', 'rb') as fp:
				self.directory = pickle.load(fp)
				self.originalDirectory = self.directory
		else:
			# If we didn't, set directory as empty
			self.directory = ""
			self.originalDirectory = ""
		# Should we rescan the music directory?
		self.rescan = False
		# Where should we save the resulting audio (leave empty to not save)
		self.resultFile = ""
		# Actual player object
		self.snip = SnipSnap()
		# Initial array that contains all the labels used
		self.labels = []
		# Initialize the Signals to communicate between player and UI
		self.snip.NoMusicFoundSignal.connect(self.noMusicWarning)
		self.snip.MissingDependencySignal.connect(self.dependencyWarning)
		self.snip.ChangeLabelSignal.connect(self.changeState)
		# Create UI objects
		self.initUI()

	def initUI(self):

		# Set font
		QToolTip.setFont(QFont('SansSerif', 10))

		# Create buttons
		btn1 = QPushButton('Start', self)
		btn1.setToolTip('Press to activate the machine')
		btn1.resize(btn1.sizeHint())
		# btn.move(95, 30)

		btn2 = QPushButton('Music Folder', self)
		# btn2.move(95, 70)
		btn2.setToolTip('Select your music folder. Neccessary for the program to work.')
		btn2.resize(btn2.sizeHint())

		btn3 = QPushButton('Stop', self)
		# btn3.move(95, 110)
		btn3.setToolTip('Press to stop the machine, a bit of time is required to cool down.')
		btn3.resize(btn3.sizeHint())

		# Connect buttons to functions
		btn1.clicked.connect(self.startMachine)
		btn2.clicked.connect(self.fileSelect)
		btn3.clicked.connect(self.stopMachine)

		# Checkbox to set rescan value
		checkbox = QCheckBox("Rescan?", self)
		checkbox.stateChanged.connect(self.rescanBox)

		# Extra button to save resulting audio
		btn4 = QPushButton('Save Result', self)
		btn4.setToolTip("Save the resulting audio into a single audio file of your choice.")
		btn4.resize(btn4.sizeHint())

		btn4.clicked.connect(self.resultSelect)

		# Maximum segment duration slider
		self.segmentSlider = QSlider(Qt.Horizontal, self)
		self.segmentSlider.setMinimum(5)
		self.segmentSlider.setMaximum(50)
		self.segmentSlider.setValue(10)
		self.segmentLabel = QLabel("Max Segment Duration: " + str(self.segmentSlider.value()))
		self.segmentDuration = self.segmentSlider.value()

		# Construct labels
		self.dirLabel = QLabel(self.directory)
		self.playLabel = QLabel("Stopped")
		self.dirLabel.setAlignment(Qt.AlignCenter)
		self.playLabel.setAlignment(Qt.AlignCenter)

		# Set layout
		self.layout = QGridLayout()
		self.layout.setSpacing(10)

		# Add all widgets to layout
		self.layout.addWidget(btn2, 1, 0)
		self.layout.addWidget(checkbox, 1, 1)
		self.layout.addWidget(self.dirLabel, 2, 0)
		self.layout.addWidget(btn4, 2, 1)
		self.layout.addWidget(btn1, 3, 0)
		self.layout.addWidget(btn3, 3, 1)
		self.layout.addWidget(self.playLabel, 4, 0, 1, 2)
		self.layout.addWidget(self.segmentSlider, 6, 0)
		self.layout.addWidget(self.segmentLabel, 6, 1)

		# Connect functions for the min-max segment slider
		self.segmentSlider.valueChanged.connect(self.segmentChanged)
		self.segmentSlider.sliderReleased.connect(self.segmentReleased)

		# Generate sliders for all probabilities
		self.generateOptions()

		# Set the layout
		self.setLayout(self.layout)

		# Create the window
		self.resize(250, 150)
		self.center()
		# self.setGeometry(300, 300, 300, 220)
		self.setWindowTitle("Mr Kite's Magnificent Kut-up Machine")

		# Show UI
		self.show()

	# Basic "Move to Center" function
	def center(self):
		qr = self.frameGeometry()
		cp = QDesktopWidget().availableGeometry().center()
		qr.moveCenter(cp)
		self.move(qr.topLeft())

	# File selection function. Used to set Music Directory
	def fileSelect(self):
		# If music directory was already set before
		if self.directory != "":
			# Start in that directory
			startDir = self.directory
		else:
			# Else, start at home dir
			startDir = expanduser("~")
		temp = str(QFileDialog.getExistingDirectory(self, "Select your music directory", startDir))
		# Check if chosen dir wasn't empty
		if temp != "":
			print("Setting directory to: " + temp)
			self.directory = temp
			# Save chose directory to disk
			with open('musicDirectory', 'wb') as fp:
				pickle.dump(temp, fp)
			# Show chose directory on GUI
			self.dirLabel.setText(temp)

	# Similar to above, but for choosing where to save the resulting audiofile.
	def resultSelect(self):
		options = QFileDialog.Options()
		self.resultFile, _ = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()","","All Files (*);;MP3 Files (*.mp3);;FLAC Files (*.flac)", options=options)

	# Start the player
	def startMachine(self):
		print("Gonna start with directory: " + self.directory)
		# If a new directory was chosen, force a rescan
		if self.directory != self.originalDirectory:
			self.rescan = True
		# Check if a directory was actually set
		if self.directory != "":
			# Start a seperate thread to scan the music folder and start the player when it's done.
			self.playLabel.setText("Scanning music folder")
			scannerThread = Thread(target=self.snip.start, args=(self.directory, self.rescan, self.probabilities, self.segmentSlider.value(), self.resultFile,))
			scannerThread.start()
		else:
			QMessageBox.about(self, "Error", "You haven't selected your music directory")

	# Show warning of no files were found in the music directory
	def noMusicWarning(self):
		self.playLabel.setText("ERROR")
		QMessageBox.about(self, "Error", "No audio files were found in: " + self.directory)

	# Show warning if missing dependencies (really only LibAv and FFMPEG) are detected
	def dependencyWarning(self):
		self.stopMachine()
		self.playLabel.setText("ERROR")
		QMessageBox.about(self, "Error", "<b>LibAv</b> nor <b>FFMPEG</b> was correctly installed. Please make sure you have one of those two programs.")


	# When user closes window, stop the player
	def closeEvent(self, event):
		self.snip.stop()
		event.accept()

	# Stop button, stops the player
	def stopMachine(self):
		self.snip.stop()
		self.playLabel.setText("Stopping...")

	# Set rescan value depending on state of rescan checkbox
	def rescanBox(self, state):
		self.rescan = state

	# Generate sliders for all probabilities
	def generateOptions(self):
		# Array of all probability values
		self.probabilities = [repeatProb, shuffleProb, overlayProb, fadeProb, gainProb, reverseProb, panProb, invertPhaseProb, lowerQualityProb, speedProb]
		# Construct base sliders
		repeatSlider = QSlider(Qt.Horizontal, self)
		shuffleSlider = QSlider(Qt.Horizontal, self)
		overlaySlider = QSlider(Qt.Horizontal, self)
		fadeSlider = QSlider(Qt.Horizontal, self)
		gainSlider = QSlider(Qt.Horizontal, self)
		reverseSlider = QSlider(Qt.Horizontal, self)
		panSlider = QSlider(Qt.Horizontal, self)
		invertPhaseSlider = QSlider(Qt.Horizontal, self)
		lowerQualitySlider = QSlider(Qt.Horizontal, self)
		speedSlider = QSlider(Qt.Horizontal, self)
		# Array of base sliders
		self.sliders = [repeatSlider, shuffleSlider, overlaySlider, fadeSlider, gainSlider, reverseSlider, panSlider, invertPhaseSlider, lowerQualitySlider, speedSlider]
		# Names of sliders
		self.names = ["Repeat", "Shuffle", "Overlay", "Fade", "Gain", "Reverse", "Panning", "Phase Invertion", "Quality Ruin", "Speedup"]
		# Construct base labels
		repeatLabel = QLabel("Temp")
		shuffleLabel = QLabel("Temp")
		overlayLabel = QLabel("Temp")
		fadeLabel = QLabel("Temp")
		gainLabel = QLabel("Temp")
		reverseLabel = QLabel("Temp")
		panLabel = QLabel("Temp")
		invertPhaseLabel = QLabel("Temp")
		lowerQualityLabel = QLabel("Temp")
		speedLabel = QLabel("Temp")
		# Array of labels
		self.labels = [repeatLabel, shuffleLabel, overlayLabel, fadeLabel, gainLabel, reverseLabel, panLabel, invertPhaseLabel, lowerQualityLabel, speedLabel]
		i = 0
		# Loop through all sliders
		while i < len(self.sliders):
			# Get slider
			currentSlider = self.sliders[i]
			# Set maximum and minimum values
			currentSlider.setMaximum(100)
			currentSlider.setMinimum(0)
			# Set base probability value
			currentSlider.setValue(self.probabilities[i])
			# Add functions for when the slider is moved to change the label and the probability of that specific effect
			currentSlider.valueChanged.connect(partial(self.probLabel, i))
			currentSlider.sliderReleased.connect(partial(self.setProb, i))
			# Set the label of slider
			currentLabel = self.labels[i]
			currentLabel.setText(self.names[i] + " Probability: " + str(currentSlider.value()))
			# Add slider to layout
			self.layout.addWidget(currentSlider, i + 7, 0)
			self.layout.addWidget(currentLabel, i + 7, 1)
			i += 1

	# Set label of slider
	def probLabel(self, index):
		currentLabel = self.labels[index]
		currentSlider = self.sliders[index]
		currentLabel.setText(self.names[index] + " Probability: " + str(currentSlider.value()))

	# Set probability value given by slider
	def setProb(self, index):
		self.probabilities[index] = self.sliders[index].value()
		
	# Same functions as above, but specifically for the segment duration slider
	def segmentChanged(self):
		self.segmentLabel.setText("Max Segment Duration: " + str(self.segmentSlider.value()))

	def segmentReleased(self):
		self.segmentDuration = self.segmentSlider.value()

	# Set what the state label says (playing, stopping etc.)
	def changeState(self, text):
		self.playLabel.setText(text)

# Main function
if __name__ == '__main__':

	app = QApplication(sys.argv)

	gui = GUI()

	sys.exit(app.exec_())