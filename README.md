Really basic, use at your own risk and modify to your needs.

My use case was to play Oblivion remastered in French (I barely understand anything in French), and have this script running on second monitor to always have a fallback translation at hand.

Set your own ignored_patterns in settings.yaml, if any. In my use case I wanted to omit the "FPS: #" texts in the upper corner of the game window, thus the regex pattern '^FPS: \d+$'

Installing the needed packages might require some extra steps, such as adding something to system PATH, and setting that one pytesseract path in the screen_capture.py file.

Translation is done locally, which is nice.