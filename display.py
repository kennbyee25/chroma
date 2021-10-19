import yeelight
import audioop
# import numpy as np
from config import *

# Display handles the visual effects of
class Display:
    def __init__(self, mode="hsv"):
        self.mode = mode
        self.bulb_modes = {
            "rgb": self.displayRGB,
            "hsv": self.displayHSV,
        }
        if self.bulb_modes in ["rgb", "hsv"]:
            self.findDevices()

        # # Array of frequency values associated with sample indices
        # self.fftfreq = np.fft.rfftfreq(CHUNK, d=1 / RATE)[1:]
        # # Array of MIDI values associated with sample indices
        # self.pitch_class = 12 * np.log2(self.fftfreq / 440)
        # # Array of weights [0, 1] relative to grey noise (approximately)
        # self.grey = 1 - np.power(2 * np.abs(0.5 - np.power(np.linspace(0, 1, CHUNK // 2), 0.3)), 2)
        # # Array of weights [-1, 1] to determine color saturation
        # self.chroma = np.cos(np.pi * self.pitch_class) * self.grey
        # # Array of hues [0, 1]
        # self.H = ((np.sign(self.chroma) * 3 - self.pitch_class + 8) % 12) / 12
        # # Array of respective theta for trigonometric calculations
        # self.Thetas = self.H * (2 * np.pi)

    def findDevices(self):
        ips = [bulb["ip"] for bulb in yeelight.discover_bulbs()]
        self.bulbs = [yeelight.Bulb(ip, effect='sudden', ) for ip in ips]
        for bulb in self.bulbs:
            bulb.start_music()

    def display_bulb(self, x1, x2, x3):
        self.bulb_modes[self.mode](x1, x2, x3)

    def displayRGB(self, r, g, b):
        self.bulbs[0].set_rgb(r, g, b)

    def displayHSV(self, h, s, v):
        self.bulbs[0].set_hsv(h, s, v)

    def process_bulb_HSV(self, data):
        rms = audioop.rms(data, 2)
        # data = np.frombuffer(data, np.float32)
        # fft = np.abs(np.fft.rfft(data))[1:]
        # # Volume * weight = value
        # V = np.abs((self.chroma) * (fft))
        # # place into polar coordinates
        # V_pol = (V * np.cos(self.Thetas), V * np.sin(self.Thetas))
        # # sum of vectors
        # XY = np.sum(V_pol, 1)
        # # hue is a function of the angle of the sum vector
        # hue = int(360 * ((np.arctan2(XY[1], XY[0]) / (2 * np.pi)) % 1))
        # # magnitude of sum vector
        # norm = np.linalg.norm(XY)
        # # sum of vector magnitudes
        # sum = np.sum(np.abs(V))
        # # random walk (colorless noise) is sqrt(N)
        # sat = int(100 * (norm / np.sqrt(sum) > 1))
        # sat = np.clip(sat, 1, 100)
        # # dynamic order polynomial on 75-100 dB for value
        # val = int(100 * np.power((rms - SENSITIVITY) / (18000 - SENSITIVITY), 18))
        # val = np.clip(val, 1, 100)
        self.display_bulb(hue, sat, val)

    def process_led_strip(self, data):
        rms = audioop.rms(data, 2)
        print(rms)

    def process(self, data):
        switch = {
            "hsv": self.process_bulb_HSV,
            "smd5050": self.process_led_strip,
        }
        switch["smd5050"](data)