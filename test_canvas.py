#!/usr/bin/env python3
# -*- coding: utf-8 -*-

WIDTH = 800
HEIGHT = 600

import tkinter as TK
from tkinter.messagebox import showinfo, showerror, showwarning
from math import sqrt, pi
from time import sleep

class Point:
    def __init__(self, x, y):
        self.set(x, y)
    
    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        elif name.upper() == 'X':
            return self.__dict__['_x']
        elif name.upper() == 'Y':
            return self.__dict__['_y']
        elif name.upper() == 'XY':
            return (self.__dict__['_x'], self.__dict__['_y'])
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
 
    def copy(self):
        return Point(self.x, self.y)
        
class Command:
    CMD_SEP = ' ' 
    SUPPORTED_CMD = ('G0, G1')
    def __init__(self, **kwargs):
        self._cmd_text = kwargs.get('cmd_text', None)
        self._cmd = kwargs.get('cmd', None)
        self._arg_x = kwargs.get('x', None)
        self._arg_y = kwargs.get('y', None)
        self._arg_speed = kwargs.get('f', None)
        self._callback = kwargs.get('callback', None)
    
        if not self._cmd_text == None:
            self.parse()
            
    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        elif name.upper() == 'CMD':
            return self.__dict__['_cmd']
        elif name.upper() == 'X':
            return self.__dict__['_arg_x']
        elif name.upper() == 'Y':
            return self.__dict__['_arg_y']
        elif name.upper() == 'P':
            #print(self.__dict__)
            return Point(self.__dict__['_arg_x'], self.__dict__['_arg_y'])
        elif name.upper() == 'CALLBACK':
            return self.__dict__['_callback']
        elif name.upper() == 'F':
            return self.__dict__['_arg_speed']
        else:
            raise AttributeError('property "{}" not defined'.format(name))
        
    def check(self):
        return True
    
    def tool_state(self):
        return (True if self._cmd == 'G1' else False)
        
    def parse(self):
        # <CMD> [X<val>] [Y<val>] [F<val>]
        cmd_text = self._cmd_text
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

class StepperPulley:
    def __init__(self, spr, microsteps, pulley_dia):
        # stepper 
        self._steps_per_revolution = spr
        self._microsteps = microsteps
        self._pulley_diameter = pulley_dia
        self._effective_steps = spr * microsteps
        self._degrees_per_step = 360 / self._effective_steps
        self._mm_per_step = (pulley_dia * pi) / self._effective_steps
        # callback
        self._id = None
        self._on_step = None
        # internal
        self._steps_to_move = 0
        self._dir_to_move = None
        # ## statistics
        # current position of pulley in degrees
        self._position_dg = 0.0
        # traveled distance in mm
        self._distance_mm = 0.0
    
    def get_steps(self):
        return self._steps_to_move
    
    def set_driven(self, id, on_step_func):
        self._id = id
        self._on_step = on_step_func
    
    def set_distance(self, dist_mm):
        # calc steps
        self._steps_to_move = round(abs(dist_mm) / self._mm_per_step)
        # calc direction
        if dist_mm > 0:
            self._dir_to_move = 1
        elif dist_mm < 0:
            self._dir_to_move = -1
        else:
            self._dir_to_move = None
            self._steps_to_move = 0

        return self._steps_to_move
    
    def step(self):
        if self._steps_to_move == 0:
            print('id={} no steps to move'.format(self._id))
            return 0
        # make one step in direction (-1 or +1)
        if self._on_step:
            self._on_step(self._id, self._mm_per_step * self._dir_to_move)
        #
        self._steps_to_move -= 1
        #print('id={}, s2m={}'.format(self._id, self._steps_to_move))
        # stats
        self._position_dg += self._degrees_per_step * self._dir_to_move
        self._distance_mm += self._mm_per_step
        
        return self._steps_to_move
        
class PolarBot:
    DEFAULT_SPEED = 100
    STEPS_PER_REV = 200
    MICROSTEP = 1
    PULLEY_DIA_MM = 10
    MAX_SEG_LEN_MM = 10
    
    def __init__(self, controler, **kwargs):
        self._executor = []
        #self._controler = controler
        self.area_width = kwargs.get('width', 800)
        self.area_height = kwargs.get('height', 600) 
        # position of robot's tool (pen)
        self.tool_position = Point(self.area_width / 2, self.area_height / 2)
        # calculated tool pos
        self.calc_tool_position = Point(self.area_width / 2, self.area_height / 2)
        # target tool position
        self.tg_tool_position = self.tool_position.copy()
        # source tool position
        self.sc_tool_position = self.tool_position.copy()
        # distance between left attachment point of robot's carriage and tool position on x axis
        self.left_offset_x = kwargs.get('left_offset', self.area_width / 20)
        # distance between right attachment point of robot's carriage and tool position on x axis
        self.right_offset_x = kwargs.get('right_offset', self.area_width / 20)
        # distance between left and right attachment points
        self.att_distance = self.left_offset_x + self.right_offset_x
        # precalculations
        self.f_w = self.area_width - self.att_distance
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
        #
        self.tick_int = controler.get_tick_interval()
        # create stepper pulleys and initialize events
        self.left_pulley = StepperPulley(PolarBot.STEPS_PER_REV, PolarBot.MICROSTEP, PolarBot.PULLEY_DIA_MM)
        self.left_pulley.set_driven('left', self.on_left_step)
        self.right_pulley = StepperPulley(PolarBot.STEPS_PER_REV, PolarBot.MICROSTEP, PolarBot.PULLEY_DIA_MM)
        self.right_pulley.set_driven('right', self.on_right_step)
        # register actions
        controler.register_action('tick', self.on_tick)
        controler.register_action('move_to', self.on_move_to)
        controler.register_action('run_cmd', self.on_run_cmd)
        controler.register_action('clear', self.on_clear)

    def calc_ropes(self, tp):
        # calc length of left rope
        f_llen = sqrt(((tp.x - self.left_offset_x) - self.left_bound_x) ** 2 + (tp.y - self.offset_y) ** 2)
        #self.left_rope_len = f_llen
        # calc length of right rope
        f_rlen = sqrt((self.right_bound_x - (tp.x + self.right_offset_x)) ** 2 + (tp.y - self.offset_y) ** 2)
        #self.right_rope_len = f_rlen
        return (f_llen, f_rlen)
        
    def update(self):
        # update executioners
        self._execute('update', (self.left_rope_len, self.right_rope_len))
        
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
    
    def _execute(self, action, args):
        for ex in self._executor:
            try:
                getattr(ex, action)(*args)
            except Exception as e:
                print(e)
    
    def actuate_pos(self):
        # calc ropes lengths to reach targer tool pos
        self.tg_left_rope_len, self.tg_right_rope_len = self.calc_ropes(self.tool_position)
        # calc deltas between new lengths and current
        ldelta = self.tg_left_rope_len - self.left_rope_len
        rdelta = self.tg_right_rope_len - self.right_rope_len
        # calc steps and set direction
        lsteps = self.left_pulley.set_distance(-ldelta) # inverted rotation
        rsteps = self.right_pulley.set_distance(rdelta)
        # set master and slave pulleys
        self.master_pulley = self.left_pulley if lsteps >= rsteps else self.right_pulley
        self.slave_pulley = self.left_pulley if lsteps < rsteps else self.right_pulley
        # error
        self.error = self.master_pulley.get_steps() / 2
        print('act pos cmd={}'.format(self.curent_cmd))
        
    def run_cmd(self, cmd):
        self.curent_cmd = cmd
        print('run_cmd={}'.format(self.curent_cmd.p.xy))
        self.sc_tool_position.set(*self.tool_position.xy)
        self.tg_tool_position.set(*cmd.p.xy)
        dx = self.tg_tool_position.x - self.tool_position.x
        dy = self.tg_tool_position.y - self.tool_position.y
        # total distance to move
        move_dist = sqrt(dx ** 2 + dy ** 2)
        # number of segmets
        self.seg_count = 1
        max_d = max(abs(dx), abs(dy))
        while max_d / self.seg_count > PolarBot.MAX_SEG_LEN_MM:
            self.seg_count += 1
        self.dx = dx / self.seg_count
        self.dy = dy / self.seg_count
        # set tool of executors
        self._execute('set_tool', (cmd.tool_state(),))
        # run first segment
        self.tool_position.x += self.dx
        self.tool_position.y += self.dy
        self.actuate_pos()
        
    # EVENTS
    def on_left_step(self, id, len):
        self.left_rope_len += -len
        self.update()
        
    def on_right_step(self, id, len):
        self.right_rope_len += len
        self.update()
        
    def on_tick(self):
        #print(self.curent_cmd)
        if self.curent_cmd:
            # step master pulley
            #print('tick')
            rem_master_steps = self.master_pulley.step()
            self.error -= self.slave_pulley.get_steps()
            if self.error < 0:
                rem_slave_steps = self.slave_pulley.step()
                self.error += self.master_pulley.get_steps()
                print('ss={}'.format(rem_slave_steps))
            print('ms={}'.format(rem_master_steps))
            if rem_master_steps == 0:
                self.seg_count -= 1
                if self.seg_count > 0:
                    self.tool_position.x += self.dx
                    self.tool_position.y += self.dy
                    self.actuate_pos()
                else:
                    # all done
                    print('on_tick@done')
                    cb = self.curent_cmd.callback
                    del(self.curent_cmd)
                    self.curent_cmd = None
                    if cb:
                        cb(True)
            
    def on_move_to(self, x, y, callback):
        print('move_to({},{})'.format(x, y))
        self.run_cmd(Command(cmd = 'G1', x = x, y = y, callback = callback))
    
    def on_run_cmd(self, text, callback):
        print('run_cmd({})'.format(text))
        self.run_cmd(Command(cmd_text = text, callback = callback))
    
    def on_clear(self):
        self._execute('clear', ())
    
class Visualiser(TK.Canvas):
    def __init__(self, parent, width, height):
        self.tag = 'draws'
        self.stats_tag = 'stats'
        self.path_tag = 'tool_path'
        
        super().__init__(parent) #, width = self.canvas_width, height = self.canvas_height)
        self.parent = parent
        self.width = width
        self.height = height
        self.bot_width = width
        self.bot_height = height
        self.x_scale = 1.0
        self.y_scale = 1.0
        
        self._last_tool_p = Point(0.0, 0.0)
        self._enable_tool = False
        
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
        kwargs['tag'] = self.tag 
        self.create_line(x0, y0, x1, y1, kwargs)
    
    def rect(self, x0, y0, x1, y1, **kwargs):
        kwargs['tag'] = self.tag 
        self.create_rectangle(x0, y0, x1, y1, kwargs)
    
    def cross(self, x, y, size = 10, **kwargs):
        kwargs['tag'] = self.tag 
        # hor line
        self.create_line(x - size // 2, y, x + size // 2, y, kwargs)
        # vert line
        self.create_line(x, y - size // 2, x, y + size // 2, kwargs)
    
    def text(self, x, y, text, **kwargs):
        kwargs['tag'] = self.stats_tag 
        kwargs['text'] = text 
        self.create_text(x, y, kwargs)
        
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
        # tool coord in scale
        tool_x = self.scale_x(f_tx)
        tool_y = self.scale_y(f_ty)
        # update stats
        self.delete(self.stats_tag)
        self.text(self.width // 2, 10, 'tool x,y={}'.format((f_tx, f_ty)))
        self.text(self.width // 2, 20, 'left l={} x,y={}'.format(left_len, (f_lx, f_y)))
        self.text(self.width // 2, 30, 'right l={} x,y={}'.format(right_len, (f_rx, f_y)))
        
        if tool_x == self._last_tool_p.x and tool_y == self._last_tool_p.y:
            # no need to redraw
            return
        # redraw
        self.delete(self.tag)
        # aim
        #self.rect(tool_x - 1, tool_y - 1, tool_x + 1, tool_y + 1, outline = 'blue')
        self.cross(tool_x, tool_y, fill = 'blue')
        # left rope
        self.line(0, 0, self.scale_x(f_lx), self.scale_y(f_y), fill = 'red')
        # right rope
        self.line(round(self.width), 0, self.scale_x(f_rx), self.scale_y(f_y), fill = 'red')
        # left attach point
        self.cross(self.scale_x(f_lx), self.scale_y(f_y), fill = 'green')
        # right attach point
        self.cross(self.scale_x(f_rx), self.scale_y(f_y), fill = 'green')
    
        # draw tool path
        if self._enable_tool:
            self.create_line(self._last_tool_p.x, self._last_tool_p.y, tool_x, tool_y, fill = 'gray')#, tag = self.path_tag)
        self._last_tool_p.set(tool_x, tool_y) 
    
    def clear(self):
        self.delete(self.path_tag)
        
    def set_tool(self, state = True):
        self._enable_tool = state

class ControlPanel(TK.Frame):
    ACTIONS = ('TICK', 'MOVE_TO', 'RUN_CMD', 'CLEAR')
    TICK_INTERVAL = 5
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent) #, width = self.canvas_width, height = self.canvas_height)
        self.parent = parent
        self._actions = {}
        self.tick_interval = kwargs.get('tick_interval', ControlPanel.TICK_INTERVAL)
        # self.width = width
        # self.height = height
        #self.configure(width = self.width, height = self.height)
        #self.pack() #ipadx = 10, ipady = 10) 
        #
        self.program_line = 0
        self.program_text = None
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
        # button - run
        self.btn_run = TK.Button(self, text = 'RUN')
        self.btn_run.grid(columnspan = 4, sticky = TK.W + TK.E + TK.N + TK.S)
        # button clear
        self.btn_clear = TK.Button(self, text = 'CLEAR')
        self.btn_clear.grid(columnspan = 4, sticky = TK.W + TK.E + TK.N + TK.S)
        # bindings
        self.ed_y.bind('<Key>', self.edXY_on_key_enter)
        self.ed_x.bind('<Key>', self.edXY_on_key_enter)
        self.btn_run.bind('<Button-1>', self.btnRun_on_click)
        self.btn_clear.bind('<Button-1>', self.btnClear_on_click)
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
                
    def get_tick_interval(self):
        return ControlPanel.TICK_INTERVAL
    
    def next_cmd(self):
        self.program_line += 1
        try:
            text = next(self.program_text)
            print('cmd #{} {}'.format(self.program_line, text))
            if text:
                self.raise_action('RUN_CMD', text, self.on_cmd_done)
        except StopIteration as e:
            self.program_line = 0
            
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
            self.raise_action('MOVE_TO', x, y, self.on_move_done)
            
    def btnRun_on_click(self, event):
        self.program_text = iter(self.txt_prog.get(1.0, TK.END).split('\n'))
        self.program_line = 0
        self.next_cmd()
        
    def btnClear_on_click(self, event):
        self.raise_action('CLEAR')
    
    def on_cmd_done(self, result):
        print('cmd done')
        self.next_cmd()
    
    def on_move_done(self, result):
        print('move done')
        
    
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
    pb = PolarBot(cp, width = 800, height = 600)
    # add visualiser as executor
    pb.add_executor(vis)
    # enter main loop
    root.mainloop()
    # while True:
        # root.update()
        # sleep(0.001)