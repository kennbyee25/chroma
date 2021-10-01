import yeelight

# Display handles the visual effects of
class Display:
    def __init__(self, mode="hsv"):
        self.mode = mode
        self.modes = {
            "rgb": self.displayRGB,
            "hsv": self.displayHSV,
        }
        self.findDevices()

    def findDevices(self):
        ips = [bulb["ip"] for bulb in yeelight.discover_bulbs()]
        self.bulbs = [yeelight.Bulb(ip, effect='sudden', ) for ip in ips]
        for bulb in self.bulbs:
            bulb.start_music()

    def display(self, x1, x2, x3):
        self.modes[self.mode](x1, x2, x3)

    def displayRGB(self, r, g, b):
        self.bulbs[0].set_rgb(r, g, b)

    def displayHSV(self, h, s, v):
        self.bulbs[0].set_hsv(h, s, v)
