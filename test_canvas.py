#!/usr/bin/env python3
# -*- coding: utf-8 -*-

WIDTH = 800
HEIGHT = 600

import tkinter as TK
from tkinter.messagebox import showinfo, showerror, showwarning
from math import sqrt

class Point:
    def __init__(self, x, y):
        self.set(x, y)
    
    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        elif name.upper() == 'X':
            return self._x
        elif name.upper() == 'Y':
            return self._y
        else:
            raise AttributeError('property "{}" not defined'.format(name))
            
    def __setattr__(self, name, val):
        if name.upper() == 'X':
            self.__dict__['_x'] = val
        elif name.upper() == 'Y':
            self.__dict__['_y'] = val
        else:
            raise AttributeError('property "{}" not defined'.format(name))
            
    def __str__(self):
        return '({},{})'.format(self._x, self._y)
    
    def set(self, x, y):
        self.__dict__['_x'] = x
        self.__dict__['_y'] = y
 
class Command:
    CMD_SEP = ' ' 
    SUPPORTED_CMD = ('G0, G1')
    def __init__(self, **kwargs):
        self._cmd_text = kwargs.get('cmd_text', None)
        self._cmd = kwargs.get('cmd', None)
        self._arg_x = kwargs.get('x', None)
        self._arg_y = kwargs.get('y', None)
        self._arg_speed = kwargs.get('f', None)
    
        if not cmd_text == None:
            self.parse(cmd_text)
            
    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        elif name.upper() == 'X':
            return self.__dict__._x
        elif name.upper() == 'Y':
            return self.__dict__._y
        elif name.upper() == 'P':
            return Point(self.__dict__._x, self.__dict__._y)
        elif name.upper() == 'F':
            return self.__dict__._arg_speed
        else:
            raise AttributeError('property "{}" not defined'.format(name))
        
    def check(self):
        return True
    
    def parse(self, cmd_text):
        # <CMD> [X<val>] [Y<val>] [F<val>]
        items = cmd_text.strip().upper().split(Command.CMD_SEP, 1)
        if len(items) == 0:
            # empty string
            raise Exception('can not parse "{}", command is empty'.format(cmd_text))
        elif len(items) == 1:
            # no args
            self._cmd = items[0].strip()
        else:
            self._cmd = items[0].strip()
            # parse args
            for item in items[1].strip().split(Command.CMD_SEP):
                t = item.strip()
                if t:
                    pref = t[0]
                    try:
                        amount = float(t[1:])
                    except Exception as e:
                        raise Exception('can not parse "{}", argument "{}" is invalid'.format(cmd_text, t))
                    if pref == 'X':
                        self._arg_x = amount
                    elif pref == 'Y':
                        self._arg_y = amount
                    elif pref == 'F':
                        self._arg_speed = amount
    
class Carriage:
    def __init__(self, width, height, left_bound_x, right_bound_x):
        self.width = width
        self.height = height
        self.half_width = self.width / 2
        self.half_height = self.height / 2
        # ropes bound points
        self.left_bound_x = left_bound_x
        self.right_bound_x = right_bound_x
        # ropes attachment points
        self.left_attpoint = Point(0.0, 0.0)
        self.right_attpoint = Point(0.0, 0.0)
        # ropes lengths
        self.left_rope = 0.0
        self.right_rope = 0.0
        # calculated pen position
        self.pen_pos = Point(0.0, 0.0)
        
        self.calc_position(canvas.width / 2, canvas.height / 2)
        
    def attpoint_from_pos(self, x, y, left):
        if left:
            return Point(x - self.half_width, y - self.half_height)
        else:
            return Point(x + self.half_width, y - self.half_height)
    
    def calc_position(self, target_x, target_y):
        #print('llen={}, rlen={}'.format(left_len, right_len))
        # calc length of left rope
        attp = self.attpoint_from_pos(target_x, target_y, True)
        f_llen = sqrt((attp.x - self.left_bound_x) ** 2 + attp.y ** 2)
        del(attp)
        # calc length of right rope
        attp = self.attpoint_from_pos(target_x, target_y, False)
        f_rlen = sqrt((self.right_bound_x - attp.x) ** 2 + attp.y ** 2)
        del(attp)
        # calc coordinates of carriage attachment poins
        f_lx = (f_llen ** 2 - f_rlen ** 2 + (self.canvas.width - self.width) ** 2) / (2 * (self.canvas.width - self.width))
        f_y = sqrt(f_llen ** 2 - f_lx ** 2)
        f_rx = float(self.canvas.width) - sqrt(f_rlen ** 2 - f_y ** 2)
        #print('w={}'.format(f_rx - f_lx))
        self.left_attpoint.set(f_lx, f_y)
        self.right_attpoint.set(f_rx, f_y)
        # calc pen position
        self.pen_pos.set(f_lx + (f_rx - f_lx) / 2, f_y + self.half_height)
        # redraw
        self.redraw()
    
    def get_position(self, precision = None):
        if precision == None:
            return (self.pen_pos.x, self.pen_pos.y) 
        else:
            return (round(self.pen_pos.x, precision), round(self.pen_pos.y, precision))

class Visualiser(TK.Canvas):
    def __init__(self, parent, width, height):
        self.tag = 'stats'

        super().__init__(parent) #, width = self.canvas_width, height = self.canvas_height)
        self.parent = parent
        self.width = width
        self.height = height
        self.bot_width = width
        self.bot_height = height
        self.x_scale = 1.0
        self.y_scale = 1.0
        
        self.configure(width = self.width, height = self.height, background = "white", borderwidth = 0)

    def init(self, width, height, att_dist, offset_y):
        # called by controler when object of this class added to controler's executioners list
        self.bot_width = width
        self.bot_height = height
        # distance
        self.bot_att_dist = att_dist
        self.bot_offset_y = offset_y
        # scale
        self.x_scale = self.width / self.bot_width
        self.y_scale = self.height / self.bot_height
        #print(self.scale_x , self.scale_y)
    
    def line(self, x0, y0, x1, y1, **kwargs):
        #print('({},{})-({},{})'.format(x0, y0, x1, y1))
        self.create_line(x0, y0, x1, y1, kwargs)
    
    def rect(self, x0, y0, x1, y1, **kwargs):
        self.create_rectangle(x0, y0, x1, y1, kwargs)
    
    def cross(self, x, y, size, **kwargs):
        # hor line
        self.create_line(x - size // 2, y, x + size // 2, y, kwargs)
        # vert line
        self.create_line(x, y - size // 2, x, y + size // 2, kwargs)
    
    def scale_x(self, v):
        return round(v * self.x_scale)
        
    def scale_y(self, v):
        return round(v * self.y_scale)
    
    def update(self, left_len, right_len):
        # calc coordinates of carriage attachment poins
        #print(left_len, right_len)
        f_w = self.bot_width - self.bot_att_dist
        f_lx = (left_len ** 2 - right_len ** 2 + f_w ** 2) / (2 * f_w)
        f_y = sqrt(left_len ** 2 - f_lx ** 2)
        f_rx = self.bot_width - sqrt(right_len ** 2 - f_y ** 2)
        # calc tool position
        f_tx = f_lx + (f_rx - f_lx) / 2
        f_ty = f_y + self.bot_offset_y
        # redraw
        self.delete(self.tag)
        # aim
        self.rect(self.scale_x(f_tx) - 1, self.scale_y(f_ty) - 1, self.scale_x(f_tx) + 1, self.scale_y(f_ty) + 1, outline = 'blue', tag = self.tag)
        # left rope
        self.line(0, 0, self.scale_x(f_lx), self.scale_y(f_y), tag = self.tag, fill = 'red')
        # right rope
        self.line(round(self.width), 0, self.scale_x(f_rx), self.scale_y(f_y), tag = self.tag, fill = 'red')
        # update stats
        self.create_text(self.width // 2, 10, tag = self.tag, text = 'target x,y={}'.format((f_tx, f_ty)))
    
    def set_pen(self, state = True):
        self._enable_pen = state
      
class PolarBot:
    DEFAULT_SPEED = 100
    
    def __init__(self, controler, **kwargs):
        self._executor = []
        self._controler = controler
        self.area_width = kwargs.get('width', 800)
        self.area_height = kwargs.get('height', 600) 
        # position of robot's tool (pen)
        self.tool_position = Point(self.area_width / 2, self.area_height / 2)
        # distance between left attachment point of robot's carriage and tool position on x axis
        self.left_offset_x = kwargs.get('left_offset', self.area_width / 20)
        # distance between right attachment point of robot's carriage and tool position on x axis
        self.right_offset_x = kwargs.get('right_offset', self.area_width / 20)
        # distance between left and right attachment points
        self.att_distance = self.left_offset_x + self.right_offset_x
        # distance between attachment points of robot's carriage and tool position on y axis
        self.offset_y = kwargs.get('y_offset', self.area_height / 20)
        # ropes bound points
        self.left_bound_x = 0.0
        self.right_bound_x = float(self.area_width)
        # ropes lengths to reach target tool position
        self.left_rope_len, self.right_rope_len = self.calc_ropes(self.tool_position)
        # ropes lengths to reach target tool position
        self.tg_left_rope_len = self.left_rope_len
        self.tg_right_rope_len = self.right_rope_len
        # rope lengths deltas
        self.left_delta = 0.0
        self.right_delta = 0.0
        # steps
        self.left_step = 0.0
        self.right_step = 0.0
        #
        self.curent_cmd = None

        # register actions
        self._controler.register_action('tick', self.on_tick)
        self._controler.register_action('move_to', self.on_move_to)

    def calc_ropes(self, tg_point):
        # calc length of left rope
        f_llen = sqrt(((tg_point.x - self.left_offset_x) - self.left_bound_x) ** 2 + (tg_point.y - self.offset_y) ** 2)
        #self.left_rope_len = f_llen
        # calc length of right rope
        f_rlen = sqrt((self.right_bound_x - (tg_point.x + self.right_offset_x)) ** 2 + (tg_point.y - self.offset_y) ** 2)
        #self.right_rope_len = f_rlen
        return (f_llen, f_rlen)
        
    def update(self):
        # update executioners
        for ex in self._executor:
            try:
                #print(ex)
                ex.update(self.left_rope_len, self.right_rope_len)
            except Exception as e:
                print(e)
        
    def add_executor(self, ex):
        try:
            ex.init(self.area_width, self.area_height, self.att_distance, self.offset_y)
            self._executor.append(ex)
        except Exception as e:
            print(e)
        self.update()
        
    def rem_executor(self, ex):
        if ex in self._executor:
            del(self._executor[self._executor.index(ex)])
            
    def load_program(self, data):
        pass
        
    def execute(self, cmd):
        self.curent_cmd = cmd
        # calc ropes lengths to reach targer tool pos
        self.tg_left_rope_len, self.tg_right_rope_len = self.calc_ropes(cmd.p)
        # calc deltas between new lengths and current
        ld = self.tg_left_rope_len - self.left_rope_len
        rd = self.tg_right_rope_len - self.right_rope_len
        # get speed in ticks to reach target point
        speed = cmd.f if cmd.f else PolarBot.DEFAULT_SPEED
        # calc steps in each tick
        self.left_step = ld / speed
        self.right_step  = rd / speed
    # EVENTS
    def on_tick(self):
        #print('tick')
        if self.curent_cmd:
            pass
        
    def on_move_to(self, x, y):
        print('move_to({},{})'.format(x, y))
        self.execute(Command(cmd = 'G0', x = x, y = y, f = PolarBot.DEFAULT_SPEED))
        
class ControlPanel(TK.Frame):
    ACTIONS = ('TICK', 'MOVE_TO', 'PROG_RUN')
    TICK_INTERVAL = 1000
    def __init__(self, parent, **kwargs):
        super().__init__(parent) #, width = self.canvas_width, height = self.canvas_height)
        self.parent = parent
        self._actions = {}
        self.tick_interval = kwargs.get('tick_interval', ControlPanel.TICK_INTERVAL)
        # self.width = width
        # self.height = height
        #self.configure(width = self.width, height = self.height)
        #self.pack() #ipadx = 10, ipady = 10)       
        # create controls
        self.lb_x = TK.Label(self, text = 'GO TO X')
        self.lb_x.grid(row = 0, column = 0)
        self.ed_x = TK.Entry(self, width = 5)
        self.ed_x.grid(row = 0, column = 1)
        self.lb_y = TK.Label(self, text = 'Y')
        self.lb_y.grid(row = 0, column = 2)
        self.ed_y = TK.Entry(self, width = 5)
        self.ed_y.grid(row = 0, column = 3)
        # text fields
        self.txt_prog = TK.Text(self, width = 20)
        self.txt_prog.grid(columnspan = 4, sticky = TK.W + TK.E + TK.N + TK.S)
        # buttond
        self.btn_run = TK.Button(self, text = 'RUN')
        self.btn_run.grid(columnspan = 4, sticky = TK.W + TK.E + TK.N + TK.S)
        self.ed_y.bind('<Key>', self.edXY_on_key_enter)
        self.ed_x.bind('<Key>', self.edXY_on_key_enter)

        # start ticking
        self.after(self.tick_interval, self.tick)

    def register_action(self, name, action):
        if not name.upper() in ControlPanel.ACTIONS:
            raise Exception('invalid action name "{}". must be one of {}'.format(name, ControlPanel.ACTIONS))
        self._actions[name.upper()] = action
    
    def unregister_action(self, name):
        if name.upper() in self._actions:
            del(self._actions[name.upper()])
    
    def raise_action(self, name, *args):
        if name in self._actions:
            try:
                self._actions[name](*args)
            except Exception as e:
                raise Exception('there was an exception while execute action "{}" witch params {}, becase:{}'.format(name, args, e))
    
    def tick(self):
        #print('--> tick()')
        self.raise_action('TICK')
        self.after(self.tick_interval, self.tick)
        #print('<-- tick()')

    
    def edXY_on_key_enter(self, event):
        #print(event)
        if event.keycode == 13:
            # "Enter" key pressed
            try:
                x = int(self.ed_x.get())
                y = int(self.ed_y.get())
            except Exception as e:
                showerror(message = 'invalid symbols in edit fields for X and Y')
                return
            self.raise_action('MOVE_TO', x, y)
        
if __name__ == '__main__':
    # main window
    root = TK.Tk()
    # bot visualiser
    vis = Visualiser(root, WIDTH, HEIGHT)
    # control panel
    cp = ControlPanel(root)
    # place controls on the main window
    vis.grid(row = 1, column = 1)
    cp.grid(row = 1, column = 2, sticky = TK.W + TK.E + TK.N + TK.S)
    # man bot controler
    pb = PolarBot(cp, width = 1000, height = 2000)
    # add visualiser as executor
    pb.add_executor(vis)
    # enter main loop
    root.mainloop()