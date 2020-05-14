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
    def __init__(self, addr, port, name, self_port=10005):
        super(Chat, self).__init__()
        self.server = Thread(target=self.start_server, args=[self_port])
        self.server.start()
        self.client = self.start_client(addr, port)
        self.name = name
        self.vbox = QVBoxLayout()
        self.messages = QListWidget()
        text = "[{}]: {}".format("Dapimex", "Hello")
        msg = QListWidgetItem(text)
        self.messages.addItem(msg)
        # msg_widget = Message(sender="Dapimex", message="Hello")
        # self.messages.setItemWidget(msg, msg_widget)
        self.vbox.addWidget(self.messages)
        self.hbox = QHBoxLayout()
        self.vbox.addLayout(self.hbox)
        self.text_input = QTextEdit()
        self.hbox.addWidget(self.text_input)
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(lambda checked: self.send_msg())
        self.hbox.addWidget(self.send_btn)
        self.setLayout(self.vbox)



    def start_server(self, port):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('', port))
        server.listen(5)
        print(port, 'SRV', server)
        while True:  # while True:
            sock, addr = server.accept()
            name = pickle.loads(sock.recv(1024))
            sock.send(pickle.dumps(0))
            msg = pickle.loads(sock.recv(1024))
            self.messages.addItem("[{}]: {}".format(name, msg))


    def start_client(self, addr, port):
        input("Launch client?")
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client.connect((addr, port))
        except ConnectionError as e:
            print(e)
        finally:
            return client

    def send_msg(self):
        msg = self.text_input.toPlainText()
        self.client.send(pickle.dumps(self.name))
        self.client.recv(1024)
        self.client.send(pickle.dumps(msg))
        self.messages.addItem("[{}]: {}".format(self.name, msg))


if __name__ == '__main__':
    app = QApplication([])
    chat = Chat(addr='', port=10006, name="Alex", self_port=10005)
    chat.show()
    app.exec_()
