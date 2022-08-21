import _rpi_ws281x as ws
from scipy.stats import binned_statistic
from colorsys import hsv_to_rgb
import audioop
import numpy as np
from config import *

class Ws281x:
    def __init__(self):
        # options
        self.reverse_index = True
        self.start_index = 33
        # TODO smart volume/brightness controls?
        self.max_vol = CHUNK / 22
        self.smoothing = 1
        self.step = 0
        self.buf = np.empty((self.smoothing, 60))
        
        # init led strip
        self.led_channel = 0
        self.led_count = 60
        self.led_freq_hz = 800000
        self.led_dma_num = 10
        self.led_gpio = 18
        self.led_brightness = 255
        self.led_invert = 0
        self.leds = ws.new_ws2811_t()
        self.channel = self.spin()
        
        # init fft
        self.fftfreq = np.fft.rfftfreq(CHUNK, d=1 / RATE)
        self.freq_low = 20.0152313
        self.freq_high = 20495.5968
        self.bin_edges = np.geomspace(self.freq_low, self.freq_high, 121, endpoint=True)
        self.bin_centers = np.geomspace(20.6017223, 19912.1269582, 120, endpoint=True)
        self.indexing = self.index()
        self.colors = self.calculate_colors()
        

    def index(self):
        if self.reverse_index:
            return np.arange(self.start_index + 60, self.start_index)
        return np.arange(self.start_index, self.start_index + 60)

    def get_info_from_freq(self, f):
        pitch_class = 12 * np.log2(f / 440)  # 0 = A
        chroma = np.cos(np.pi * pitch_class)
        hue = ((-np.sign(chroma) * 3 - pitch_class + 8) % 12) / 12
        theta = hue * (2 * np.pi)
        # todo change info to a struct-esque class?
        info = dict(
            pitch_class=pitch_class,
            chroma=chroma,
            hue=hue,
            theta=theta,
        )
        return info

    def calculate_colors(self):
        # TODO add ability to calculate color live
        # that is, to support dynamic coloring as opposed to static
        # this should be available as an option
        colors = np.empty((120, 3))
        for i, freq in enumerate(self.bin_centers):
            info = self.get_info_from_freq(freq)
            color = hsv_to_rgb(info["hue"], 1, 1)
            # is this the most efficient? probably not
            colors[i][0] = color[0] * 32
            colors[i][1] = color[1] * 32
            colors[i][2] = color[2] * 32
        return colors[self.indexing]
        
    def process(self, data):
        data = np.frombuffer(data, np.float32)
        fft = np.abs(np.fft.rfft(data))
        # TODO custom binning
        stats = binned_statistic(
            self.fftfreq,
            fft,
            statistic="sum",
            bins=self.bin_edges.tolist(),
            range=(self.freq_low, self.freq_high)
        )
        fft = stats.statistic
        # select, re-organize, and consolidate bins to proper indexing
        fft = fft[self.indexing]
        # normalize within standardized range
        # todo this can be improved upon
        fft /= self.max_vol
        # bins can be empty
        fft = np.nan_to_num(fft)
        # squaring fft value is more representative of actual human sensory processing of
        # audio and light (citation needed)
        fft = fft ** 2
        # smooth out transition (should be in its own function)
        # similarly, this can be handled up in the Display class when update() is implemented
        if self.smoothing > 1:
            self.buf[:-1] = self.buf[1:]
            self.buf[-1] = fft.copy()
            if self.step >= self.smoothing:
                w = 0
                fft = np.zeros((60,))
                for i in range(self.smoothing):
                    w += 1/(i+1)
                    fft += self.buf[i]
                fft /= w
        self.vals = np.clip(fft, 0.0675, 1)
        for i, (c, v) in enumerate(zip(self.colors, self.vals)):
            v_r, v_g, v_b = int(round(c[0]*v)), int(round(c[1]*v)), int(round(c[2]*v))
            r = 0x10000*v_r
            g = 0x100*v_g
            b = v_b
            color = r + g + b
            ws.ws2811_led_set(self.channel, i, color)
        resp = ws.ws2811_render(self.leds)
        self.step += 1

    def off(self):
        for i in range(self.led_count):
            ws.ws2811_led_set(self.channel, i, 0)
        resp = ws.ws2811_render(self.leds)

    def spin(self):
        for channum in range(2):
            channel = ws.ws2811_channel_get(self.leds, channum)
            ws.ws2811_channel_t_count_set(channel, 0)
            ws.ws2811_channel_t_gpionum_set(channel, 0)
            ws.ws2811_channel_t_invert_set(channel, 0)
            ws.ws2811_channel_t_brightness_set(channel, 0)

        channel = ws.ws2811_channel_get(self.leds, self.led_channel)

        ws.ws2811_channel_t_count_set(channel, self.led_count)
        ws.ws2811_channel_t_gpionum_set(channel, self.led_gpio)
        ws.ws2811_channel_t_invert_set(channel, self.led_invert)
        ws.ws2811_channel_t_brightness_set(channel, self.led_brightness)
            
        ws.ws2811_t_freq_set(self.leds, self.led_freq_hz)
        ws.ws2811_t_dmanum_set(self.leds, self.led_dma_num)
        
        resp = ws.ws2811_init(self.leds)
        if resp != ws.WS2811_SUCCESS:
            message = ws.ws2811_get_return_t_str(resp)
            raise RuntimeError('ws2811_init failed with code {0} ({1})'.format(resp, message))
        
        return channel
    

    def close(self):
        ws.ws2811_fini(self.leds)
        ws.delete_ws2811_t(self.leds)
