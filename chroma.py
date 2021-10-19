import pyaudio
from config import *
from display import Display

FORMAT = pyaudio.paFloat32

p = pyaudio.PyAudio()
d = Display()

# Initialize audio stream with config
stream = pyaudio.Stream(p,
                        format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        input_device_index=DEVICE,
                        )

while stream.is_active():
    data = stream.read(CHUNK, False)
    d.process(data)


stream.stop_stream()
stream.close()

p.terminate()
