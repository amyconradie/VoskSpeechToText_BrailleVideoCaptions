import numpy as np
import cv2 # opencv-python in package manager
import textwrap
from PIL import Image, ImageFont, ImageDraw # Pillow in package manager


class BrailleVideoCaptions:

    def __init__(self, encoder=None, stt = None):
        self.running = False
        self.terminated = False
        self.speech_text = "def"
        self.displayWindowName = "Live Braille Transcription"
        self.encoder = encoder
        self.stt = stt

        # text settings
        self.line_length = 20
        self.text_color = (255, 255, 255)
        self.bg_color = (0, 0, 0, 192)
        self.font_size = 28
        self.edges_margin = round(self.font_size*0.2)
        self.edges_curve_radius = round(self.font_size*0.3)
        self.alpha_font = ImageFont.truetype("./Inter-Medium.ttf", self.font_size)
        self.braille_font = ImageFont.truetype("./SimBraille.ttf", self.font_size)

    def speechToText(self):
        while True:
            if self.running:
                if self.stt is not None:
                    self.speech_text = self.stt.partial_text
            if self.terminated:
                break

    def videoCaptioning(self):
        # set the width and height, and UNSUCCESSFULLY set the exposure time
        cam = cv2.VideoCapture(0)
        cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))  # depends on fourcc available camera
        cam.set(cv2.CAP_PROP_FRAME_WIDTH, cam.get(cv2.CAP_PROP_FRAME_WIDTH))
        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, cam.get(cv2.CAP_PROP_FRAME_HEIGHT))
        # cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        # cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        cam.set(cv2.CAP_PROP_FPS, cam.get(cv2.CAP_PROP_FPS))

        # read recording
        flag, frame = cam.read()

        # get width and height
        width, height = np.size(frame, 1), np.size(frame, 0)

        print("Starting Transcriber...")

        while True:
            # start recording
            ret, img = cam.read()
            self.running = True

            # mirror camera
            img = cv2.flip(img, 1)

            # convert to pillow format
            img_pil = Image.fromarray(img)
            draw = ImageDraw.Draw(img_pil, "RGBA")


            # translate text
            wrapped_speech = textwrap.wrap(self.speech_text, self.line_length)
            wrapped_translation = textwrap.wrap(self.encoder.encode_text(self.speech_text), self.line_length)

            # if not silence
            if wrapped_translation != []:
                default_braille_height = self.braille_font.getbbox(wrapped_translation[0])[3]
                default_braille_row_gap = default_braille_height + round(default_braille_height * 0.5) + round(default_braille_height * 0.25)
                default_text_height = self.braille_font.getbbox(wrapped_speech[0])[3]

                # BRAILLE CAPTIONS

                # start position for braille captions
                translation_start_y = height - (default_braille_row_gap * len(wrapped_translation)) - default_braille_row_gap

                for i in range(0, len(wrapped_translation)):
                    # get size/position values
                    text_size = self.braille_font.getbbox(str(wrapped_translation[i]))
                    _, _, text_w, text_h = text_size

                    # position
                    x = round(width / 2) - round(text_w / 2)
                    y = translation_start_y + (i * (text_h + round(text_h * 0.5)))

                    # create captions
                    bbox = draw.textbbox((x, y + text_h), wrapped_translation[i], font=self.braille_font)
                    draw.rounded_rectangle((bbox[0] - self.edges_margin, bbox[1] - self.edges_margin, bbox[2] + self.edges_margin, bbox[3] + self.edges_margin), fill=self.bg_color, radius = self.edges_curve_radius)
                    draw.text((x, y + text_h), wrapped_translation[i], font=self.braille_font, fill=self.text_color)

                # TEXT CAPTIONS

                # start position for text captions
                text_start_y = translation_start_y - (default_braille_row_gap * len(wrapped_speech))

                for i in range(0, len(wrapped_speech)):
                    # get size/position values
                    text_size = self.alpha_font.getbbox(str(wrapped_speech[i]))
                    _, _, text_w, _ = text_size

                    # position
                    x = round(width / 2) - round(text_w / 2)
                    y = text_start_y + (i * (default_text_height + round(default_text_height * 0.75)))

                    # create captions
                    bbox = draw.textbbox((x, y + default_text_height), wrapped_speech[i], font=self.alpha_font)
                    draw.rounded_rectangle((bbox[0] - self.edges_margin, bbox[1] - self.edges_margin, bbox[2] + self.edges_margin, bbox[3] + self.edges_margin), fill=self.bg_color, radius = self.edges_curve_radius)
                    draw.text((x, y + default_text_height), wrapped_speech[i], font=self.alpha_font, fill=self.text_color)

            # convert from pillow to np
            img = np.array(img_pil)

            # display captioned video
            cv2.imshow(self.displayWindowName, img)

            key = cv2.waitKey(10)
            if key == 27:
                self.running = False
                self.terminated = True
                self.stt.terminate()
                break
            if cv2.getWindowProperty(self.displayWindowName, cv2.WND_PROP_VISIBLE) < 1:
                self.running = False
                self.terminated = True
                self.stt.terminate()
                break

        cv2.destroyAllWindows()
        cv2.VideoCapture(0).release()
        print("Shutting Down...")