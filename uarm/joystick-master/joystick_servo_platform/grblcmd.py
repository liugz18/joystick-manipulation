#coding:utf-8
import serial
from collections import namedtuple


class GrblCmd:
    def __init__(self, serial_port):
        self.serial_port = serial_port
        try:
            self.serial = serial.Serial(serial_port, 115200)
        except:
            raise NameError("cann't open " + serial_port)
        self.g_code_end = '\n'
        self.speed_level_dict = {1: 'F1000', 2: 'F4000', 3: 'F7000'}
        self.current_pos = {'x': 0, 'y': 0}
        self.spindle_state = None
        self.serial_state = 'OPEN'

    @staticmethod
    def level_to_speed(level, speed_level_dict):
        if level is None:
            return ''
        else:
            return speed_level_dict[level]

    def _serial_ok(self):
        if self.serial_state == 'OPEN':
            return True
        else:
            print('Serial is ' + self.serial_state)
            return False

    def write_data(self, g_code):
        self.serial.write((g_code + self.g_code_end).encode('ascii'))

    def spindle_up(self):
        if self.spindle_state in ['DOWN', None]:
            self.write_data('M5')
            self.spindle_state = 'UP'

    def spindle_down(self):
        if self.spindle_state in ['UP', None]:
            self.write_data('M3S1000')
            self.spindle_state = 'DOWN'

    def move_x(self, distance, speed_level=None):
        if self._serial_ok():
            speed_str = self.level_to_speed(speed_level, self.speed_level_dict)
            try:
                self.write_data('G91G0X' + '%.3f' % (distance) + speed_str)
                self.current_pos['x'] += distance
            except:
                print('Movement along x failed')

    def move_y(self, distance, speed_level=None):
        if self._serial_ok():
            speed_str = self.level_to_speed(speed_level, self.speed_level_dict)
            try:
                self.write_data('G91G0Y' + '%.3f' % (distance) + speed_str)
                self.current_pos['y'] += distance
            except:
                print('Movement along y failed')

    def move_xy(self, distance_x, distance_y, speed_level=None):
        if self._serial_ok():
            speed_str = self.level_to_speed(speed_level, self.speed_level_dict)
            try:
                position_str = 'X%.3fY%.3f' % (distance_x, distance_y)
                self.write_data('G91G0' + position_str + speed_str)
                self.current_pos['x'] += distance_x
                self.current_pos['y'] += distance_y
            except:
                print('Movement failed')

    def move_to(self, position, speed_level=None):
        if self._serial_ok():
            speed_str = self.level_to_speed(speed_level, self.speed_level_dict)
            try:
                delta = (position[0] - self.current_pos['x'],
                         position[1] - self.current_pos['y'])
                position_str = 'X%.3fY%.3f' % delta
                self.write_data('G91G0' + position_str + speed_str)
                self.current_pos['x'] += delta[0]
                self.current_pos['y'] += delta[1]
            except TypeError:
                print('Please make sure position is a tuple')
            except:
                print('The movement to ' + ','.join(position) + ' failed')

    def move_to_x(self, x_pos, speed_level=None):
        if self._serial_ok():
            speed_str = self.level_to_speed(speed_level, self.speed_level_dict)
            try:
                delta = x_pos - self.current_pos['x']
                position_str = 'X%.3f' % delta
                self.write_data('G91G0' + position_str + speed_str)
                self.current_pos['x'] += delta
            except TypeError:
                print('Please make sure position is a tuple')
            except:
                print('The movement failed')

    def move_to_y(self, y_pos, speed_level=None):
        if self._serial_ok():
            speed_str = self.level_to_speed(speed_level, self.speed_level_dict)
            try:
                delta = y_pos - self.current_pos['y']
                position_str = 'Y%.3f' % delta
                self.write_data('G91G0' + position_str + speed_str)
                self.current_pos['y'] += delta
            except TypeError:
                print('Please make sure position is a tuple')
            except:
                print('The movement to failed')

    def print_pos(self):
        print('X:%.3f Y:%.3f' % (self.current_pos['x'], self.current_pos['y']))

    def print_status(self):
        self.print_pos()
        if self.spindle_state is not None:
            print('Spindle is ' + self.spindle_state)
        else:
            print('Spindle state is not clear')
        print('Serial is ' + self.serial_state)

    def close_connection(self):
        self.serial.close()
        self.serial_state = 'CLOSED'

    def create_connection(self, serial_port=None):
        if serial_port is not None:
            self.serial_port = serial_port
        self.serial = serial.Serial(self.serial_port, 115200)
        self.serial_state = 'OPEN'

    def go_home(self):
        self.move_to((0, 0))
        self.current_pos = {'x': 0, 'y': 0}

    def set_here_home(self):
        self.current_pos = {'x': 0, 'y': 0}

    def spindle_is_up(self):
        if self.spindle_state == 'UP':
            return True
        else:
            return False
    def spindle_is_down(self):
        if self.spindle_state == 'DOWN':
            return True
        else:
            return False
