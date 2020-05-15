from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QLabel, QHBoxLayout, \
    QApplication, QTextEdit, QPushButton, QListWidgetItem
from PyQt5 import QtMultimedia
from PyQt5.QtCore import QByteArray, QBuffer
import socket
import pickle
from threading import Thread


class AudioHandle(QWidget):
    def __init__(self, addr, port, self_port=10005):
        super(AudioHandle, self).__init__()
        self.recorder = QtMultimedia.QAudioRecorder()
        # self.recorder.setContainerFormat(self.recorder.supportedContainers()[1])
        # print(self.recorder.supportedAudioCodecs())
        # print(self.recorder.containerFormat())
        self.settings = QtMultimedia.QAudioEncoderSettings()
        self.settings.setCodec("audio/mpeg")

        self.settings.setBitRate(8)
        self.settings.setSampleRate(44100)
        self.settings.setChannelCount(2)
        self.settings.setQuality(QtMultimedia.QMultimedia.NormalQuality)
        # self.recorder.setAudioSettings(self.settings)

        self.client = self.start_client(addr, port)

        self.audioprobe = QtMultimedia.QAudioProbe()
        self.audioprobe.setSource(self.recorder)
        self.audioprobe.audioBufferProbed.connect(self.send_audio)
        # self.output = QtMultimedia.QAudioOutput()
        # self.buffer = QBuffer()
        # self.recorder.setOutputLocation(self.buffer)
        self.recorder.record()
        # self.output.start(self.buffer)

    def send_audio(self, buf: QtMultimedia.QAudioBuffer):
        data = buf.data().asarray(buf.byteCount())
        data = QByteArray.fromRawData(data)
        self.client.send(pickle.dumps(data))
        self.client.recv(1024)

    def start_client(self, addr, port):
        input("Launch client?")

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client.connect((addr, port))
        except ConnectionError as e:
            print(e)
        finally:
            return client



if __name__ == '__main__':
    app = QApplication([])
    chat = AudioHandle(addr='', port=10006, self_port=10005)
    chat.show()
    app.exec_()
