from picamera2 import Picamera2
from libcamera import Transform
import time

picam2 = Picamera2()
config = picam2.create_still_configuration(transform=Transform(hflip=1, vflip=1))
picam2.configure(config)

# Manual exposure controls
picam2.set_controls({
    "AeEnable": False,
    "ExposureTime": 30000,
    "AnalogueGain": 2.5,
    "AwbEnable": False,
    "ColourGains": (1.5, 1.5)  # (red_gain, blue_gain) — start here, we'll tune
})

picam2.start()
time.sleep(2)

picam2.capture_file("test_image.jpg")
print("Saved test_image.jpg")

picam2.stop()
