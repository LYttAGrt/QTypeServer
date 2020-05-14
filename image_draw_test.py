from PyQt5 import Qt, QtWidgets, QtMultimedia
from scipy import ndimage
import numpy as np


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
        planes.append(np.asarray(data[:height*width], dtype=np.uint8).reshape((width, height)))
        # U is data[x*y:x*y*5/4]
        planes.append(np.asarray(data[height*width:int(height*width*5/4)], dtype=np.uint8).reshape((int(width/2), int(height/2))))
        # V is data[x*y*5/4:]
        planes.append(np.asarray(data[int(height*width*5/4):], dtype=np.uint8).reshape((int(width/2), int(height/2))))
        return convertYUVtoRGB(yuv_planes=planes, zoom_needed=True)

    # Convert YUYV to RGB
    elif pixel_format == Qt.QVideoFrame.Format_YUYV:
        planes = list()
        return convertYUVtoRGB(yuv_planes=planes, zoom_needed=False)


class App(QtWidgets.QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.window = QtWidgets.QMainWindow()
        self.window.resize(960, 540)

        self.view_finder = Qt.QCameraViewfinder(self.window)
        self.view_finder.setGeometry(0, 0, int(self.window.width() / 6), int(self.window.height()/6))

        self.viewfinder_settings = Qt.QCameraViewfinderSettings()
        self.viewfinder_settings.setResolution(640, 480)

        self.camera = QtMultimedia.QCamera(QtMultimedia.QCamera.availableDevices()[0])
        self.camera.setParent(self.window)
        self.camera.setCaptureMode(Qt.QCamera.CaptureVideo)
        self.camera.setViewfinder(self.view_finder)
        self.camera.setViewfinderSettings(self.viewfinder_settings)

        self.video_probe = QtMultimedia.QVideoProbe(self.window)
        self.video_probe.setSource(self.camera)
        self.video_probe.videoFrameProbed.connect(self.show_image)

        # Attempt 1: QGraphicsView
        self.view = QtWidgets.QGraphicsView(self.window)
        self.view.setGeometry(int(self.window.width() / 6), 0, self.window.width(), self.window.height())
        self.scene = QtWidgets.QGraphicsScene(self.view)
        self.view.fitInView(0, 0, self.window.width(), self.window.height())

    def show_image(self, frame: QtMultimedia.QVideoFrame):
        # Send frame data
        frame.map(QtMultimedia.QAbstractVideoBuffer.ReadOnly)
        bits_ptr = frame.bits()
        bits_ptr.setsize(frame.mappedBytes())
        bits_ptr = bytes(bits_ptr)
        print(f"size: {frame.width()}*{frame.height()} is {frame.mappedBytes()}, format={frame.pixelFormat()}", "--->", end=' ')

        # Recv raw QVideoFrame
        conv: np.ndarray = convert_to_rgb([*bits_ptr])
        print(conv.shape, "--->", end=' ')

        image = Qt.QImage(conv.data, conv.shape[0], conv.shape[1], conv.shape[0]*conv.shape[2], Qt.QImage.Format_Indexed8)
        print(image.width(), image.height())
        self.scene.clear()
        self.scene.addPixmap(Qt.QPixmap.fromImage(image))
        self.view.setScene(self.scene)


if __name__ == '__main__':
    app = App([])
    app.camera.start()
    app.window.show()
    exit(app.exec_())
