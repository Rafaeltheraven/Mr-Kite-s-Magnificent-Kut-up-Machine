import sys
from PyQt5.QtWidgets import QApplication, QWidget, QToolTip, QPushButton, QAction, QFileDialog, QDesktopWidget, QMessageBox, QVBoxLayout, QLabel, QCheckBox, QGridLayout, QSlider
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt
from main import SnipSnap
import pickle
from os.path import isfile, expanduser
from threading import Thread


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

	def __init__(self):
		super().__init__()

		if isfile("musicDirectory"):
			with open('musicDirectory', 'rb') as fp:
				self.directory = pickle.load(fp)
				self.originalDirectory = self.directory
		else:
			self.directory = ""
			self.originalDirectory = ""
		self.rescan = False
		self.resultFile = ""
		self.snip = SnipSnap()
		self.snip.NoMusicFoundSignal.connect(self.noMusicWarning)
		self.snip.MissingDependencySignal.connect(self.dependencyWarning)
		self.initUI()

	def initUI(self):

		QToolTip.setFont(QFont('SansSerif', 10))

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

		btn1.clicked.connect(self.startMachine)
		btn2.clicked.connect(self.fileSelect)
		btn3.clicked.connect(self.stopMachine)

		checkbox = QCheckBox("Rescan?", self)
		checkbox.stateChanged.connect(self.rescanBox)

		btn4 = QPushButton('Save Result', self)
		btn4.setToolTip("Save the resulting audio into a single audio file of your choice.")
		btn4.resize(btn4.sizeHint())

		btn4.clicked.connect(self.resultSelect)

		self.segmentSlider = QSlider(Qt.Horizontal, self)
		self.segmentSlider.setMinimum(5)
		self.segmentSlider.setMaximum(50)
		self.segmentSlider.setValue(10)
		self.segmentLabel = QLabel("Max Segment Duration: " + str(self.segmentSlider.value()))
		self.segmentDuration = self.segmentSlider.value()

		# layout = QVBoxLayout()
		self.dirLabel = QLabel(self.directory)
		self.playLabel = QLabel("Stopped")
		self.dirLabel.setAlignment(Qt.AlignCenter)
		self.playLabel.setAlignment(Qt.AlignCenter)

		self.layout = QGridLayout()
		self.layout.setSpacing(10)

		self.layout.addWidget(btn2, 1, 0)
		self.layout.addWidget(checkbox, 1, 1)
		self.layout.addWidget(self.dirLabel, 2, 0)
		self.layout.addWidget(btn4, 2, 1)
		self.layout.addWidget(btn1, 3, 0)
		self.layout.addWidget(btn3, 3, 1)
		self.layout.addWidget(self.playLabel, 4, 0, 1, 2)
		self.layout.addWidget(self.segmentSlider, 6, 0)
		self.layout.addWidget(self.segmentLabel, 6, 1)

		self.segmentSlider.valueChanged.connect(self.segmentChanged)
		self.segmentSlider.sliderReleased.connect(self.segmentReleased)

		self.generateOptions()

		self.setLayout(self.layout)

		self.resize(250, 150)
		self.center()
		# self.setGeometry(300, 300, 300, 220)
		self.setWindowTitle("Mr Kite's Magnificent Kut-up Machine")

		self.show()

	def center(self):
		qr = self.frameGeometry()
		cp = QDesktopWidget().availableGeometry().center()
		qr.moveCenter(cp)
		self.move(qr.topLeft())

	def fileSelect(self):
		if self.directory != "":
			startDir = self.directory
		else:
			startDir = expanduser("~")
		temp = str(QFileDialog.getExistingDirectory(self, "Select your music directory", startDir))
		if temp != "":
			print("Setting directory to: " + temp)
			self.directory = temp
			with open('musicDirectory', 'wb') as fp:
				pickle.dump(temp, fp)
			self.dirLabel.setText(temp)

	def resultSelect(self):
		options = QFileDialog.Options()
		self.resultFile, _ = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()","","All Files (*);;MP3 Files (*.mp3);;FLAC Files (*.flac)", options=options)


	def startMachine(self):
		print("Gonna start with directory: " + self.directory)
		if self.directory != self.originalDirectory:
			self.rescan = True
		if self.directory != "":
			self.playLabel.setText("Scanning music folder")
			scannerThread = Thread(target=self.snip.start, args=(self.directory, self.rescan, self.probabilities, self.segmentSlider.value(), self.resultFile, self,))
			scannerThread.start()
		else:
			QMessageBox.about(self, "Error", "You haven't selected your music directory")

	def noMusicWarning(self):
		self.playLabel.setText("ERROR")
		QMessageBox.about(self, "Error", "No audio files were found in: " + self.directory)

	def dependencyWarning(self):
		self.stopMachine()
		self.playLabel.setText("ERROR")
		QMessageBox.about(self, "Error", "<b>LibAv</b> nor <b>FFMPEG</b> was correctly installed. Please make sure you have one of those two programs.")


	def closeEvent(self, event):
		self.snip.stop()
		event.accept()

	def stopMachine(self):
		self.snip.stop()
		self.playLabel.setText("Stopping...")

	def rescanBox(self, state):
		self.rescan = state

	def generateOptions(self):
		self.probabilities = [repeatProb, shuffleProb, overlayProb, fadeProb, gainProb, reverseProb, panProb, invertPhaseProb, lowerQualityProb, speedProb]
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
		self.sliders = [repeatSlider, shuffleSlider, overlaySlider, fadeSlider, gainSlider, reverseSlider, panSlider, invertPhaseSlider, lowerQualitySlider, speedSlider]
		self.names = ["Repeat", "Shuffle", "Overlay", "Fade", "Gain", "Reverse", "Panning", "Phase Invertion", "Quality Ruin", "Speedup"]
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
		self.labels = [repeatLabel, shuffleLabel, overlayLabel, fadeLabel, gainLabel, reverseLabel, panLabel, invertPhaseLabel, lowerQualityLabel, speedLabel]
		i = 0
		while i < len(self.sliders):
			currentSlider = self.sliders[i]
			currentSlider.setMaximum(100)
			currentSlider.setMinimum(0)
			currentSlider.setValue(self.probabilities[i])
			currentSlider.valueChanged.connect(lambda: self.probLabel(i))
			currentSlider.sliderReleased.connect(lambda: self.setProb(i))
			currentLabel = self.labels[i]
			currentLabel.setText(self.names[i] + " Probability: " + str(currentSlider.value()))
			self.layout.addWidget(currentSlider, i + 7, 0)
			self.layout.addWidget(currentLabel, i + 7, 1)
			i += 1


	def probLabel(self, index):
		currentLabel = self.labels[index]
		currentSlider = self.sliders[index]
		currentLabel.setText(self.names[index] + " Probability: " + str(currentSlider.value()))

	def setProb(self, index):
		probabilities[index] = self.sliders[index].value()
		
	def segmentChanged(self):
		self.segmentLabel.setText("Max Segment Duration: " + str(self.segmentSlider.value()))

	def segmentReleased(self):
		self.segmentDuration = self.segmentSlider.value()

if __name__ == '__main__':

	app = QApplication(sys.argv)

	gui = GUI()
	sys.exit(app.exec_())