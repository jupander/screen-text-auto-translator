
# screen_capture.py
import mss
from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' # to counter the error of tesseract not being found NOTE TODO change this to the path of your tesseract installation

def capture_image_and_text(monitor_index=1):
    with mss.mss() as sct:
        mon = sct.monitors[monitor_index]
        screenshot = sct.grab(mon)
        img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
        text = pytesseract.image_to_string(img)
        return img, text
