from BrailleCaptions import BrailleVideoCaptions
from BrailleEncoder import BrailleEncoder
from VoskSpeechToText import SpeechToText
import time

from threading import Thread

stt = SpeechToText()
transcriber = BrailleVideoCaptions(BrailleEncoder(), stt)

# run these three functions simultaneously
video_captions_thread = Thread(target=transcriber.videoCaptioning)
stt_to_captions_thread = Thread(target=transcriber.speechToText)
stt_thread = Thread(target=stt.run)


video_captions_thread.start() # takes a second to load
stt_to_captions_thread.start()
stt_thread.start()
