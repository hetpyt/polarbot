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
        if name.upper() == 'X':
            return self._x
        elif name.upper() == 'Y':
            return self._y
        else:
            raise AttributeError('property "{}" not defined'.format(name))
            
    def __setattr__(self, name, val):
        if name.upper() == 'X':
            self._x = val
        elif name.upper() == 'Y':
            self._y = val
        else:
            raise AttributeError('property "{}" not defined'.format(name))
            
    def __str__(self):
        return '({},{})'.format(self._x, self._y)
    
    def set(self, x, y):
        self.__dict__['_x'] = x
        self.__dict__['_y'] = y
 
class Command:
    self.CMD_SEP = ' ' 
    self.SUPPORTED_CMD = ('G0, G1')
    def __init__(self, cmd_text = None):
        self._cmd = None
        self._arg_x = None
        self._arg_y = None
        self._arg_speed = None
    
        if not cmd_text == None:
            self.parse(cmd_text)
            
    def check(self):
        return True
    
    def parse(self, cmd_text):
        # <CMD> [X<val>] [Y<val>] [F<val>]
        items = cmd_text.strip().upper().split(Command.CMD_SEP, 1)
        if len(items) == 0:
            # empty string
            raise Exception('can not parse "{}", command is empty'.format(cmd_text))
        elif len(items) == 1
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
    def __init__(self, canvas, width, height, tag = 'carriage'):
        self.canvas = canvas
        self.width = width
        self.height = height
        self.tag = tag
        self.half_width = self.width / 2
        self.half_height = self.height / 2
        # ropes bound points
        self.left_bound_x = 0.0
        self.right_bound_x = float(self.canvas.width)
        # ropes attachment points
        self.left_attpoint = Point(0.0, 0.0)
        self.right_attpoint = Point(0.0, 0.0)
        # ropes lengths
        self.left_rope = 0.0
        self.right_rope = 0.0
        # calculated pen position
        self.pen_pos = Point(0.0, 0.0)
        
        self.calc_position(canvas.width / 2, canvas.height / 2)
        
    def redraw(self):
        self.canvas.delete(self.tag)
        # bounds
        self.canvas.rect(round(self.pen_pos.x - self.half_width), round(self.pen_pos.y - self.half_height), round(self.pen_pos.x + self.half_width), round(self.pen_pos.y + self.half_height), outline = 'blue', tag = self.tag)
        # aim
        self.canvas.rect(round(self.pen_pos.x - 1), round(self.pen_pos.y - 1), round(self.pen_pos.x + 1), round(self.pen_pos.y + 1), outline = 'blue', tag = self.tag)
        # left rope
        self.canvas.line(round(self.left_bound_x), 0, round(self.left_attpoint.x), round(self.left_attpoint.y), tag = self.tag, fill = 'red')
        # right rope
        self.canvas.line(round(self.right_bound_x), 0, round(self.right_attpoint.x), round(self.right_attpoint.y), tag = self.tag, fill = 'red')
        #self.canvas.cross(round(f_lx), round(f_y), 10, tag = 'calc_attpoint', fill = 'green')
        #self.canvas.cross(round(f_rx), round(f_y), 10, tag = 'calc_attpoint', fill = 'green')
    
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
        self.stats_tag = 'stats'
        self.interval_ms = 1000

        super().__init__(parent) #, width = self.canvas_width, height = self.canvas_height)
        self.parent = parent
        self.width = width
        self.height = height
        self.configure(width = self.width, height = self.height, background = "white", borderwidth = 0)
        #self.pack() #ipadx = 10, ipady = 10)
        #self.place(x = 10, y = 10)
        #self.create_rectangle(2, 2, self.width, self.width, outline = "black", fill = "white")
        #self.line(0, 0, 10, 0, fill = "black", tag = 'test_line')    
        self.after(self.interval_ms, self.tick)
        # создаем объект каретки робота
        self.carriage = Carriage(self, self.width // 10, self.height // 10, 'carriage')
        self.cur_x, self.cur_y = self.carriage.get_position()

    
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
    
    def update(self):
        self.carriage.calc_position(self.cur_x, self.cur_y)
        # update stats
        self.delete(self.stats_tag)
        self.create_text(self.width // 2, 10, tag = self.stats_tag, text = 'target x,y={}'.format((self.cur_x, self.cur_y)))
        self.create_text(self.width // 2, 20, tag = self.stats_tag, text = 'calc x,y={}'.format(self.carriage.get_position()), justify = TK.LEFT)
    
    def move_to(self, x, y):
        self.cur_x, self.cur_y = x, y
        self.update()
    
    def tick(self):
        #print('--> tick()')
        self.cur_x += 1
        self.cur_y += 1
        #self.line(self.cur_x, self.cur_y, self.cur_x, self.cur_y + 10)
        self.update()
        self.after(self.interval_ms, self.tick)
        #print('<-- tick()')

class PolarBot:
    def __init__(self):
        self._executor = []
        # 
        self.position = Point(0.0, 0.0)
        self.curent_cmd = None

    def add_executor(self, ex):
        self._executor.append(ex)
        
    def rem_executor(self, ex):
        if ex in self._executor:
            del(self._executor[self._executor.index(ex)])
            
    def load_program(self, data):
        pass
        
    def execute(self):
        pass
        

class ControlPanel(TK.Frame):
    def __init__(self, parent, bot):
        super().__init__(parent) #, width = self.canvas_width, height = self.canvas_height)
        self.parent = parent
        self.bot = bot
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
        self.ed_y.bind('<Key>', self.on_key_enter)
        self.ed_x.bind('<Key>', self.on_key_enter)

    def on_key_enter(self, event):
        #print(event)
        if event.keycode == 13:
            self.bot.move_to(int(self.ed_x.get()), int(self.ed_y.get()))
        
if __name__ == '__main__':
    root = TK.Tk()
    bot = Visualiser(root, WIDTH, HEIGHT)
    cp = ControlPanel(root, bot)
    bot.grid(row = 1, column = 1)
    cp.grid(row = 1, column = 2, sticky = TK.W + TK.E + TK.N + TK.S)
    root.mainloop()