# display.py (modified)
from PySide6.QtWidgets import QApplication, QLabel, QWidget
from PySide6.QtCore import Qt, QTimer
import mss

class TranslationDisplay(QWidget):
    def __init__(self, get_text_callback, update_interval=2000, monitor_index=2):
        super().__init__()
        self.get_text_callback = get_text_callback
        self.monitor_index = monitor_index
        self.init_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_text)
        self.timer.start(update_interval)

    def init_ui(self):
        with mss.mss() as sct:
            mon = sct.monitors[self.monitor_index]
            self.setGeometry(mon["left"], mon["top"], mon["width"], mon["height"])

        self.label = QLabel("", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 32px; color: white; background-color: black;")
        self.setWindowTitle("Live Translation")
        self.showFullScreen()

    def update_text(self):
        text = self.get_text_callback()
        self.label.setText(text)
