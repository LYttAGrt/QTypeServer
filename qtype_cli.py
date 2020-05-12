from PyQt5 import QtWidgets, QtMultimedia, Qt, QtGui, QtCore
from threading import Thread
import requests
import socket
import sys


dns_url = "http://52.14.64.130:7000/dns"


class Caller(QtWidgets.QApplication):
    # Define all stuff
    def __init__(self, argv):
        super().__init__(argv)
        self.user_name = str()

        # Register widgets
        self.alias_input = QtWidgets.QLineEdit()
        self.login_btn = QtWidgets.QPushButton()

        # online_users widgets
        self.list_widget = QtWidgets.QListWidget()
        self.logout_btn = QtWidgets.QPushButton()

        # Call widgets
        self.socket_srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        self.socket_cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        self.receiver = Thread(target=self.recv_image, args=())
        self.camera = QtMultimedia.QCamera(QtMultimedia.QCamera.availableDevices()[0])

    def connect_sockets(self, addr, port):
        try:
            self.socket_cli.connect((addr, port))
            self.socket_srv.bind((socket.gethostname(), 16000))
            self.socket_srv.listen(10)
            print('Sockets connected')
            self.camera.start()
            print('Camera started')
        except ConnectionError as e:
            print(e)
        finally:
            return self

    def send_image(self, frame: QtMultimedia.QVideoFrame):
        frame.map(QtMultimedia.QAbstractVideoBuffer.ReadOnly)
        data = bytes(frame.bits())
        sizes = list(range(0, len(data), 4096*16)) + [len(data)]
        print("Sending frames:", sizes)
        # split by chunks
        for i in range(len(sizes) - 1):
            self.socket_cli.send(data[sizes[i]:sizes[i+1]])

    def recv_image(self):
        while True:
            print("Receiving started")
            conn, addr = self.socket_srv.accept()
            print(f"{conn} recv from: {addr}")
            data = conn.recv(4096*16)
            print(data)

    # REGISTER PAGE
    def register_ui(self, window: QtWidgets.QMainWindow, window_size: tuple):
        window.resize(*window_size)

        self.alias_input.setParent(window)
        self.alias_input.setGeometry(0, int(window.height() / 2), window.width(), 40)
        self.alias_input.setPlaceholderText("Type your alias")
        self.login_btn.setParent(window)
        self.login_btn.setGeometry(0, int(window.height() * 2 / 3), window.width(), 50)
        self.login_btn.setText("Register!")

    # USERS LIST PAGE
    def userlist_ui(self, window: QtWidgets.QMainWindow, window_size: tuple):
        window.resize(*window_size)
        self.list_widget.setParent(window)
        self.list_widget.setGeometry(0, 0, window.width(), int(window.height() * 7 / 8))
        self.logout_btn.setParent(window)
        self.logout_btn.setText("Log out!")
        self.logout_btn.setGeometry(0, int(window.height() * 7 / 8), window.width(), int(window.height() / 8))

        # users = requests.get(url + "/list")
        users = ["Den", "Alex", "Misha", "Danya", "Danis"]

        for i in range(len(users)):
            item = QtWidgets.QListWidgetItem(users[i], self.list_widget)
            btn = QtWidgets.QPushButton(users[i], self.list_widget)
            btn.setGeometry(0, 100 * i + 20, self.list_widget.width(), 100)
            btn.clicked.connect(lambda checked: self.switch_list_to_call(btn.text()))
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, btn)
        print(f"Found {len(users)} users")

    # CALLS PAGE
    def callpage_ui(self, window: QtWidgets.QMainWindow, window_size: tuple):
        window.setObjectName("MainWindow")
        window.resize(*window_size)

        self.video_probe = QtMultimedia.QVideoProbe(window)
        self.view_finder = Qt.QCameraViewfinder(window)
        self.recorder = QtMultimedia.QMediaRecorder(self.camera)

        self.camera.setParent(window)
        self.camera.setViewfinder(self.view_finder)
        self.camera.setCaptureMode(Qt.QCamera.CaptureStillImage)

        self.video_probe.setSource(self.recorder)
        self.video_probe.videoFrameProbed.connect(self.send_image)

        self.view_finder.setParent(window)
        self.view_finder.setGeometry(0, 0, int(window_size[0] / 2), int(window_size[1]*8/9))

        self.client_view = Qt.QLabel(window)
        self.client_view.setGeometry(int(window_size[0] / 2), 0, int(window_size[0] / 2), int(window_size[1]*8/9))
        self.client_view.setStyleSheet("background-color: grey")

        self.end_call_btn = QtWidgets.QPushButton()
        self.end_call_btn.setParent(window)
        self.end_call_btn.setText("End call")
        self.end_call_btn.setGeometry(0, int(window_size[1] * 8 / 9), window_size[0], int(window_size[1] / 9))

    # Creates 3 filled up windows
    def switch_regi_to_list(self):
        self.user_name = self.alias_input.text()
        res = requests.get(dns_url + f"/register?alias={self.user_name}&status=true")
        if res.status_code != 200:
            self.alias_input.setPlaceholderText("Something went wrong!")
        else:
            self.register_window.setVisible(False)
            self.userlist_window.setVisible(True)
            self.callpage_window.setVisible(False)

    def switch_list_to_call(self, callee_alias):
        print(f"{self.user_name} calls to {callee_alias}")
        self.register_window.setVisible(False)
        self.userlist_window.setVisible(False)
        self.callpage_window.setVisible(True)

    def switch_call_to_list(self):
        self.register_window.setVisible(False)
        self.userlist_window.setVisible(True)
        self.callpage_window.setVisible(False)

    def switch_list_to_regi(self):
        res = requests.get(dns_url + f"/register?alias={self.user_name}&status=false")
        if res.status_code == 200:
            self.register_window.setVisible(True)
            self.userlist_window.setVisible(False)
            self.callpage_window.setVisible(False)
        else:
            print("Logging out failed!")

    def generate_windows(self):
        stacked_widget = QtWidgets.QStackedWidget()

        self.register_window = QtWidgets.QMainWindow()
        self.register_ui(self.register_window, (720, 540))
        self.login_btn.clicked.connect(self.switch_regi_to_list)

        self.userlist_window = QtWidgets.QMainWindow()
        self.userlist_ui(self.userlist_window, (720, 540))
        self.logout_btn.clicked.connect(self.switch_list_to_regi)

        self.callpage_window = QtWidgets.QMainWindow()
        self.callpage_ui(self.callpage_window, (720, 540))
        self.end_call_btn.clicked.connect(self.switch_call_to_list)

        stacked_widget.addWidget(self.register_window)
        stacked_widget.addWidget(self.userlist_window)
        stacked_widget.addWidget(self.callpage_window)

        self.register_window.setVisible(True)
        self.userlist_window.setVisible(False)
        self.callpage_window.setVisible(False)
        return stacked_widget


if __name__ == '__main__':
    app = Caller(sys.argv)
    main_window = app.generate_windows()
    main_window.resize(720, 540)
    main_window.show()
    sys.exit(app.exec_())
