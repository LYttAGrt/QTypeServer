from PyQt5 import QtWidgets, QtMultimedia, Qt, QtCore
from threading import Thread
import requests
import socket
from scipy import ndimage
import pickle
import json
import numpy as np


# Works with DNS
class DNSConnecter:
    def __init__(self, dns_url="http://52.14.64.130:7000/dns", port=20000):
        self.url = dns_url
        self.user_name = str()
        self.port = int() if port is None else port

    # Log in & log out
    def register_user(self, status: str) -> int:
        try:
            res = requests.get(self.url + f"/register?alias={self.user_name}&status={status}&port={self.port}")
            return res.status_code
        except Exception as e:
            print(e)
            return 500

    def list_users(self):
        res = requests.get(self.url + f"/list")
        data: dict = json.loads(res.content)
        return data

    # TODO
    def call(self, other_alias):
        res = requests.get(self.url + f"/call?alias={self.user_name}&other_alias={other_alias}")
        res = json.loads(res.content)
        return res

    def free(self) -> int:
        res = requests.get(self.url + f"/free?alias={self.user_name}")
        return res.status_code


class MThread(QtCore.QThread):
    def __init__(self, parent=None, func=None):
        super().__init__(parent)
        self.func: callable = func

    def run(self) -> None:
        if self.func is not None:
            self.func.__call__()


class QtypeDemo(QtWidgets.QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.connecter = DNSConnecter()
        self.window = QtWidgets.QMainWindow()
        # Define all widgets
        self.graphics_view = QtWidgets.QGraphicsView(self.window)
        self.view_finder = Qt.QCameraViewfinder(self.window)
        self.chat_widget = QtWidgets.QListWidget(self.window)
        self.text_input = QtWidgets.QLineEdit("Input your text", self.window)
        self.name_input = QtWidgets.QLineEdit("Input your name", self.window)
        self.addr_input = QtWidgets.QLineEdit("192.168.1.", self.window)
        self.exit_btn = QtWidgets.QPushButton("Exit demo", self.window)
        self.send_msg_btn = QtWidgets.QPushButton("Send", self.window)
        self.conn_btn = QtWidgets.QPushButton("Connect", self.window)
        self.clear_btn = QtWidgets.QPushButton("Clear chat", self.window)
        self.camera_btn = QtWidgets.QPushButton("Camera", self.window)

        self.camera = QtMultimedia.QCamera(QtMultimedia.QCamera.availableDevices()[0])
        self.viewfinder_settings = Qt.QCameraViewfinderSettings()
        self.viewfinder_settings.setResolution(640, 480)
        self.video_probe = QtMultimedia.QVideoProbe()
        self.graphics_scene = QtWidgets.QGraphicsScene()
        self.camera.setViewfinderSettings(self.viewfinder_settings)
        self.camera.setViewfinder(self.view_finder)
        self.camera.setCaptureMode(Qt.QCamera.CaptureVideo)
        self.video_probe.setSource(self.camera)

        self.video_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        self.chat_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        self.frame_buffer = Qt.QBuffer()
        self.frame_buffer.open(Qt.QBuffer.ReadWrite)
        self.frame_buffer.bytesWritten.connect(self.redraw)
        self.video_th = MThread(func=self.recv_image) # Thread(target=self.recv_image)
        self.chat_th = MThread(func=self.recv_msg)
        self.video_th.start()
        self.chat_th.start()

    def connect_clients(self):
        # self.connecter.register_user('true')
        try:
            print(f"Connecting to {self.addr_input.text()}:20000")
            self.video_client.connect((self.addr_input.text(), 20000))
            self.chat_client.connect((self.addr_input.text(), 20004))
            # self.camera.start()
        except ConnectionError as e:
            print(e)

    @staticmethod
    def convert_to_rgb(data, pixel_format=19, width=640, height=480) -> np.ndarray:
        # https://maxsharabayko.blogspot.com/2016/01/fast-yuv-to-rgb-conversion-in-python-3.html
        def convertYUVtoRGB(yuv_planes: list, zoom_needed: bool):
            plane_y = yuv_planes[0]
            plane_u = yuv_planes[1]
            plane_v = yuv_planes[2]

            # upsample if YV12, alternativelly can perform upsampling with numpy.repeat()
            plane_u = ndimage.zoom(plane_u, 2, order=0) if zoom_needed else plane_u.repeat(2, axis=0).repeat(2, axis=1)
            plane_v = ndimage.zoom(plane_v, 2, order=0) if zoom_needed else plane_v.repeat(2, axis=0).repeat(2, axis=1)

            # reshape
            plane_y = plane_y.reshape((plane_y.shape[0], plane_y.shape[1], 1))
            plane_u = plane_u.reshape((plane_u.shape[0], plane_u.shape[1], 1))
            plane_v = plane_v.reshape((plane_v.shape[0], plane_v.shape[1], 1))

            # make YUV of shape [height, width, color_plane]
            yuv = np.concatenate((plane_y, plane_u, plane_v), axis=2)

            # according to ITU-R BT.709
            yuv[:, :, 0] = yuv[:, :, 0].clip(16, 235).astype(yuv.dtype) - 16
            yuv[:, :, 1:] = yuv[:, :, 1:].clip(16, 240).astype(yuv.dtype) - 128

            A = np.array([[1.164, 0.000, 1.793],
                          [1.164, -0.213, -0.533],
                          [1.164, 2.112, 0.000]])

            # our result
            return np.dot(yuv, A.T).clip(0, 255).astype('uint8')

        # Convert YV12 to RGB
        if pixel_format == Qt.QVideoFrame.Format_YV12:
            planes = list()
            # Y is data[:x*y]
            planes.append(np.asarray(data[:height * width], dtype=np.uint8).reshape((width, height)))
            # U is data[x*y:x*y*5/4]
            planes.append(np.asarray(data[height * width:int(height * width * 5 / 4)], dtype=np.uint8).reshape(
                (int(width / 2), int(height / 2))))
            # V is data[x*y*5/4:]
            planes.append(np.asarray(data[int(height * width * 5 / 4):], dtype=np.uint8).reshape(
                (int(width / 2), int(height / 2))))
            return convertYUVtoRGB(yuv_planes=planes, zoom_needed=True)

        # Convert YUYV to RGB
        elif pixel_format == Qt.QVideoFrame.Format_YUYV:
            planes = list()
            return convertYUVtoRGB(yuv_planes=planes, zoom_needed=False)

    def window_ui(self, window: QtWidgets.QMainWindow, window_size: tuple = (640, 540)):
        window.resize(*window_size)
        self.graphics_view.setStyleSheet("background-color: grey")

        # Geometry
        self.graphics_view.setGeometry(
            int(0), int(0), int(window_size[0]*2/3), int(window_size[1]*7/9))
        self.view_finder.setGeometry(
            int(int(window_size[0]*2/3)), int(0), int(int(window_size[0]/3)), int(window_size[1]*2/9))
        self.chat_widget.setGeometry(
            int(window_size[0]*2/3), int(window_size[1]*2/9), int(window_size[0]/3), int(window_size[1]*5/9))
        self.exit_btn.setGeometry(
            0, int(window_size[1]*7/9), int(window_size[0]*2/3), int(window_size[1]*1/9))

        self.text_input.setGeometry(
            int(window_size[0]*2/3), int(window_size[1]*7/9), int(window_size[0]*4/9), int(window_size[1]/9))
        self.send_msg_btn.setGeometry(
            int(window_size[0]*16/18), int(window_size[1] * 7 / 9), int(window_size[0]/9), int(window_size[1]/9))
        self.name_input.setGeometry(
            0, int(window_size[1] * 8 / 9), int(window_size[0] / 6), int(window_size[1]/9))
        self.addr_input.setGeometry(
            int(window_size[0] / 6), int(window_size[1]*8/9), int(window_size[0]/2), int(window_size[1]/9))
        self.conn_btn.setGeometry(
            int(window_size[0] / 2), int(window_size[1]*8/9), int(window_size[0]/6), int(window_size[1]/9))
        self.clear_btn.setGeometry(
            int(window_size[0] * 2 / 3), int(window_size[1]*8/9), int(window_size[0] / 6), int(window_size[1]/9))
        self.camera_btn.setGeometry(
            int(window_size[0]*5/6), int(window_size[1] * 8 / 9), int(window_size[0] / 6), int(window_size[1] / 9))

        # Listeners
        self.conn_btn.clicked.connect(self.connect_clients)
        self.clear_btn.clicked.connect(lambda x: self.chat_widget.clear())
        self.camera_btn.clicked.connect(
            lambda x: self.camera.stop() if self.camera.status() == Qt.QCamera.StartingStatus else self.camera.start())
        self.send_msg_btn.clicked.connect(self.send_msg)
        self.exit_btn.clicked.connect(self.closeAllWindows)
        self.video_probe.videoFrameProbed.connect(self.send_image)
        self.graphics_scene.changed.connect(lambda x: self.graphics_view.setScene(self.graphics_scene))

    def send_image(self, frame):
        frame.map(QtMultimedia.QAbstractVideoBuffer.ReadOnly)
        bits_ptr = frame.bits()
        bits_ptr.setsize(frame.mappedBytes())
        bits_ptr = bytes(bits_ptr)
        # print(f"Sending {len(bits_ptr)} bytes")
        # Send it
        self.video_client.send(bits_ptr)

    def redraw(self):
        img = bytes(self.frame_buffer.data())
        img = self.convert_to_rgb([*img])
        self.graphics_scene.clear()
        self.graphics_scene.addPixmap(Qt.QPixmap.fromImage(
            Qt.QImage(img.data, img.shape[0], img.shape[1], img.shape[0] * img.shape[2], Qt.QImage.Format_Indexed8)))
        self.graphics_view.setScene(self.graphics_scene)

    def recv_image(self):
        self.video_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        self.video_server.bind(('', 20000))
        # print(self.video_server)
        self.video_server.listen()
        conn, addr = self.video_server.accept()
        while True:
            bits_ptr = bytes()
            while len(bits_ptr) < 640*720:
                bits_ptr += conn.recv(640*720)
            # print(len(bits_ptr), '-->', end=' ')
            self.frame_buffer.write(bits_ptr[:640*720])
            self.frame_buffer.seek(0)
            bits_ptr = bits_ptr[640*720:]
            # print(len(bits_ptr))

    def send_msg(self):
        msg = self.text_input.text()
        self.text_input.setText("")
        self.chat_client.send(pickle.dumps(self.name_input.text()))
        self.chat_client.recv(1024)
        self.chat_client.send(pickle.dumps(msg))
        self.chat_client.recv(1024)
        self.chat_widget.addItem("[{}]: {}".format(self.name_input.text(), msg))

    def recv_msg(self):
        self.chat_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        self.chat_server.bind(('', 20004))
        # print(self.chat_server)
        self.chat_server.listen()
        sock, addr = self.chat_server.accept()
        while True:  # while True:
            name = pickle.loads(sock.recv(1024))
            sock.send(pickle.dumps(0))
            msg = pickle.loads(sock.recv(1024))
            sock.send(pickle.dumps(0))
            self.chat_widget.addItem("[{}]: {}".format(name, msg))


if __name__ == '__main__':
    app = QtypeDemo([])
    app.window_ui(app.window, (720, 540))
    app.window.show()
    exit(app.exec_())
