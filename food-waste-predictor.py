import sys
import cv2
import numpy as np
import tensorflow as tf
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)


def load_prediction_model():
    try:
        model = tf.keras.models.load_model("trained_model.keras")
        print("Modelo carregado com sucesso.")
        return model
    except Exception as e:
        print(f"Erro ao carregar o modelo: {e}")
        return None

def preprocess_image(image):

    resized_image = cv2.resize(image, (128, 128))  # Redimensiona para o tamanho usado no treinamento
    normalized_image = resized_image / 255.0  # Normaliza os valores de pixel
    return np.expand_dims(normalized_image, axis=0)  # Adiciona uma dimensão para o batch

def predict_waste_with_model(model, image):
    if model is None:
        return "Modelo não carregado"
    processed_image = preprocess_image(image)
    prediction = model.predict(processed_image)
    return "Desperdício" if prediction[0] > 0.5 else "Não Desperdício"

class FoodWastePredictor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Food Waste Predictor")
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet("background-color: #f5f5f5;")


        self.model = load_prediction_model()


        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        title = QLabel("Predição de despedício de alimento")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #333;")
        layout.addWidget(title)

        info_layout = QHBoxLayout()

        authors = QLabel("Autores: Brenno Pacheco, Thallyson Gabriel, Vinícius Santos")
        authors.setFont(QFont("Arial", 12))
        authors.setStyleSheet("color: #555;")
        info_layout.addWidget(authors)

        logo = QLabel()
        logo.setPixmap(QPixmap("university_logo.png").scaled(100, 100, Qt.KeepAspectRatio))
        logo.setAlignment(Qt.AlignRight)
        info_layout.addWidget(logo)

        layout.addLayout(info_layout)

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(
            "border: 2px solid #ccc; background-color: #fff; padding: 10px;"
        )
        layout.addWidget(self.image_label, alignment=Qt.AlignCenter)

        self.predict_button = QPushButton("Realizar predição", self)
        self.predict_button.setFont(QFont("Arial", 14))
        self.predict_button.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 10px; border-radius: 5px;"
        )
        self.predict_button.clicked.connect(self.predict_waste)
        layout.addWidget(self.predict_button, alignment=Qt.AlignCenter)

        # Resultado da predição
        self.result_label = QLabel("O resultado da predição vai aparecer aqui", self)
        self.result_label.setFont(QFont("Arial", 14))
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("color: #333;")
        layout.addWidget(self.result_label)

        # Inicializa a câmera
        self.capture = None
        self.init_camera()

        # Timer para atualizar os frames
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        if self.capture is None or not self.capture.isOpened():
            self.result_label.setText("Camera indisponivel. Tente novamente...")
            self.init_camera()
            return

        ret, frame = self.capture.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            self.image_label.setPixmap(pixmap.scaled(640, 480, Qt.KeepAspectRatio))
        else:
            self.result_label.setText("Falha ao capturar a imagem. Reiniciando cametra...")
            self.init_camera()

    def predict_waste(self):
        if self.capture is None or not self.capture.isOpened():
            self.result_label.setText("Camera indisponivel. A predição não pode ser realixzada.")
            return

        ret, frame = self.capture.read()
        if ret:
            # Aqui aplicamos o modelo de predição
            prediction = predict_waste_with_model(self.model, frame)
            self.result_label.setText(f"Predição: {prediction}")
        else:
            self.result_label.setText("Falha ao capturar o frame para a predição.")

    def init_camera(self):
        for i in range(10):  # Tenta os primeiros 10 índices de câmera
            self.capture = cv2.VideoCapture(i, cv2.CAP_MSMF)
            if self.capture.isOpened():
                print(f"Index da camera {i}")
                return
            self.capture.release()

        print("Nenhuma camera encontrada. Checar a conexão.")
        self.result_label.setText("Nenhuma camera encontrada. Checar a conexão.")

    def closeEvent(self, event):
        if self.capture is not None:
            self.capture.release()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FoodWastePredictor()
    window.show()
    sys.exit(app.exec_())
