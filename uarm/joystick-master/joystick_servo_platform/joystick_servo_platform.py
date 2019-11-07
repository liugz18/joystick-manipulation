#coding:utf-8
from __future__ import division
import sys
import time
import ctypes
from collections import OrderedDict
import sdl2
import sdl2.ext
import sdl2.sdlttf
from sdl2 import *
from sdl2.sdlttf import TTF_OpenFont, TTF_RenderText_Solid, TTF_CloseFont, TTF_Init, TTF_Quit
from serial.tools.list_ports import comports
import cv2
import numpy as np
from grblcmd import GrblCmd
import pdb

WHITE = sdl2.ext.Color(255, 255, 255)
LIGHT_WHITE = sdl2.ext.Color(200, 200, 200)
GRAY = sdl2.ext.Color(100, 100, 100)
BLACK = sdl2.ext.Color(0, 0, 0)
RED = sdl2.ext.Color(255, 0, 0)

SDL_BLACK = sdl2.pixels.SDL_Color(0, 0, 0)
SDL_RED = sdl2.pixels.SDL_Color(255, 0, 0)
SDL_GREEN = sdl2.pixels.SDL_Color(0, 255, 0)
SDL_BLUE = sdl2.pixels.SDL_Color(0, 0, 255)
SDL_GRAY = sdl2.pixels.SDL_Color(180, 180, 180)

SDL_SCANCODE_NUM_LIST = [
    SDL_SCANCODE_0, SDL_SCANCODE_1, SDL_SCANCODE_2, SDL_SCANCODE_3,
    SDL_SCANCODE_4, SDL_SCANCODE_5, SDL_SCANCODE_6, SDL_SCANCODE_7,
    SDL_SCANCODE_8, SDL_SCANCODE_9
]

QUIT = True
# max value of joystick's axis
AXISMAXVALUE = 32768
# limit of the motion of platform in one direction
PLATFORM_LIMIT = 20


def get_serial_port():
    return [com.device for com in comports()]

def get_touch_sensor_list(maxnum=3, ignore_webcam=True):
    device_accessible = []
    for i in range(maxnum):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if not cap.read()[0]:
            break
        else:
            device_accessible.append(i)
            cap.release()
    cv2.destroyAllWindows()
    # ignore the webcam
    return device_accessible[1:] if ignore_webcam else device_accessible


def loadTexture(filepath, renderer):
    if isinstance(filepath, str):
        filepath = filepath.encode('utf8')
    loaded_image = sdl2.sdlimage.IMG_Load(filepath)
    texture = SDL_CreateTextureFromSurface(renderer, loaded_image)
    return texture

def load_CV_images_to_window(cv_image, window):
    window_surface = SDL_GetWindowSurface(window)
    surface_texture_array = sdl2.ext.pixels3d(window_surface.contents)
    image = np.insert(cv_image, 3, 255, axis=2)
    # image = np.rot90(image)
    np.copyto(surface_texture_array, image)

def renderTexture(texture, render, x, y):
    dst = SDL_Rect()
    dst.x, dst.y = x, y
    w, h = ctypes.c_int(), ctypes.c_int()
    SDL_QueryTexture(texture, None, None, w, h)
    dst.w, dst.h = w, h
    SDL_RenderCopy(render, texture, None, dst)


def renderTextureScale(texture, render, x, y, w, h):
    dst = SDL_Rect()
    dst.x, dst.y = x, y
    dst.w, dst.h = w, h
    SDL_RenderCopy(render, texture, None, dst)


def renderText(message, ttffont, color, renderer):
    message = message.encode('utf8') if isinstance(message, str) else message
    surf = TTF_RenderText_Solid(ttffont, message, color)
    texture = SDL_CreateTextureFromSurface(renderer, surf)
    SDL_FreeSurface(surf)
    return texture


class MessageManager:
    def __init__(self, renderer, window, fontdict):
        self.renderer = renderer
        self.window = window
        self.time = None
        #TODO
    def renderMessage(self, type_message):
        pass
        # if type_message is not None:
        #     color = SDL_RED if type_message == 'warning' else SDL_BLUE
        #     txt_texture = renderText(type_message[1], ttffont, color, renderer)
        #     # offset is added here to make the text is in the almost middle of the window
        #     renderTexture(txt_texture, renderer, int(window_size_width/2) - 5 * len(type_message), int(window_size_height/2) - 3)

class JoystickController:
    def __init__(self):
        sdl2.SDL_Init(SDL_INIT_JOYSTICK | SDL_INIT_TIMER)
        self.device = None
        self.button = {}
        # L - Left, R - Right, H - Horizontal, V - Vertical, B - Button
        self.axis_map = {0: 'L_H', 1: 'L_V', 2: 'L_B', 3: 'R_H', 4: 'R_V', 5: 'R_B'}
        # set value of axes to 0s
        self.axis = {}.fromkeys(self.axis_map.values(), 0)

        self.button_map = {0: 'A', 1: 'B', 2: 'X', 3: 'Y', 4: 'L', 5:'R'}
        # U - Up, R - Right, D - Down, L - Left, UR - UpRight ...
        self.hat_map = {
            0: 'Release',
            1: 'U',
            2: 'R',
            3: 'UR',
            4: 'D',
            6: 'RD',
            8: 'L',
            9: 'UL',
            12: 'DL'
        }
        # connection between the joystick and the servo platforms
        self.con_left = None
        self.con_right = None
        self.current_con = None
        # 100ms between operationcmd updating
        self.cmd_update_rate = 100

    def close_connections(self):
        if self.con_left is not None:
            self.con_left.close_connection()
            self.con_left = None
        if self.con_right is not None:
            self.con_right.close_connection()
            self.con_right = None

    def swap_connections(self):
        self.con_left, self.con_right = self.con_right, self.con_left

    def shock_spindle(self):
        if self.con_left is not None:
            self.con_left.spindle_up()
            time.sleep(0.1)
            self.con_left.spindle_down()
        if self.con_right is not None:
            self.con_right.spindle_up()
            time.sleep(0.1)
            self.con_right.spindle_down()

    def update(self, event):
        if event.type == sdl2.SDL_JOYDEVICEADDED:
            self.device = sdl2.SDL_JoystickOpen(event.jdevice.which)
            return ('info', 'The joystick is connected')
        elif event.type == sdl2.SDL_JOYDEVICEREMOVED:
            self.device = None
            return ('info', 'The joystick is removed')
        elif event.type == sdl2.SDL_JOYAXISMOTION:
            # print(self.axis_map[event.jaxis.axis], event.jaxis.value)
            # ignore left up button
            self.axis[self.axis_map[
                event.jaxis.axis]] = event.jaxis.value / AXISMAXVALUE
            # move the platform
            button_and_type = self.axis_map[event.jaxis.axis]
            con = None
            if button_and_type[0] == 'R':
                if self.con_right is not None:
                    con = self.con_right
            else:
                if self.con_left is not None:
                    con = self.con_left
            if con is not None:
                if button_and_type[-1] == 'H':
                    action = 'move_to_x'  
                elif button_and_type[-1] == 'V':
                    action = 'move_to_y'
                else:
                    if event.jaxis.value > 0:
                        con.spindle_up()
                    else:
                        con.spindle_down()
                    return 
                value = event.jaxis.value / AXISMAXVALUE * PLATFORM_LIMIT
                getattr(con, action)(value)
            else:
                return ('info', 'The servo platforms are not connected.')

        elif event.type == sdl2.SDL_JOYBUTTONDOWN:
            # print("Button down:", event.jbutton.button)
            self.button[self.button_map[event.jbutton.button]] = True
            btn = self.button_map[event.jbutton.button]
            if btn == 'A':
                self.current_con = self.con_left
            elif btn == 'B':
                self.current_con = self.con_right
            elif btn == 'X':
                if self.current_con is not None:
                    self.current_con.go_home()
                else:
                    return ('warning',
                            'Please select target you want to operate first.')
            elif btn == 'Y':
                if self.current_con is not None:
                    self.current_con.set_here_home()
                else:
                    return ('warning',
                            'Please select target you want to operate first.')

        elif event.type == sdl2.SDL_JOYBUTTONUP:
            # print("Button up:", event.jbutton.button)
            self.button[self.button_map[event.jbutton.button]] = False
        elif event.type == sdl2.SDL_JOYHATMOTION:
            # print("Hat motion",self.hat_map[event.jhat.value])
            hat_value = self.hat_map[event.jhat.value]
            if self.current_con is not None:
                sign = 1 if self.current_con is self.con_left else -1
                if hat_value == 'D':
                    self.current_con.move_y(1 * sign)
                elif hat_value == 'U':
                    self.current_con.move_y(-1 * sign)
                elif hat_value == 'L':
                    self.current_con.move_x(1 * sign)
                elif hat_value == 'R':
                    self.current_con.move_x(-1 * sign)
            else:
                return ('warning',
                        'Please select target you want to operate first.')

def main(video_filename):
    sdl2.ext.init()
    SDL_Init(SDL_INIT_VIDEO)
    SDL_Init(SDL_INIT_JOYSTICK)
    TTF_Init()
    window_size_width = 800
    window_size_height = 400
    image_width = 320
    image_height = 240
    border_width = 50
    axis_animation_range = 300
    window = SDL_CreateWindow(b"Joystick Servo Platform", 
                                100,
                                100, 
                                window_size_width,
                                window_size_height, 
                                SDL_WINDOW_SHOWN)
    renderer = SDL_CreateRenderer(
        window, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC)
    window_sensors = sdl2.ext.Window("Sensor Images", size=(image_width * 2, image_height))
    

    RESOURCES = sdl2.ext.Resources(__file__, "resources")
    # load background
    path = RESOURCES.get_path('circle.png').encode('utf8')
    texture_operation = loadTexture(path, renderer)
    # load help image
    path = RESOURCES.get_path('help.png').encode('utf8')
    texture_help = loadTexture(path, renderer)
    # load axis image
    path = RESOURCES.get_path('axis.png').encode('utf8')
    texture_axis = loadTexture(path, renderer)
    texture_axis_w, texture_axis_h = ctypes.c_int(), ctypes.c_int()
    SDL_QueryTexture(texture_axis, None, None, texture_axis_w, texture_axis_h)
    texture_axis_w, texture_axis_h = texture_axis_w.value, texture_axis_h.value
    # load font
    fontfile = RESOURCES.get_path('arialbd.ttf').encode('utf8')
    fontsize = 14
    ttffont = TTF_OpenFont(fontfile, fontsize)
    # instructions to be shown on the gui
    instructions = [
        '=============== Menu =================',
        'Choose serial port for left platform, then for right platform, using number',
        'Press "s" to swap serial connections',
        'Press "c" to close all serial connections',
        'Press "t" to test connections',
        'Press "h" to show or hide the picture of the usage of joystick'
    ]
    instructions_sensor = [
        '---------------- ',
        'Choose sensor for the left, then for the right, using (a,b)',
        'Press "v" to show images from touch sensor',
        'Press "x" to exchange images from sensor',
        'Prsss "M" to write image to file',
        'Press "N" to stop write image to file',
        'Press "q" to quit'
    ]
    h_offset = 15
    selected_ports = OrderedDict({'Left': None, 'Right': None})
    selected_sensors = OrderedDict({'Left Sensor': None, 'Right Sensor': None})
    avaliable_ports = get_serial_port()
    joystick = JoystickController()
    start_position = (10, 10)
    def list_infos(pre_info, info_list, dev_list, selected_items, start_position, h_offset, use_alpha=False):
        for index, item in enumerate(pre_info):
            txt_texture = renderText(item, ttffont, SDL_BLACK, renderer)
            renderTexture(txt_texture, renderer, start_position[0], start_position[1] + index * h_offset)
        if len(dev_list) > 0:
            port_str = info_list[0]
        else:
            port_str = info_list[1]
        txt_texture = renderText(port_str, ttffont, SDL_BLACK, renderer)
        renderTexture(txt_texture, renderer, start_position[0],
                      start_position[1] + h_offset * len(pre_info))
        for index, port in enumerate(dev_list):
            if use_alpha:
                index_char = chr(index + 97)
            else:
                index_char = str(index)
            port_str = ' ' * 9 + '[' + index_char + ']' + str(port)
            txt_texture = renderText(port_str, ttffont, SDL_BLACK, renderer)
            renderTexture(txt_texture, renderer, start_position[0],
                          start_position[1] + h_offset * (len(pre_info) + 1 + index))

        for index, (platform_index, port) in enumerate(selected_items.items()):
            if port is None:
                port_str = 'None'
                color = SDL_RED
            else:
                port_str = str(port)
                color = SDL_GREEN
            txt_texture = renderText(platform_index + ':' + port_str, ttffont,
                                     color, renderer)
            renderTexture(
                txt_texture, renderer, start_position[0], start_position[1] + h_offset *
                (len(pre_info) + 1 + len(dev_list) + index))

    list_infos(instructions,
        ['Avaliable serial ports:', 'No serial port avaliable'] ,
        get_serial_port(), 
        selected_ports, 
        start_position,
        h_offset)
    # just get the usb touch sensor list only once to save time and didn't use the win32api
    avaliable_touch_sensors = get_touch_sensor_list()
    print(avaliable_touch_sensors)
    start_position_sensor = start_position[0], start_position[1] + 180
    list_infos(instructions_sensor,
            ['Avaliable sensors:', 'No sensors avaliable'] ,
            avaliable_touch_sensors,
            selected_sensors,
            start_position_sensor,
            h_offset)
    
    event = sdl2.SDL_Event()
    show_help_picture = False
    running = True
    # joystick_message = None
    show_sensors_images = False
    sensor_left_cap, sensor_right_cap = None, None
    sensor_left_writer, sensor_right_writer = None, None
    while running:
        while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == SDL_KEYDOWN:
                keyboard_state = SDL_GetKeyboardState(None)
                if keyboard_state[SDL_SCANCODE_S]:
                    selected_ports['Left'], selected_ports[
                        'Right'] = selected_ports['Right'], selected_ports[
                            'Left']
                    joystick.swap_connections()
                elif keyboard_state[SDL_SCANCODE_H]:
                    show_help_picture = not show_help_picture
                elif keyboard_state[SDL_SCANCODE_C]:
                    selected_ports['Left'], selected_ports[
                        'Right'] = None, None
                    joystick.close_connections()
                elif keyboard_state[SDL_SCANCODE_T]:
                    joystick.shock_spindle()
                elif keyboard_state[SDL_SCANCODE_A]:
                    if len(avaliable_touch_sensors) < 1:
                        break
                    sensor = avaliable_touch_sensors[0]
                    if sensor_left_cap is None:
                        sensor_left_cap = cv2.VideoCapture(sensor, cv2.CAP_DSHOW)
                        index = 'Left Sensor'
                    else:
                        sensor_right_cap = cv2.VideoCapture(sensor, cv2.CAP_DSHOW)
                        index = 'Right Sensor'
                    selected_sensors[index] = sensor
                    
                elif keyboard_state[SDL_SCANCODE_B]:
                    if len(avaliable_touch_sensors) < 2:
                        break
                    sensor = avaliable_touch_sensors[1]
                    if sensor_left_cap is None:
                        sensor_left_cap = cv2.VideoCapture(sensor, cv2.CAP_DSHOW)
                        index = 'Left Sensor'
                    else:
                        sensor_right_cap = cv2.VideoCapture(sensor, cv2.CAP_DSHOW)
                        index = 'Right Sensor'
                    selected_sensors[index] = sensor
                elif keyboard_state[SDL_SCANCODE_V]:
                    if sensor_right_cap is not None or sensor_left_cap is not None:
                        show_sensors_images = True
                        window_sensors.show()
                    if sensor_right_cap is not None:
                        sensor_right_cap.set(3, 320)
                        sensor_right_cap.set(4, 240)
                    if sensor_left_cap is not None:
                        sensor_left_cap.set(3, 320)
                        sensor_left_cap.set(4, 240)
                        # print('press V')
                elif keyboard_state[SDL_SCANCODE_M]:
                    writer_num = 0
                    if sensor_right_cap is not None:
                        fps = sensor_right_cap.get(cv2.CAP_PROP_FPS)
                        width = sensor_right_cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                        height = sensor_right_cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                        sensor_right_writer = cv2.VideoWriter(video_filename + '_right.avi',
                                                              cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                                                              30,
                                                              (int(width), int(height)))
                        print('Writing right sensor''s image.')
                    if sensor_left_cap is not None:
                        fps = sensor_left_cap.get(cv2.CAP_PROP_FPS)
                        width = sensor_left_cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                        height = sensor_left_cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                        print('fps,w,h:',fps, width, height)
                        sensor_left_writer = cv2.VideoWriter(video_filename + '_left.avi',
                                                              cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                                                             30,
                                                            (int(width), int(height)))
                        print('Writing left sensor''s image.')
                elif keyboard_state[SDL_SCANCODE_N]:
                    sensor_writer_exist = False
                    if sensor_right_writer is not None:
                        sensor_right_writer.release()
                        sensor_right_writer = None
                        sensor_writer_exist = True
                    if sensor_left_writer is not None:
                        sensor_left_writer.release()
                        sensor_left_writer = None
                        sensor_writer_exist = True
                    if sensor_writer_exist:
                        print('All video writers are closed')
                elif keyboard_state[SDL_SCANCODE_X]:
                    sensor_left_cap, sensor_right_cap = sensor_right_cap, sensor_left_cap
                elif keyboard_state[SDL_SCANCODE_Q]:
                    running = False
                    break
                # num key
                elif event.key.keysym.scancode in SDL_SCANCODE_NUM_LIST:
                    # pdb.set_trace()
                    num = SDL_SCANCODE_NUM_LIST.index(
                        event.key.keysym.scancode)
                    if num < len(avaliable_ports) and avaliable_ports[num] not in selected_ports.values() and\
                         None in selected_ports.values():
                        for index, value in selected_ports.items():
                            if value is None:
                                if index == 'Left':
                                    joystick.con_left = GrblCmd(
                                        avaliable_ports[num])
                                else:
                                    joystick.con_right = GrblCmd(
                                        avaliable_ports[num])
                                selected_ports[index] = avaliable_ports[num]
                                break
            elif event.type == sdl2.SDL_QUIT:
                running = False
            else:
                joystick_message = joystick.update(event)
                # print(event.type, event.key)
        SDL_RenderClear(renderer)
        # draw background
        if show_help_picture:
            renderTexture(texture_help, renderer, 0, 0)
        else:
            renderTexture(texture_operation, renderer, 0, 0)
            # draw axis poles
            x_L_axis = int(border_width + axis_animation_range / 2 +
                           joystick.axis['L_H'] * axis_animation_range / 2 -
                           texture_axis_w / 2)
            y_L_axis = int(border_width + axis_animation_range / 2 +
                           joystick.axis['L_V'] * axis_animation_range / 2 -
                           texture_axis_h / 2)
            renderTexture(texture_axis, renderer, x_L_axis, y_L_axis)
            x_R_axis = int(window_size_width -
                           (border_width + axis_animation_range / 2) +
                           joystick.axis['R_H'] * axis_animation_range / 2 -
                           texture_axis_w / 2)
            y_R_axis = int(border_width + axis_animation_range / 2 +
                           joystick.axis['R_V'] * axis_animation_range / 2 -
                           texture_axis_h / 2)
            renderTexture(texture_axis, renderer, x_R_axis, y_R_axis)
        # draw help info and the serial port info
        
        list_infos(instructions,
            ['Avaliable serial ports:', 'No serial port avaliable'] ,
            get_serial_port(),
            selected_ports,
            start_position,
            h_offset)
        list_infos(instructions_sensor,
            ['Avaliable sensors:', 'No sensors avaliable'] ,
            avaliable_touch_sensors,
            selected_sensors,
            start_position_sensor,
            h_offset, use_alpha=True)
        # joystick connection status
        if joystick.device is not None:
            color = SDL_BLUE
            joystick_state_text = 'Joystick'
        else:
            color = SDL_GRAY
            joystick_state_text = 'Joystick'
        txt_texture = renderText(joystick_state_text, ttffont, color, renderer)
        # shown on right corner
        renderTexture(txt_texture, renderer,
                      window_size_width - 10 * len(joystick_state_text), 10)

        SDL_RenderPresent(renderer)

        # get pictures
        if show_sensors_images:
            total_image = np.zeros((image_width * 2, image_height, 3), dtype=np.uint8)
            if sensor_left_cap is not None:
                ret, left_image = sensor_left_cap.read()
                if ret:
                    if sensor_left_writer is not None:
                        sensor_left_writer.write(left_image)
                    total_image[:image_width,:,:] = np.rot90(left_image)
            if sensor_right_cap is not None:
                # pdb.set_trace()
                ret, right_image = sensor_right_cap.read()
                if ret:
                    if sensor_right_writer is not None:
                        sensor_right_writer.write(right_image)
                    total_image[image_width:,:,:] = np.rot90(right_image)
            load_CV_images_to_window(total_image, window_sensors.window)
            window_sensors.refresh()

    TTF_CloseFont(ttffont)
    SDL_DestroyTexture(texture_operation)
    SDL_DestroyRenderer(renderer)
    SDL_DestroyWindow(window)
    SDL_Quit()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        video_filename = 'sample'
    else:
        video_filename = sys.argv[1]
    main(video_filename)