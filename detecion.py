import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QSlider, QHBoxLayout, QLineEdit
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

    def mousePressEvent(self, event):
        if self.parent.label.pixmap() is not None:
            image_x = int(event.pos().x() * self.parent.cap.get(cv2.CAP_PROP_FRAME_WIDTH) / self.parent.label.pixmap().width())
            image_y = int(event.pos().y() * self.parent.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) / self.parent.label.pixmap().height())
            self.parent.roi_pts = [(image_x, image_y)]
            self.parent.drawing = True

    def mouseMoveEvent(self, event):
        if self.parent.drawing and self.parent.label.pixmap() is not None:
            image_x = int(event.pos().x() * self.parent.cap.get(cv2.CAP_PROP_FRAME_WIDTH) / self.parent.label.pixmap().width())
            image_y = int(event.pos().y() * self.parent.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) / self.parent.label.pixmap().height())
            self.parent.roi_pts.append((image_x, image_y))


class MotionDetectionApp(QMainWindow):
    def __init__(self, video_path, sensitivity):
        super().__init__()

        self.video_path = video_path
        self.sensitivity = sensitivity
        self.prev_frame = None
        self.paused = False
        self.playback_speed = 1  # Velocidad de reproducción inicial
        self.drawing = False
        self.roi_pts =[]
        self.pausas_detectadas = 0
        self.emular_frame=0

        self.cap = cv2.VideoCapture(self.video_path)

        self.maximo_frames_del_video=int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 1
        
        self.setGeometry(100, 100, 1280, 800)
        self.setWindowTitle("Detección de Movimiento en Video")

        self.label = ImageLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(self.maximo_frames_del_video)  # Establece el máximo al número total de frames menos 1
        self.slider.valueChanged.connect(self.slider_value_changed)

        
        layout = QVBoxLayout()

        self.slider_layout = QHBoxLayout()

        self.playback_slider = QSlider(Qt.Horizontal)
        self.playback_slider.setMinimum(1)
        self.playback_slider.setMaximum(300)
        self.playback_slider.setValue(self.sensitivity)
        self.playback_slider.valueChanged.connect(self.update_playback_speed)
        self.slider_layout.addWidget(self.playback_slider)

        #layout.addLayout(self.slider_layout)
        
        
        self.slider_layout_2 = QHBoxLayout()

        self.sensibilidad_slider = QSlider(Qt.Horizontal)
        self.sensibilidad_slider.setMinimum(1)
        self.sensibilidad_slider.setMaximum(1000)
        self.sensibilidad_slider.setValue(self.playback_speed)
        self.sensibilidad_slider.valueChanged.connect(self.update_sensitivity)
        self.slider_layout_2.addWidget(self.sensibilidad_slider)

        #layout.addLayout(self.slider_layout_2)

        self.sensitivity_layout = QHBoxLayout()
        self.sensitivity_label = QLabel("Sensibilidad:")
        self.sensitivity_value = QLabel(str(self.sensitivity))
        self.sensitivity_value.setFixedWidth(50)
        self.sensitivity_layout.addWidget(self.sensitivity_label)
        self.sensitivity_layout.addLayout(self.slider_layout_2)
        self.sensitivity_layout.addWidget(self.sensitivity_value)
        layout.addLayout(self.sensitivity_layout)

        self.speed_play_layout = QHBoxLayout()

        
        self.speed_play_label = QLabel("Velocidad:")
        self.speed_play_value = QLabel(str(self.playback_speed))
        self.speed_play_value.setFixedWidth(50)
        self.speed_play_layout.addWidget(self.speed_play_label)
        self.speed_play_layout.addLayout(self.slider_layout)
        self.speed_play_layout.addWidget(self.speed_play_value)
        layout.addLayout(self.speed_play_layout)

        self.play_pause_button = QPushButton("Pausa/Reanudar", self)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        layout.addWidget(self.play_pause_button)

        self.step_button = QPushButton("Avanzar un Cuadro", self)
        self.step_button.clicked.connect(self.step_frame)
        layout.addWidget(self.step_button)

        self.stop_button = QPushButton("Detener", self)
        self.stop_button.clicked.connect(self.stop)
        layout.addWidget(self.stop_button)

        layout.addWidget(self.label)
        layout.addWidget(self.slider)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.cap = cv2.VideoCapture(self.video_path)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(self.playback_speed)  # Actualizar a una velocidad según la reproducción

        
    def slider_value_changed(self, value):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, value)  # Cambiar la posición del video según el valor del slider


    def toggle_play_pause(self):
        self.paused = not self.paused

    def step_frame(self):
        self.paused = True
        self.update_frame()

    def stop(self):
        self.timer.stop()
        self.cap.release()

    def update_frame(self):

      if self.paused: 
          return
      

      ret, frame = self.cap.read()
      if not ret:
          self.slider.setValue(self.maximo_frames_del_video)
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

      if self.roi_pts:
          mask = np.zeros_like(thresh)
          cv2.fillPoly(mask, [np.array(self.roi_pts)], 255)
          thresh = cv2.bitwise_and(thresh, mask)

      contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

      for contour in contours:
          if cv2.contourArea(contour) < self.sensitivity:
              continue
          (x, y, w, h) = cv2.boundingRect(contour)
          cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2) # colorea un rectangulo verde
          self.pausas_detectadas+=1
          if self.pausas_detectadas>3:
            self.pausas_detectadas=0;
            self.paused = True

      if self.roi_pts:
        overlay = frame.copy()
        cv2.fillPoly(overlay, [np.array(self.roi_pts)], (0, 0, 255))  # Relleno rojo sólido
        cv2.polylines(overlay, [np.array(self.roi_pts)], isClosed=True, color=(0, 0, 255), thickness=6)  # Trazo del área
        cv2.addWeighted(overlay, 0.5, frame, 1 - 0.5, 0, frame)

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
      


    def update_playback_speed(self, value):
        self.playback_speed = value
        self.speed_play_value.setText(str(self.playback_speed))
        self.timer.setInterval(self.playback_speed)  # Actualizar la velocidad del temporizador

    def update_sensitivity(self, value):
        self.sensitivity_value.setText(str(value))
        self.sensitivity = value

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

