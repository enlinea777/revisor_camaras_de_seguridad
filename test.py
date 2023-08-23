import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QSlider
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer

class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
    
    def setPixmap(self, pixmap):
        super().setPixmap(pixmap)
        if pixmap is not None:
            self.setFixedSize(pixmap.size())

class MotionDetectionApp(QMainWindow):
    def __init__(self, video_path, sensitivity):
        super().__init__()

        self.video_path = video_path
        self.sensitivity = sensitivity
        self.prev_frame = None
        self.playback_speed = 1  # Velocidad de reproducción inicial
        self.emular_frame=0

        self.cap = cv2.VideoCapture(self.video_path)
        
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle("Detección de Movimiento en Video")

        self.label = ImageLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setMinimumSize(640, 480)


        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 1)  # Establece el máximo al número total de frames menos 1
        self.slider.valueChanged.connect(self.slider_value_changed)
        
        
       
        layout = QVBoxLayout()
        layout.addWidget(self.label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.cap = cv2.VideoCapture(self.video_path)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(self.playback_speed)  # Actualizar a una velocidad según la reproducción
        
        layout.addWidget(self.slider)


    def slider_value_changed(self, value):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, value)  # Cambiar la posición del video según el valor del slider


    def   update_frame(self):
        
        

        ret, frame = self.cap.read()
        if not ret:
            self.timer.stop()
            self.cap.release()
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self.prev_frame is None:
            self.prev_frame = gray.copy()

        frame_delta = cv2.absdiff(self.prev_frame, gray)
        thresh = cv2.threshold(frame_delta, self.sensitivity, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        thresh = cv2.erode(thresh, None, iterations=2)

        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if cv2.contourArea(contour) < self.sensitivity:
                continue
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        self.prev_frame = gray.copy()

        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_image)

        self.label.setPixmap(pixmap)
        if self.emular_frame>200:
          self.slider.setValue(int(self.cap.get(cv2.CAP_PROP_POS_FRAMES)))
          self.emular_frame=0
        
        self.emular_frame+=1

    

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python script.py ruta_del_video.mp4 sensibilidad")
        sys.exit(1)

    video_path = sys.argv[1]
    sensitivity = int(sys.argv[2])

    app = QApplication(sys.argv)
    window = MotionDetectionApp(video_path, sensitivity)
    window.show()
    sys.exit(app.exec_())
