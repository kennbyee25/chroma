import pyaudio
import yeelight

p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')
for i in range(0, numdevices):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))

bulbs = yeelight.discover_bulbs()
for bulb in bulbs:
    print(bulb["ip"])
    bulb.set_rgb(255,255,255)
    bulb.set_temp(1700)