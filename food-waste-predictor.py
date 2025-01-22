import sys
import cv2
import numpy as np
import tensorflow as tf
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)

# Função para carregar o modelo de predição
def load_prediction_model():
    try:
        model = tf.keras.models.load_model("trained_model.keras") # Substitua pelo caminho correto
        print("Modelo carregado com sucesso.")
        return model
    except Exception as e:
        print(f"Erro ao carregar o modelo: {e}")
        return None

def preprocess_image(image):
    """Pré-processa a imagem para ser compatível com o modelo."""
    resized_image = cv2.resize(image, (128, 128))  # Redimensiona para o tamanho usado no treinamento
    normalized_image = resized_image / 255.0  # Normaliza os valores de pixel
    return np.expand_dims(normalized_image, axis=0)  # Adiciona uma dimensão para o batch

def predict_waste_with_model(model, image):
    """Realiza a predição usando o modelo carregado."""
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

        # Inicializa o modelo de predição
        self.model = load_prediction_model()

        # Layout principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Título da aplicação
        title = QLabel("Food Waste Predictor")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #333;")
        layout.addWidget(title)

        # Nome dos alunos e logo
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

        # Visualização da imagem
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(
            "border: 2px solid #ccc; background-color: #fff; padding: 10px;"
        )
        layout.addWidget(self.image_label, alignment=Qt.AlignCenter)

        # Botão de predição
        self.predict_button = QPushButton("Predict Waste", self)
        self.predict_button.setFont(QFont("Arial", 14))
        self.predict_button.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 10px; border-radius: 5px;"
        )
        self.predict_button.clicked.connect(self.predict_waste)
        layout.addWidget(self.predict_button, alignment=Qt.AlignCenter)

        # Resultado da predição
        self.result_label = QLabel("Prediction result will appear here", self)
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
            self.result_label.setText("Camera not available. Trying to reinitialize...")
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
            self.result_label.setText("Failed to capture frame. Trying to reinitialize camera...")
            self.init_camera()

    def predict_waste(self):
        if self.capture is None or not self.capture.isOpened():
            self.result_label.setText("Camera not available. Cannot predict.")
            return

        ret, frame = self.capture.read()
        if ret:
            # Aqui aplicamos o modelo de predição
            prediction = predict_waste_with_model(self.model, frame)
            self.result_label.setText(f"Prediction: {prediction}")
        else:
            self.result_label.setText("Failed to capture frame for prediction.")

    def init_camera(self):
        for i in range(10):  # Tenta os primeiros 10 índices de câmera
            self.capture = cv2.VideoCapture(i, cv2.CAP_MSMF)
            if self.capture.isOpened():
                print(f"Camera initialized with index {i}")
                return
            self.capture.release()

        print("No camera found. Please check your camera connection.")
        self.result_label.setText("No camera found. Please check your camera connection.")

    def closeEvent(self, event):
        if self.capture is not None:
            self.capture.release()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FoodWastePredictor()
    window.show()
    sys.exit(app.exec_())
