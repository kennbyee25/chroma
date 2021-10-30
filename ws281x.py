import _rpi_ws281x as ws
from scipy.stats import binned_statistic
from colorsys import hsv_to_rgb
import audioop
import numpy as np
from config import *

class Ws281x:
    def __init__(self):
        # options
        self.start_index = 32
        self.max_vol = CHUNK / 40000
        self.smoothing = 4
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
        return np.arange(self.start_index, self.start_index + 60)

    def get_info_from_freq(self, f):
        pitch_class = 12 * np.log2(f / 440)  # 0 = A
        chroma = np.cos(np.pi * pitch_class)
        hue = ((-np.sign(chroma) * 3 - pitch_class + 8) % 12) / 12
        theta = hue * (2 * np.pi)
        info = dict(
            pitch_class=pitch_class,
            chroma=chroma,
            hue=hue,
            theta=theta,
        )
        return info

    def calculate_colors(self):
        colors = np.empty((120, 3))
        for i, freq in enumerate(self.bin_centers):
            info = self.get_info_from_freq(freq)
            color = hsv_to_rgb(info["hue"], 1, 1)
            colors[i][0] = color[0] * 32
            colors[i][1] = color[1] * 32
            colors[i][2] = color[2] * 32
        return colors[self.indexing]
        
    def process(self, data):
        data = np.frombuffer(data, np.float32)
        fft = np.abs(np.fft.rfft(data))
        stats = binned_statistic(
            self.fftfreq,
            fft,
            #statistic="sum",
            bins=self.bin_edges.tolist(),
            range=(self.freq_low, self.freq_high)
        )
        fft = stats.statistic
        fft = fft[self.indexing]
        fft = np.nan_to_num(fft)
        fft = np.clip(fft / self.max_vol, 0, 1)
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
        for i, (c, v) in enumerate(zip(self.colors, fft)):
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
