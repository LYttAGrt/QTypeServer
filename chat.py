from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QLabel, QHBoxLayout, \
    QApplication, QTextEdit, QPushButton, QListWidgetItem
import socket
import pickle
from threading import Thread


class Message(QWidget):
    def __init__(self, sender, message):
        super(Message, self).__init__()
        self.vbox = QVBoxLayout()
        self.name = QLabel()
        self.name.setText(sender)
        self.msg = QLabel()
        self.msg.setText(message)
        self.vbox.addWidget(self.name)
        self.vbox.addWidget(self.msg)
        self.name.setLineWidth(1.2)
        self.setLayout(self.vbox)


class Chat(QWidget):
    def __init__(self):
        super(Chat, self).__init__()
        self.port = 20000
        self.addr = ""
        self.name = ""
        self.server = Thread(target=self.start_server, args=[self.port])
        self.server.start()
        self.client = None
        # self.name = name
        self.vbox = QVBoxLayout()
        self.messages = QListWidget()
        self.vbox.addWidget(self.messages)
        self.hbox = QHBoxLayout()
        self.vbox.addLayout(self.hbox)
        self.text_input = QTextEdit()
        self.hbox.addWidget(self.text_input)
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(lambda checked: self.send_msg())
        self.hbox.addWidget(self.send_btn)
        self.setLayout(self.vbox)

    def set_name(self, name):
        self.name = name

    def set_addr(self, addr):
        self.addr = addr

    def start_server(self, port):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('', port))
        server.listen(5)
        print(port, 'SRV', server)
        sock, addr = server.accept()
        while True:  # while True:
            name = pickle.loads(sock.recv(1024))
            sock.send(pickle.dumps(0))
            msg = pickle.loads(sock.recv(1024))
            sock.send(pickle.dumps(0))
            self.messages.addItem("[{}]: {}".format(name, msg))

    def start_client(self):
        input("Launch client?")
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect((self.addr, self.port))
        except ConnectionError as e:
            print(e)
        finally:
            return

    def send_msg(self):
        msg = self.text_input.toPlainText()
        self.text_input.setText("")
        self.client.send(pickle.dumps(self.name))
        self.client.recv(1024)
        self.client.send(pickle.dumps(msg))
        self.client.recv(1024)
        self.messages.addItem("[{}]: {}".format(self.name, msg))


if __name__ == '__main__':
    app = QApplication([])
    chat = Chat()
    chat.set_addr("")
    chat.set_name("Dapimex")
    chat.start_client()
    chat.show()
    app.exec_()
