#coding:utf-8
#c1:1090, 1933
#c2:1090, 1933
#c3:1090, 1933
#c4:1090, 1933
import io
import serial
port = '/dev/ttyACM0'
# baudrate
bps = 115200
# time
timex = 2
ser = serial.Serial(port, bps, timeout=timex)
sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))

def parse_radio_data(data_string):
    """parse the radio data which is in format 
        like 'c1:1000 c2:1023 c3:1033 c4:1972"""
    result = []
    for data in data_string.split():
        result.append(float(data.split(':')[1]))
    return result

print('Program started')
    # read some break data
while(True):
    # get radio channel data
    sio.write("s")
    sio.flush()
    data = sio.readline()
    print('raw data:', data)
    data = parse_radio_data(data)
    print('joystick data:',data)


print('Program ended')
