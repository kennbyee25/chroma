import pyaudio
import audioop
import numpy as np
from config import *
from display import Display

FORMAT = pyaudio.paFloat32
p = pyaudio.PyAudio()
d = Display("hsv")

# Initialize audio stream with config
stream = pyaudio.Stream(p,
                        format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        input_device_index=DEVICE)

# Array of frequency values associated with sample indices
fftfreq = np.fft.rfftfreq(CHUNK, d=1 / RATE)[1:]
# Array of MIDI values associated with sample indices
pitch_class = 12 * np.log2(fftfreq / 440)
# Array of weights [0, 1] relative to grey noise (approximately)
grey = 1 - np.power(2 * np.abs(0.5 - np.power(np.linspace(0, 1, CHUNK // 2), 0.3)), 2)
# Array of weights [-1, 1] to determine color saturation
chroma = np.cos(np.pi * pitch_class) * grey
# Array of hues [0, 1]
H = ((np.sign(chroma) * 3 - pitch_class + 8) % 12) / 12
# Array of respective theta for trigonometric calculations
Thetas = H * (2 * np.pi)

while stream.is_active():
    i = np.random.randint(0, CHUNK // 2)
    data = stream.read(CHUNK, False)
    rms = audioop.rms(data, 2)
    data = np.frombuffer(data, np.float32)
    fft = np.abs(np.fft.rfft(data))[1:]
    # Volume * weight = value
    V = np.abs((chroma) * (fft))
    # place into polar coordinates
    V_pol = (V * np.cos(Thetas), V * np.sin(Thetas))
    # sum of vectors
    XY = np.sum(V_pol, 1)
    # hue is a function of the angle of the sum vector
    hue = int(360 * ((np.arctan2(XY[1], XY[0]) / (2 * np.pi)) % 1))
    # magnitude of sum vector
    norm = np.linalg.norm(XY)
    # sum of vector magnitudes
    sum = np.sum(np.abs(V))
    # random walk (colorless noise) is sqrt(N)
    sat = int(100 * (norm / np.sqrt(sum) > 1))
    sat = np.clip(sat, 1, 100)
    # dynamic order polynomial on 75-100 dB for value
    val = int(100 * np.power((rms - SENSITIVITY) / (18000-SENSITIVITY), 18))
    val = np.clip(val, 1, 100)
    d.display(hue, sat, val)


stream.stop_stream()
stream.close()

p.terminate()
