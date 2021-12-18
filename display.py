import audioop
from config import *
from ws281x import Ws281x

# Display handles the visual effects
class Display:
    def __init__(self, mode="hsv"):
        self.mode = mode
        self.display = Ws281x()
        self.count = 0
        self.switch = {
            "smd5050": self.process_led_strip,
        }
        self.active = True

    def process_led_strip(self, data):
        self.display.process(data)

    def process(self, data):
        rms = audioop.rms(data, 1)
        if rms < 29:
            self.count += 1
        else:
            # TODO implement a better sleep/wake
            self.count = 0
        if self.count < 300:  # sleep if inactive
            self.switch["smd5050"](data)
        elif self.count >= 15 and self.active:
            self.display.off()

    def close(self):
        self.display.off()
        self.display.close()

    # TODO add update loop separate from FFT
    def update(self):
        # interpolate
        # update at rate (60 Hz)
        # predictive filtering?
        pass
