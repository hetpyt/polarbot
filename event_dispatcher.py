#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class MetaEventDispatcher(type):
    def __getattr__(cls, name):
        return cls._root.__getattr__(name)
        
    def __setattr__(cls, name, value):
        if hasattr(cls, name):
            super().__setattr__(name, value)
        else:
            cls._root.__setattr__(name, value)

class EventHandler:
    def __init__(self):
        self._handlers = []
        
    def __iadd__(self, handler):
        print(f'add,{handler}')
        self._handlers.append(handler)
        return self
        
    def __isub__(self, handler):
        self._handlers.remove(handler)
        return self
        
    def __call__(self, *args, **keywargs):
        for handler in self._handlers:
            handler(*args, **keywargs)

class Event:
    def __init__(self, event_name, args, kwargs):
        self._name = event_name
        self._args = args
        self._kwargs = kwargs
        
    def __getattr__(self, name):
        inname = '_' + name
        if inname in self.__dict__:
            return self.__dict__[inname]
        else:
            raise AttributeError('Attribute "{}" not found'.format(name))
            
class EventDispatcher(metaclass = MetaEventDispatcher):
    _root = None
    
    def __new__(cls):
        if not cls._root:
            cls._root = super().__new__(cls)
        return cls._root
        
    def __init__(self):
        self.__dict__['_events'] = {}
        self.__dict__['_queue'] = []
        
    def __getattr__(self, name):
        print(f'getattr,{name}')
        if name not in self.__dict__['_events']:
            #self.__dict__['_events'][name] = EventHandler()
            self._events[name] = EventHandler()
        return self.__dict__['_events'][name]
            
    def __setattr__(self, name, value):
        print(f'setattr,{name},{value}')
        if name not in self.__dict__['_events']:
            self.__dict__['_events'][name] = EventHandler()
        super().__setattr__(name, value)
    
    @classmethod
    def add_event(cls, event_name):
        """ add new event """
        if event_name not in cls._root._events:
            cls._root._events[event_name] = EventHandler()
            
    @classmethod
    def rem_event(cls, event_name):
        """ remove event """
        if event_name in cls._root._events:
            del(cls._root._events[event_name])
            
    @classmethod
    def trigger_event(cls, event_name, *args, **kwargs):
        """ trigger an event - add event to queue """
        # check event name
        if event_name in cls._root._events:
            cls._root._queue.append(Event(event_name, args, kwargs))
        else:
            raise AttributeError('Event "{}" not found'.format(event_name))
            
    @classmethod
    def dispatch(cls):
        """ dispatch events """
        while len(cls._root._queue) > 0:
            event = cls._root._queue.pop(0)
            cls._root._events[event.name](*event.args, **event.kwargs)
            
EventDispatcher()

