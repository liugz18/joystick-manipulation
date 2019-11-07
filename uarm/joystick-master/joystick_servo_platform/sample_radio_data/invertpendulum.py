#coding:utf-8
#c1:1090, 1933 c2:1090, 1933 c3:1090, 1933 c4:1090, 1933
import io
import sys
from time import time
import serial
from threading import Thread
from numpy import sin, cos, tan
import numpy as np
import scipy.integrate as integrate
from matplotlib import pyplot as plt
import matplotlib.patches as patches
import matplotlib.animation as animation
port = 'COM6'
# baudrate
bps = 115200
# time
timex = 5
ser = serial.Serial(port, bps, timeout=timex)
sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))

def parse_radio_data(data_string):
    """parse the radio data which is in format 
        like 'c1:1000 c2:1023 c3:1033 c4:1972"""
    print(data_string)
    result = []
    for data in data_string.split():
        result.append(float(data.split(':')[1]))
    return result

radio_ops = [1500, 1500, 1500, 1500]
# read some initial error data on serial port
try:
    ser.readline()
except:
    pass


# invert pendulum dynamics
length_pendulum = 0.2 # m
mass_pendulum = 0.5 # kg
width_box = 1 
height_box = 0.5
mass_box = 1
#G = 1.81 # m/s^2
G = 9.81
params = [width_box, length_pendulum, mass_box, mass_pendulum, G, height_box]

dt = 1/30
# initial angle and angular velocity
theta = np.random.randint(45, 135)
omega = 0.0
# initial position of box
x,y = 0, 0

F_ratio = 1
F = 0

state = [0.0,0.0,np.pi/2.0 + 0.05 * np.pi,0.0]
def dstate_dt(state, t):
    """Compute the derivative of the given state"""
    (L1, L2, M1, M2, G, boxHeight) = params
    dydx = np.zeros_like(state)

    dydx[0] = state[1]
    dydx[2] = state[3]

    # PID controller
    #F_final = 320 * (np.pi/2 - state[2]) #- 20 * (state[3])
    #print('F, F_ratio:', F, F_ratio)
    F_final = F * F_ratio * 50

    dydx[3] = (F_final * sin(state[2]) + 1 / 2 * M2 * state[3] ** 2 * cos(state[2]) * sin(state[2])
               - G * cos(state[2]) * (M1 + M2)) / \
              (7 / 6 * L2 * (M1 + M2) - 1 / 2 * M2 * L2 * (sin(state[2])) ** 2)

    dydx[1] = 7 / 6 * L2 ** 2 * 1 / sin(state[2]) * (dydx[3]) + G * 1 / tan(state[2])
    return dydx

def get_enegy(state):
    """Calculate the all energy

    Returns:
        energy:
    """
    (L1, L2, M1, M2, G, boxHeight) = params
    # Potential energy
    V = L1 * M1 * G * np.sin(state[2])
    # Kinetic energy
    T = 1 / 2.0 * M1 * state[1] ** 2.0 + 1 / 12.0 * M2 * L2 ** 2 * state[3] ** 2 + \
        1 / 2.0 * M2 * (state[1] - state[3] * L2 / 2 * sin(state[2])) ** 2 + \
        1 / 2.0 * M2 * (state[3] * L2 / 2.0 * cos(state[2])) ** 2
    return V + T

limit = [np.pi/4, np.pi * 3/4]
def step():
    """Run one step

    Returns:
        reward:
    """
    global F, F_ratio
    global state
    ser.write(b's')
    bytes = ser.readline()
    radio_ops = parse_radio_data(bytes.decode('utf-8'))
    print(radio_ops)
    F_ratio = (radio_ops[2] - 1090) / (1933 - 1090) * 3
    F = (radio_ops[0] -  1511) / (1933 - 1090)
    print('F, F_ratio:', F, F_ratio)
    start = time()
    state = integrate.odeint(dstate_dt, state, [0, dt])[1]
    print('integration time', time() - start)
    if (state[2] < limit[0] or state[2] > limit[1]):
        R = -1
        termination = True
    else:
        R = 0
        termination = False

    new_state = state[2], state[3]
    return R, termination, new_state

fig = plt.figure()
ax = fig.add_subplot(111, aspect='equal', autoscale_on=False,
                     xlim=(-5, 5), ylim=(-1, 3))
ax.grid()

(L1, L2, M1, M2, G, boxHeight) = params
box = ax.add_patch(patches.Rectangle((0, 0), 0, 0, color='red', animated=True))
line, = ax.plot([], [], 'o-', lw=6)
time_text = ax.text(0.02, 0.95, '', transform=ax.transAxes)
energy_text = ax.text(0.02, 0.85, '', transform=ax.transAxes)

def simulation():
    #plt.ion()
    def init():
        """initialize animation"""
        box.set_height(boxHeight)
        box.set_width(L1)
        line.set_data([], [])
        time_text.set_text('')
        energy_text.set_text('')
        return box, line, time_text, energy_text

    time_elapsed  = 0
    def animate(i):
        nonlocal time_elapsed
        R, termination, _ = step()
        posX = np.cumsum([state[0],
                       L1 * cos(state[2])])
        posY = np.cumsum([boxHeight,
                       L1 * sin(state[2])])
        energy = get_enegy(state)
        box.set_x(posX[0] - L1 / 2)
        line.set_data(posX, posY)
        time_elapsed += dt
        time_text.set_text('time = %.1f' % time_elapsed)
        energy_text.set_text('energy = %.3f J' % energy)
        return box, line, time_text, energy_text

    t0 = time()
    animate(0)
    t1 = time()
    interval = 1000* dt - (t1 - t0)

    ani = animation.FuncAnimation(fig, animate,
                                  interval=dt, blit=True, init_func=init)
    print('show')
    plt.show()
    print('end')

if __name__ == '__main__':
    simulation()
