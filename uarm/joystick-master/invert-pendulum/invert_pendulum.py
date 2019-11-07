#coding:utf-8

from __future__ import division
from time import time
from copy import deepcopy
from numpy import sin, cos ,tan
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy import integrate
import matplotlib.animation as animation
import serial
import pdb
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

class Invert_Pendulum(object):
    """This is a invert simulation class.

    Attributes:
        L1: The length of the box
        L2: The length of the pendulum
    boxHeight: The height of the box
        M1: The mass of box
        M2: The mass of pendulum
        init_state: the init state of the system. [x1,x1_dot,x2,x2_dot]
            x1 is the displacement, x2 is the angle from horizontal and
            is positive in clockwise, x1_dot is  derivative of x1,
            x2_dot is the derivative of x2_dot.
    """

    def __init__(self,
                L1=0.5,
                L2=1.0,
                boxHeight=0.2,
                M1=1.0,
                M2=1.0,
                G = 9.8,
                init_state = [0.0,0.0,np.pi/2.0 + 0.1 * np.pi,0.0]):
        """Inits SampleClass."""
        self.params = (L1,L2,M1,M2,G, boxHeight)
        self._init_state = init_state
        self.time_elapsed = 0
        self.state = deepcopy(self._init_state)
        
        # failed limit
        self.limit = (np.pi/4,3*np.pi/4)
        
        # all states
        self.states = [(round(theta,3),round(dtheta,3)) for theta in np.linspace(self.limit[0],self.limit[1],10) 
                         for dtheta in np.linspace(-10,10,10)]
        # all possible Forces
        self.actions = [-120,-100,-80,-60,-40,-20,-10,-6,-1,0,1,6,10,20,40,60,80,100,120]
        
        # F 
        self.F = 0
        
        self.history = []
        self.dt = 1/30
        self.steps = 0        
        

    def dstate_dt(self, state, t):
        """Compute the derivative of the given state"""
        (L1, L2, M1, M2, G, boxHeight) = self.params

        dydx = np.zeros_like(state)
        dydx[0] = state[1]
        dydx[2] = state[3]

        #PID controller
        #F = 320 * (np.pi/2 - state[2]) - 20 * (state[3])
        F = self.F
        
        dydx[3] = ( F * sin(state[2]) + 1/2 * M2 * state[3]**2 * cos(state[2])*sin(state[2])
                     - G * cos(state[2]) *(M1 + M2)) / \
                  (7/6 * L2 * (M1 + M2) - 1/2* M2 * L2 * (sin(state[2]))**2)

        dydx[1] = 7/6 * L2**2 * 1/sin(state[2])*(dydx[3]) + G * 1/tan(state[2])
        return dydx
    
    def take_action(self,action):
        """Take some action"""
        #print("action:%d" % (action))
        self.F = action
        return self.step()
            
    def step(self):
        """Run one step
        
        Returns:
            reward:
        """
        dt = self.dt
        self.state = integrate.odeint(self.dstate_dt, self.state, [0, dt])[1]
        self.time_elapsed += dt
        self.steps += 1
        # append to the history list
        self.history.append((self.get_position(),self.time_elapsed,self.get_enegy()))
        
        # if failed punished, otherwise no return
        if(self.state[2] < self.limit[0] or self.state[2] > self.limit[1]):
            R = -1
            termination = True
        else:
            R = 0
            termination = False
        
        new_state = self.state[2],self.state[3]
        #print(new_state)
        return R,termination,new_state
        

    def get_position(self):
        """Return the position of the box and the pole

        """
        (L1, L2, M1, M2, G, boxHeight) = self.params
        x = np.cumsum([self.state[0],
                      L1 * cos(self.state[2])])
        y = np.cumsum([boxHeight,
                      L1 * sin(self.state[2])])
        return x,y
    
    def get_enegy(self):
        """Calculate the all energy
        
        Returns:
            energy:
        """
        (L1, L2, M1, M2, G, boxHeight) = self.params
        # Potential energy
        V = L1 * M1* G * np.sin(self.state[2])
        # Kinetic energy
        T = 1/2.0 * M1 * self.state[1]**2.0 + 1/12.0* M2 * L2 **2 * self.state[3]**2 + \
            1/2.0 * M2 * (self.state[1] - self.state[3] * L2/2 * sin(self.state[2]))**2 + \
            1/2.0 * M2 * (self.state[3] * L2/2.0 * cos(self.state[2]))**2
        return V+T
    
    
    def simulate(self,steps=None):
        """Run the simulation with given steps
        """
        if steps is None:
            # iter until failed
            while True:
                R,termination,_ = self.step()
                if termination:
                    print('Termination happened.')
                    break
        else:
            for i in range(steps):
                R,termination,_ = self.step()
                if termination:
                    print('Termination happened.')
                    break
                
    def set_init_state(self,init_state):
       self._init_state = init_state
       self.state = init_state


    def get_init_state(self,for_Q=False):
        """Get simulate init state
        
        Args:
            for_Q: whether return only init state that 
                used in Q-Learning
        """
        if for_Q:
            return self._init_state[2],self._init_state[3]
        else:
            return self._init_state
    
    def get_current_state(self,toShow=False):
        
        if toShow:
            return self.state
        else:
            return self.state[0],self.state[2]
    
    def reset(self,init_state=None):
        """Init the state to begin.
        
        Args:
            init_state: state to start
        """
        if init_state is None:
            self.state = self._init_state
        else:
            self.set_init_state(init_state)
        # clear history 
        self.history = []     
               
        
    def plot_history(self):
        """
            Animate according to simulation history
        """
        if len(self.history) == 0:
            print('You must first simulation')
            return
        # set up initial state and global variables
        dt = 1./30 # 30 fps
        
        #------------------------------------------------------------
        # set up figure and animation
        fig = plt.figure()
        ax = fig.add_subplot(111, aspect='equal', autoscale_on=False,
                             xlim=(-5, 5), ylim=(-1, 3))
        ax.grid()
        
        (L1, L2, M1, M2, G, boxHeight) = self.params
        box = ax.add_patch(patches.Rectangle((0,0),0,0,color='red',animated=True))
        line, = ax.plot([], [], 'o-', lw=6)
        time_text = ax.text(0.02, 0.95, '', transform=ax.transAxes)
        energy_text = ax.text(0.02, 0.85, '', transform=ax.transAxes)

        
        def init():
            """initialize animation"""
            box.set_height(boxHeight)
            box.set_width(L1)
            line.set_data([], [])
            time_text.set_text('')
            energy_text.set_text('')
            return box, line, time_text , energy_text
        
        def animate(i):
            """perform animation step"""
            #print('animation i frame:%d' % i)
            (posX,posY),time_elapsed,energy = self.history[i]
            box.set_x(posX[0] - L1 / 2)
            line.set_data(posX,posY)
            time_text.set_text('time = %.1f' % time_elapsed)
            energy_text.set_text('energy = %.3f J' % energy)
            return box, line, time_text, energy_text
        
        # choose the interval based on dt and the time to animate one step

        t0 = time()
        animate(0)
        t1 = time()
        interval = 1000* dt - (t1 - t0)
        
        ani = animation.FuncAnimation(fig, animate, frames=len(self.history),
                                      interval=interval, blit=True, init_func=init)

        # ani.save('double_pendulum.gif',fps=30,dpi=80,writer='imagemagick')

        plt.show()

        
if __name__ == '__main__':
    pendulum = Invert_Pendulum()
    pendulum.simulate(60)
    pendulum.plot_history()
