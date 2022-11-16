import argparse
import queue
import sys
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import json
from text2digits import text2digits


class SpeechToText:

    def __init__(self):
        self.q = queue.Queue()
        self.wav = queue.Queue()
        self.create_parser()
        self.set_sample_rate()
        self.load_model()
        self.running = True
        self.t2d = text2digits.Text2Digits()
        self.partial_text = ""
        self.text = ""

    def terminate(self):
        print("Stopped Listening... ")
        self.running = False
        exit(0)

    def int_or_str(self, text):
        """Helper function for argument parsing."""
        try:
            return int(text)
        except ValueError:
            return text

    def callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
        self.q.put(bytes(indata))
        self.wav.put(indata)

    def create_parser(self):
        self.parser = argparse.ArgumentParser(add_help=False)
        self.parser.add_argument("-l", "--list-devices", action="store_true", help="show list of audio devices and exit")
        self.args, self.remaining = self.parser.parse_known_args()

        # find active sound device
        if self.args.list_devices:
            print(sd.query_devices())
            self.parser.exit(0)

        self.parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, parents=[self.parser])
        self.parser.add_argument("-f", "--filename", type=str, metavar="FILENAME", help="audio file to store recording to")
        self.parser.add_argument("-d", "--device", type=self.int_or_str, help="input device (numeric ID or substring)")
        self.parser.add_argument("-r", "--samplerate", type=int, help="sampling rate")

        self.args = self.parser.parse_args(self.remaining)

    def set_sample_rate(self):
        if self.args.samplerate is None:
            device_info = sd.query_devices(self.args.device, "input")
            # soundfile expects an int, sounddevice provides a float:
            self.args.samplerate = int(device_info["default_samplerate"])

    def load_model(self):
        print("\nLoading Model... ")
        self.model = Model("small_model")
        print("\nModel Loaded... ")

    def run(self):
        with sd.RawInputStream(
                samplerate=self.args.samplerate, blocksize = 8196, device=self.args.device,
                dtype="int16", channels=1, callback=self.callback):

            print("Listening... ")

            rec = KaldiRecognizer(self.model, self.args.samplerate)

            self.text = ""
            self.partial_text = ""

            while self.running:
                self.data = self.q.get()

                if rec.AcceptWaveform(self.data):
                    # final sentence, can be added to a txt file
                    result = rec.Result()
                    # convert number words to numbers e.g. four = 4
                    self.text = self.t2d.convert(json.loads(result)["text"])
                else:
                    # unfinished sentence
                    partial_result = rec.PartialResult()
                    # convert number words to numbers e.g. four = 4
                    self.partial_text = self.t2d.convert(json.loads(partial_result)["partial"])


