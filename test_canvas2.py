#!/usr/bin/env python3
# -*- coding: utf-8 -*-

WIDTH = 800
HEIGHT = 600

import tkinter as TK
from tkinter.messagebox import showinfo, showerror, showwarning
from math import sqrt, pi, cos, acos
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
    def __init__(self, id, spr, microsteps, on_step_func):
        # stepper 
        self._steps_per_revolution = spr
        self._microsteps = microsteps
        self._effective_steps = spr * microsteps
        self._rads_per_step = (2 * pi) / self._effective_steps
        # callback
        self._id = id
        self._on_step = on_step_func
        # internal
        self._steps_to_move = 0
        self._dir_to_move = 0
    
    def get_steps(self):
        return self._steps_to_move
    
    def set_rotation(self, angle):
        # calc steps
        self._steps_to_move = round(abs(angle) / self._rads_per_step)
        # calc direction
        if angle > 0:
            self._dir_to_move = 1
        elif angle < 0:
            self._dir_to_move = -1
        else:
            self._dir_to_move = 0
            self._steps_to_move = 0
        #print('set rotation id={}, s={}, d={}'.format(self._id, self._steps_to_move, self._dir_to_move))
        return self._steps_to_move
    
    def step(self):
        if self._steps_to_move == 0:
            #print('id={} no steps to move'.format(self._id))
            pass
        else:
            # make one step in direction (-1 or +1)
            self._steps_to_move -= 1
            if self._on_step:
                self._on_step(self._id, self._rads_per_step * self._dir_to_move)
            #print('id={}, s2m={}'.format(self._id, self._steps_to_move))
        
        return self._steps_to_move
        
class PolarBot:
    DEFAULT_SPEED = 100
    STEPS_PER_REV = 200
    MICROSTEP = 16
    PULLEY_DIA_MM = 10
    MAX_SEG_LEN_MM = 5
    
    def __init__(self, controler, **kwargs):
        self._executor = []
        #self._controler = controler
        self.area_width = kwargs.get('width', 800)
        self.area_height = kwargs.get('height', 600) 
        #
        self.mount_point = Point(self.area_width / 2, 100)
        #
        self.armA_len = self.area_width / 4
        self.armB_len = self.armA_len
        self.sqr_arm_len = self.armA_len ** 2 
        # max tool distance
        self.sqr_max_tool_dist = (self.armA_len + self.armB_len) ** 2
        # angle in radians between arm A and x axis
        self.armA_angle = pi / 2
        self.tg_armA_angle = None
        # angle in radians between arm B and arm A
        self.armB_angle = 2 * pi - pi / 2
        self.tg_armB_angle = None
        
        # position of robot's tool (pen)
        self.tool_position = Point(self.mount_point.x - self.armA_len, self.mount_point.y + self.armA_len)
        # calculated tool pos
        self.calc_tool_position = self.tool_position.copy()
        # target tool position
        self.tg_tool_position = self.tool_position.copy()
        # source tool position
        self.sc_tool_position = self.tool_position.copy()
        #
        self.curent_cmd = None
        #
        self.tick_int = controler.get_tick_interval()
        # create stepper pulleys and initialize events
        self.pulleyA = StepperPulley('A', PolarBot.STEPS_PER_REV, PolarBot.MICROSTEP, self.on_a_step)
        self.pulleyB = StepperPulley('B', PolarBot.STEPS_PER_REV, PolarBot.MICROSTEP, self.on_b_step)
        # register actions
        controler.register_action('tick', self.on_tick)
        controler.register_action('move_to', self.on_move_to)
        controler.register_action('run_cmd', self.on_run_cmd)
        controler.register_action('clear', self.on_clear)

    def update(self):
        # update executioners
        self._execute('update', (self.armA_angle, self.armB_angle))
        
    def add_executor(self, ex):
        try:
            ex.init(self.area_width, self.area_height, self.mount_point, self.armA_len)
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
    
    def calc_target_angles(self):
        #print('tp={}'.format(self.tool_position))
        # calc distance between tool position and mount point
        dx = self.tool_position.x - self.mount_point.x
        dy = self.tool_position.y - self.mount_point.y
        sqr_tool_dist = dx ** 2 + dy ** 2
        self.tool_dist = sqrt(sqr_tool_dist)
        #print('dx,dy = {}'.format((dx, dy)))
        #print('tool dist = {}'.format(self.tool_dist))
        # calc armB_angle
        cos_beta = (self.sqr_arm_len + self.sqr_arm_len - sqr_tool_dist) / (2 * self.sqr_arm_len)
        #print('cos beta = {}'.format(cos_beta))
        beta = acos(cos_beta)
        self.tg_armB_angle = 2 * pi - beta
        # calc armA_angle
        # calc other two angles in isosceles triangle
        base_angle = (pi - beta) / 2
        # calc straight angle of tool path line
        alpha = acos(abs(self.tool_position.x - self.mount_point.x) / self.tool_dist)
        if self.tool_position.x <= self.mount_point.x:
            self.tg_armA_angle = pi - (alpha + base_angle)
        else:
            self.tg_armA_angle = alpha - base_angle
            
    def actuate_pos(self):
        self.calc_target_angles()
        # deltas
        da = self.tg_armA_angle - self.armA_angle
        db = self.tg_armB_angle - self.armB_angle
        #print('tgab={}, ab={}'.format((round(self.tg_armA_angle, 5), round(self.tg_armB_angle, 5)),(round(self.armA_angle, 5), round(self.armB_angle, 5))))
        #
        stepsA = self.pulleyA.set_rotation(da)
        stepsB = self.pulleyB.set_rotation(db)
        # set master and slave pulleys
        self.master_pulley = self.pulleyA if stepsA >= stepsB else self.pulleyB
        self.slave_pulley = self.pulleyA if stepsA < stepsB else self.pulleyB
        # error
        self.error = self.master_pulley.get_steps() / 2
        #print('act pos cmd={}'.format(self.curent_cmd))
        
    def check_bounds(self, x, y):
        return ((x - self.mount_point.x) ** 2 + (y - self.mount_point.y) ** 2 <= self.sqr_max_tool_dist)
    
    def move_to(self, x, y):
        if not self.check_bounds(x, y):
            print('move fail: out of bounds')
        self.tool_position.x = x
        self.tool_position.y = y
        self.calc_target_angles()
        self.armA_angle, self.armB_angle = self.tg_armA_angle, self.tg_armB_angle
        self.update()
        
    def run_cmd(self, cmd):
        self.curent_cmd = cmd
        #print('run_cmd={}'.format(self.curent_cmd.p.xy))
        if not self.check_bounds(*self.curent_cmd.p.xy):
            print('cmd fail: out of bounds')
            cb = self.curent_cmd.callback
            del(self.curent_cmd)
            self.curent_cmd = None
            if cb:
                cb(False)
            return
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
        #print('sg={}, dx,dy={}'.format(self.seg_count, (self.dx, self.dy)))
        # set tool of executors
        self._execute('set_tool', (cmd.tool_state(),))
        # run first segment
        self.tool_position.x += self.dx
        self.tool_position.y += self.dy
        self.actuate_pos()
        
    # EVENTS
    def on_a_step(self, id, angle):
        self.armA_angle += angle
        #self.update()
        
    def on_b_step(self, id, angle):
        self.armB_angle += angle
        #self.update()
        
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
                #print('ss={}'.format(rem_slave_steps))
            #print('ms={}'.format(rem_master_steps))
            self.update()
            if rem_master_steps == 0:
                self.seg_count -= 1
                #print('seg left={}'.format(self.seg_count))
                if self.seg_count > 0:
                    self.tool_position.x += self.dx
                    self.tool_position.y += self.dy
                    self.actuate_pos()
                else:
                    # all done
                    #print('on_tick@done')
                    cb = self.curent_cmd.callback
                    del(self.curent_cmd)
                    self.curent_cmd = None
                    if cb:
                        cb(True)
            
    def on_move_to(self, x, y, callback):
        #print('move_to({},{})'.format(x, y))
        self.run_cmd(Command(cmd = 'G1', x = x, y = y, callback = callback))
        #self.move_to(x, y)
    
    def on_run_cmd(self, text, callback):
        #print('run_cmd({})'.format(text))
        self.run_cmd(Command(cmd_text = text, callback = callback))
    
    def on_clear(self):
        self._execute('clear', ())
        self._execute('update', (self.left_rope_len, self.right_rope_len, True))
    
class Visualiser(TK.Canvas):
    GRID_STEP = 100
    def __init__(self, parent, width, height):
        self.tag = 'draws'
        self.stats_tag = 'stats'
        self.path_tag = 'tool_path'
        self.grid_tag = 'grid'
        
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

    def init(self, width, height, mount_point, arm_len):
        # called by controler when object of this class added to controler's executioners list
        self.bot_width = width
        self.bot_height = height
        self.bot_mount_point = mount_point
        # distance
        self.bot_armA_len = arm_len
        self.bot_armB_len = arm_len
        # scale
        self.x_scale = self.width / self.bot_width
        self.y_scale = self.height / self.bot_height
        #print(self.scale_x , self.scale_y)
        # draw grid
        x = 0
        while x < self.width:
            y = 0
            while y < self.height:
                self.cross(x, y, 15, fill='gray', tag = self.grid_tag)
                y += Visualiser.GRID_STEP
            x += Visualiser.GRID_STEP

    
    def line(self, x0, y0, x1, y1, **kwargs):
        #print('({},{})-({},{})'.format(x0, y0, x1, y1))
        kwargs['tag'] = self.tag 
        self.create_line(x0, y0, x1, y1, kwargs)
    
    def rect(self, x0, y0, x1, y1, **kwargs):
        kwargs['tag'] = self.tag 
        self.create_rectangle(x0, y0, x1, y1, kwargs)
    
    def cross(self, x, y, size = 10, **kwargs):
        if not 'tag' in kwargs:
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
    
    def update(self, angleA, angleB, force_redraw = False):
        #print('update')
        signa = 1 if angleA >= 0 else -1
        # calc point of junction armA and armB
        dx1 = self.bot_armA_len * cos(angleA)
        dy1 = sqrt(self.bot_armA_len ** 2 - dx1 ** 2) * signa
        x1 = self.bot_mount_point.x + dx1 
        y1 = self.bot_mount_point.y + dy1
        # calc tool position
        if angleA >=0:
            beta = pi - (2 * pi - angleB) - (pi - abs(angleA) - pi / 2)
        else:
            beta = pi - (2 * pi - angleB) - abs(angleA) - pi / 2
        signbeta = 1 if beta >= 0 else -1
        #print('beta={}'.format(beta))
        dy2 = self.bot_armB_len * cos(beta)
        dx2 = sqrt(self.bot_armB_len ** 2 - dy2 ** 2)
        f_tx = x1 - (dx2 * signbeta)
        f_ty = y1 + dy2
        # tool coord in scale
        tool_x = self.scale_x(f_tx)
        tool_y = self.scale_y(f_ty)
        # update stats
        self.delete(self.stats_tag)
        self.text(self.width // 2, 10, 'tool x,y={}'.format((f_tx, f_ty)))
        self.text(self.width // 2, 20, 'x1,y1={}'.format((x1, y1)))
        self.text(self.width // 2, 30, 'a,b={}'.format((round(angleA, 5), round(angleB, 5))))
        
        if tool_x != self._last_tool_p.x or tool_y != self._last_tool_p.y or force_redraw:
            # redraw
            self.delete(self.tag)
            # aim
            #self.rect(tool_x - 1, tool_y - 1, tool_x + 1, tool_y + 1, outline = 'blue')
            self.cross(tool_x, tool_y, fill = 'blue')
            # armA
            self.line(self.scale_x(self.bot_mount_point.x), self.scale_x(self.bot_mount_point.y), self.scale_x(x1), self.scale_y(y1), fill = 'red')
            # armB
            self.line(self.scale_x(x1), self.scale_y(y1), tool_x, tool_y, fill = 'red')
        
            # draw tool path
            if self._enable_tool:
                self.create_line(self._last_tool_p.x, self._last_tool_p.y, tool_x, tool_y, fill = 'gray')#, tag = self.path_tag)
            self._last_tool_p.set(tool_x, tool_y) 
    
    def clear(self):
        #self.delete(self.path_tag)
        print('clear')
        self.delete(*self.find_all())
        
    def set_tool(self, state = True):
        self._enable_tool = state

class ControlPanel(TK.Frame):
    ACTIONS = ('TICK', 'MOVE_TO', 'RUN_CMD', 'CLEAR')
    TICK_INTERVAL = 10
    
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
        self.script_running = False
        self.cmd_running = False
        self.program_line = 0
        self.program_text_iter = None
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
            text = next(self.program_text_iter)
            if text:
                print('cmd #{} {}'.format(self.program_line, text))
                self.cmd_running = True
                self.raise_action('RUN_CMD', text, self.on_cmd_done)
        except StopIteration as e:
            self.program_line = 0
            self.script_running = False
            
    def tick(self):
        #print('--> tick()')
        if self.script_running and not self.cmd_running:
            self.next_cmd()
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
        self.program_text_iter = iter(self.txt_prog.get(1.0, TK.END).split('\n'))
        self.program_line = 0
        #self.next_cmd()
        self.script_running = True
        
    def btnClear_on_click(self, event):
        self.raise_action('CLEAR')
    
    def on_cmd_done(self, result):
        print('cmd done={}'.format(result))
        #self.next_cmd()
        self.cmd_running = False
    
    def on_move_done(self, result):
        print('move done={}'.format(result))
        
    
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