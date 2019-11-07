#coding:utf-8
#c1:1090, 1933
#c2:1090, 1933
#c3:1090, 1933
#c4:1090, 1933
import io
import sys
import os
import time
sys.path.append(os.path.join(os.path.split(__file__)[0], 'lib'))
import vrep
import serial
port = 'COM17'
# baudrate
bps = 115200
# time
timex = 5
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
vrep.simxFinish(-1)  # just in case, close all opened connections
clientID = vrep.simxStart('127.0.0.1', 19997, True, True, 5000, 5)  # Connect to V-REP
if clientID != -1:
    res, objs = vrep.simxGetObjectHandle(clientID, 'Quadricopter',
                                         vrep.simx_opmode_blocking)
    if res == vrep.simx_return_ok:
        print('get quadricopter')

    vrep.simxSynchronous(clientID, True)
    vrep.simxStartSimulation(clientID, vrep.simx_opmode_blocking)
    # read some break data
    try:
        data = sio.readline()
    except:
        pass
    for i in range(10):
        print(i)
        # get radio channel data
        sio.write("s")
        sio.flush()
        data = sio.readline()
        print('raw data:', data)
        data = parse_radio_data(data)
        print('input data:',data)
        inputInts = []
        inputFloats = data
        inputStrings = []
        inputBuffer = bytearray()
        res, retInts, retFloats, retStrings, retBuffer = vrep.simxCallScriptFunction(
            clientID, 'Quadricopter', vrep.sim_scripttype_childscript,
            'setControlValue', inputInts, inputFloats, inputStrings, inputBuffer,
            vrep.simx_opmode_blocking)
        if res == vrep.simx_return_ok:
            print('set value successful.')
        vrep.simxSynchronousTrigger(clientID)
        # time.sleep(0.2)
        
    time.sleep(3)
    

    vrep.simxAddStatusbarMessage(clientID, 'Hello V-REP!',
                                 vrep.simx_opmode_oneshot)

    # Before closing the connection to V-REP, make sure that the last command sent out had time to arrive. You can guarantee this with (for example):
    vrep.simxGetPingTime(clientID)

    # Now close the connection to V-REP:
    vrep.simxFinish(clientID)
else:
    print('Failed connecting to remote API server')
print('Program ended')
