# main.py
import sys
import yaml
import mss
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout,
    QPushButton, QComboBox, QSpinBox, QLineEdit,
    QHBoxLayout, QTextEdit
)
from PySide6.QtCore import Qt, QTimer, QThreadPool, QRunnable, QObject, Signal, Slot
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor, QPen
from PIL import Image, ImageQt
import pytesseract
import re

#from screen_capture import capture_text
from screen_capture import capture_image_and_text
from translator import translate_text

CONFIG_PATH = "settings.yaml"

class TranslationWorker(QRunnable):
    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    @Slot()
    def run(self):
        self.fn()

class SignalEmitter(QObject):
    translation_ready = Signal(str, int)  # text, font_size

class ControlPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto Translator Control Panel")
        self.threadpool = QThreadPool()
        self.last_text = ""
        self.load_settings()
        #self.setGeometry(100, 100, 900, 1200)
        # get the last window position and size from settings
        # if "window_position" in self.settings: # "yaml.constructor.ConstructorError: could not determine a constructor for the tag 'tag:yaml.org,2002:python/tuple'"
        #     self.move(*self.settings["window_position"])
        if "window_position_x" in self.settings and "window_position_y" in self.settings:
            self.move(self.settings["window_position_x"], self.settings["window_position_y"])
        # if "window_size" in self.settings: # "yaml.constructor.ConstructorError: could not determine a constructor for the tag 'tag:yaml.org,2002:python/tuple'"
        #     self.resize(*self.settings["window_size"])
        if "window_size_width" in self.settings and "window_size_height" in self.settings:
            self.resize(self.settings["window_size_width"], self.settings["window_size_height"])
        else:
            self.resize(900, 1200)
        self.setup_ui()
        self.signal_emitter = SignalEmitter()
        self.signal_emitter.translation_ready.connect(self.display_text)

    def display_text(self, translated, font_size):
        self.output_area.setStyleSheet(f"font-size: {font_size}px;")
        self.output_area.setText(translated)


    def load_settings(self):
        with open(CONFIG_PATH, "r") as f:
            self.settings = yaml.safe_load(f)
            self.ignored_patterns = [
                re.compile(pat) for pat in self.settings.get("ignored_patterns", [])
            ]

    def save_settings(self):
        with open(CONFIG_PATH, "w") as f:
            yaml.dump(self.settings, f)

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #2e2e2e;
                color: white;
                font-size: 14px;
            }
            QTextEdit {
                background-color: black;
                color: white;
                font-family: Consolas;
            }
        """)

        layout = QVBoxLayout()

        self.capture_monitor_combo = QComboBox()
        self.populate_monitors()
        layout.addWidget(QLabel("Capture Monitor:"))
        layout.addWidget(self.capture_monitor_combo)

        lang_row = QHBoxLayout()
        self.source_input = QLineEdit(self.settings.get("source_language", "fr"))
        self.target_input = QLineEdit(self.settings.get("target_language", "en"))
        lang_row.addWidget(QLabel("From:"))
        lang_row.addWidget(self.source_input)
        lang_row.addWidget(QLabel("To:"))
        lang_row.addWidget(self.target_input)
        layout.addLayout(lang_row)

        layout.addWidget(QLabel("Update Interval:"))
        self.interval_input = QSpinBox()
        self.interval_input.setMinimum(500)
        self.interval_input.setMaximum(10000)
        self.interval_input.setSingleStep(500)
        self.interval_input.setSuffix(" ms")
        self.interval_input.setToolTip("Interval for capturing and translating text")
        self.interval_input.setValue(self.settings.get("update_interval", 3000))
        layout.addWidget(self.interval_input)

        layout.addWidget(QLabel("Font Size:"))
        self.font_size_input = QSpinBox()
        self.font_size_input.setMinimum(8)
        self.font_size_input.setMaximum(48)
        self.font_size_input.setValue(self.settings.get("font_size", 16))
        layout.addWidget(self.font_size_input)

        button_row = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_translation)
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_translation)
        button_row.addWidget(self.start_button)
        button_row.addWidget(self.stop_button)
        layout.addLayout(button_row)
        self.status_label = QLabel()
        self.set_status("Stopped")
        layout.addWidget(self.status_label)

        layout.addWidget(QLabel("Translated Output:"))
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        layout.addWidget(self.output_area)

        self.preview_label = QLabel()
        self.preview_label.setFixedHeight(200)
        self.preview_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(QLabel("Captured Region Preview:"))
        layout.addWidget(self.preview_label)

        self.setLayout(layout)

    def populate_monitors(self):
        with mss.mss() as sct:
            for i, mon in enumerate(sct.monitors[1:], start=1):
                desc = f"Monitor {i}: {mon['width']}x{mon['height']}"
                self.capture_monitor_combo.addItem(desc, i)
        default_index = self.settings.get("capture_monitor", 1) - 1
        self.capture_monitor_combo.setCurrentIndex(default_index)

    def start_translation(self):
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        #self.status_label.setText("Status: Running")
        self.set_status("Running")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.run_translation_threaded)
        self.timer.start(self.interval_input.value())

    def stop_translation(self):
        if hasattr(self, 'timer'):
            self.timer.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        #self.status_label.setText("Status: Stopped")
        self.set_status("Stopped")

    def run_translation_threaded(self):
        worker = TranslationWorker(self.update_text)
        self.threadpool.start(worker)

    def update_text(self):
        monitor_index = self.capture_monitor_combo.currentData()
        source_lang = self.source_input.text().strip()
        target_lang = self.target_input.text().strip()
        font_size = self.font_size_input.value()
        
        pil_img, text = capture_image_and_text(monitor_index)
        text = text.strip()

        # Filter out ignored patterns
        lines = text.splitlines()
        lines = [line for line in lines if not any(p.match(line) for p in self.ignored_patterns)]
        text = "\n".join(lines).strip()

        self.update_preview(pil_img)

        if len(text) < 12 or text == self.last_text:
            return
        translated = translate_text(text, target_lang, source_lang)
        self.last_text = text
        self.signal_emitter.translation_ready.emit(translated, font_size)

    def set_status(self, status):
        color = "green" if status == "Running" else "red"
        self.status_label.setText(f"<span style='color:{color}; font-weight:bold;'>●</span> Status: {status}")

    def closeEvent(self, event):
        self.settings["capture_monitor"] = self.capture_monitor_combo.currentData()
        self.settings["source_language"] = self.source_input.text().strip()
        self.settings["target_language"] = self.target_input.text().strip()
        self.settings["update_interval"] = self.interval_input.value()
        self.settings["font_size"] = self.font_size_input.value()
        #self.settings["window_position"] = self.pos().toTuple() # "yaml.constructor.ConstructorError: could not determine a constructor for the tag 'tag:yaml.org,2002:python/tuple'"
        self.settings["window_position_x"] = self.pos().x()
        self.settings["window_position_y"] = self.pos().y()
        #self.settings["window_size"] = self.size().toTuple() # "yaml.constructor.ConstructorError: could not determine a constructor for the tag 'tag:yaml.org,2002:python/tuple'"
        self.settings["window_size_width"] = self.size().width()
        self.settings["window_size_height"] = self.size().height()
        self.save_settings()
        super().closeEvent(event)

    def update_preview(self, pil_img):
        qimage = ImageQt.ImageQt(pil_img)
        pixmap = QPixmap.fromImage(QImage(qimage))
        painter = QPainter(pixmap)
        #painter.setPen(QPen(QColor(255, 255, 0, 180), 2)) # Yellow color with alpha
        painter.setPen(QPen(QColor(255, 20, 147, 180), 2)) # Neon pink color with alpha
        #painter.setBrush(QColor(255, 255, 0, 80)) # Yellow color with alpha
        painter.setBrush(QColor(255, 20, 147, 80)) # Neon pink color with alpha

        boxes = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)
        for i in range(len(boxes['text'])):
            if int(boxes['conf'][i]) > 0 and len(boxes['text'][i].strip()) > 1:
                x, y, w, h = boxes['left'][i], boxes['top'][i], boxes['width'][i], boxes['height'][i]
                painter.drawRect(x, y, w, h)

        painter.end()
        scaled = pixmap.scaledToHeight(200, Qt.SmoothTransformation)
        self.preview_label.setPixmap(scaled)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    panel = ControlPanel()
    panel.show()
    sys.exit(app.exec())
