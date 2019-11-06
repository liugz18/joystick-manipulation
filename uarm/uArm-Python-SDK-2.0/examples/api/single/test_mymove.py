
import os
import sys
import time
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from uarm.wrapper import SwiftAPI

"""
api test: move
"""

swift = SwiftAPI(filters={'hwid': 'USB VID:PID=2341:0042'})

swift.waiting_ready(timeout=3)

device_info = swift.get_device_info()
print(device_info)
firmware_version = device_info['firmware_version']
if firmware_version and not firmware_version.startswith(('0.', '1.', '2.', '3.')):
    swift.set_speed_factor(0.0005)

swift.set_mode(0)
swift.reset(wait=True, speed=10000)
time.sleep(100)
os.system("pause")
#swift.set_position(x=200, speed=10000)
# swift.set_position(y=100)
# swift.set_position(z=80)
# os.system("pause")
#swift.flush_cmd(wait_stop=True)