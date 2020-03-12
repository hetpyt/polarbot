#!/usr/bin/env python3
# -*- coding: utf-8 -*-

WIDTH = 800
HEIGHT = 600

import tkinter as TK
from tkinter.messagebox import showinfo, showerror, showwarning
from math import sqrt

class Carriage:
    def __init__(self, canvas):
        self.color = 'blue'
        self.width = 80
        self.height = 60
        self.half_width = self.width // 2
        self.half_height = self.height // 2
        self.pen_x = canvas.width // 2
        self.pen_y = canvas.height // 2
        self.canvas = canvas
        self.tag = 'carriage'
        # bounds
        canvas.rect(self.pen_x - self.half_width, self.pen_y - self.half_height, self.pen_x + self.half_width, self.pen_y + self.half_height, outline = self.color, tag = self.tag)
        # aim
        canvas.rect(self.pen_x - 1, self.pen_y - 1, self.pen_x + 1, self.pen_y + 1, outline = self.color, tag = self.tag)
        
    def update(self):
        pass
    
    def move(self, dx, dy):
        self.pen_x += dx
        self.pen_y += dy
        self.canvas.move(self.tag, dx, dy)
    
    def move_to(self, x, y):
        self.move(x - self.pen_x, y - self.pen_y)
    
    def calc_position(self, left_len, right_len):
        print('llen={}, rlen={}'.format(left_len, right_len))
        
        f_lx = (left_len ** 2 - right_len ** 2 + (self.canvas.width - self.width) ** 2) / (2 * (self.canvas.width - self.width))
        ly = round(sqrt(left_len ** 2 - f_lx ** 2))
        # draw calcutated attpoints
        self.canvas.delete('calc_attpoint')
        self.canvas.cross(round(f_lx), ly, 10, tag = 'calc_attpoint', fill = 'green')
        #self.canvas.cross(round(f_rx), ry, 10, fill = 'yellow')
        
    def calc_attpoint(self, x, y, left):
        if left:
            return (x - self.half_width, y - self.half_height)
        else:
            return (x + self.half_width, y - self.half_height)
        
    def get_attpoint(self, left):
        return self.calc_attpoint(self.pen_x, self.pen_y, left)
        
    def get_position(self):
        return (self.pen_x, self.pen_y)

class Rope:
    def __init__(self, canvas, is_left):
        self.is_left = is_left
        self.tag = 'left_rope' if is_left else 'right_rope'
        self.canvas = canvas
        self.carriage = canvas.get_carriage()
        self.bound_x = 0 if is_left else canvas.width
        self.bound_y = 0 
        self.end_x, self.end_y = self.carriage.get_attpoint(is_left)
        self.redraw()

    def redraw(self):
        self.canvas.delete(self.tag)
        self.canvas.line(self.bound_x, self.bound_y, self.end_x, self.end_y, tag = self.tag, fill = 'red')
    
    def move(self, dx, dy):
        self.end_x += dx
        self.end_y += dy
        self.redraw()
        
    def move_to(self):
        #self.move(x - self.end_x, y - self.end_y)
        self.end_x, self.end_y = self.carriage.get_attpoint(self.is_left)
        self.redraw()
        
    def calc_length(self, dest_x, dest_y):
        px, py = self.carriage.calc_attpoint(dest_x, dest_y, self.is_left)
        if not self.is_left:
            px = self.bound_x - px
        self.length = round(sqrt( px ** 2 + py ** 2))  
        return self.length
    
    def set_length(self, len):
        pass
        
    def get_length(self):
        pass

class PolarBot(TK.Canvas):
    def __init__(self, parent, width, height):
        self.stats_tag = 'stats'
        self.interval_ms = 1000
        self.cur_x = 0
        self.cur_y = 0
        super().__init__(parent) #, width = self.canvas_width, height = self.canvas_height)
        self.parent = parent
        self.width = width
        self.height = height
        self.configure(width = self.width, height = self.height, background = "white", borderwidth = 0)
        self.pack() #ipadx = 10, ipady = 10)
        #self.place(x = 10, y = 10)
        #self.create_rectangle(2, 2, self.width, self.width, outline = "black", fill = "white")
        #self.line(0, 0, 10, 0, fill = "black", tag = 'test_line')    
        self.after(self.interval_ms, self.tick)
        # создаем объект каретки робота
        self.carriage = Carriage(self)
        self.left_rope = Rope(self, True)
        self.right_rope = Rope(self, False)
    
        self.cur_x, self.cur_y = self.carriage.get_position()
        
    def get_carriage(self):
        return self.carriage
    
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
        # update stats
        self.delete(self.stats_tag)
        self.create_text(self.width // 2, 10, tag = self.stats_tag, text = 'x,y={}'.format(self.carriage.get_position()))
    
    def move_to(self, x, y):
        self.cur_x = x
        self.cur_y = y
        self.carriage.calc_position(self.left_rope.calc_length(x, y), self.right_rope.calc_length(x, y))
        self.carriage.move_to(x, y)
        self.left_rope.move_to()
        self.right_rope.move_to()
        
    def tick(self):
        #print('--> tick()')
        self.cur_x += 1
        self.cur_y += 1
        #self.line(self.cur_x, self.cur_y, self.cur_x, self.cur_y + 10)
        self.move_to(self.cur_x, self.cur_y)
        self.update()
        self.after(self.interval_ms, self.tick)
        #print('<-- tick()')

class ControlPanel(TK.Frame):
    def __init__(self, parent, bot, width, height):
        super().__init__(parent) #, width = self.canvas_width, height = self.canvas_height)
        self.parent = parent
        self.bot = bot
        self.width = width
        self.height = height
        self.configure(width = self.width, height = self.height)
        self.pack() #ipadx = 10, ipady = 10)
        # create controls
        self.lb_x = TK.Label(self, text = 'GO X')
        self.lb_x.grid(row = 1, column = 1)
        self.ed_x = TK.Entry(self, width = 5)
        self.ed_x.grid(row = 1, column = 2)
        self.lb_y = TK.Label(self, text = 'Y')
        self.lb_y.grid(row = 1, column = 3)
        self.ed_y = TK.Entry(self, width = 5)
        self.ed_y.grid(row = 1, column = 4)
        
        self.ed_y.bind('<Key>', self.on_key_enter)
        self.ed_x.bind('<Key>', self.on_key_enter)

    def on_key_enter(self, event):
        print(event)
        if event.keycode == 13:
            self.bot.move_to(int(self.ed_x.get()), int(self.ed_y.get()))
        
if __name__ == '__main__':
    root = TK.Tk()
    bot = PolarBot(root, WIDTH, HEIGHT)
    cp = ControlPanel(root, bot, WIDTH, 50)
    root.mainloop()