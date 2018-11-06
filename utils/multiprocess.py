# -*- coding: utf-8 -*-

import threading

class rethread(threading.Thread):
    '''A thread that returns a result with a get_result() function'''
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        threading.Thread.__init__(self, group, target, name, args, kwargs)
        self.ended = False
        self._return = None
    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)
            self.ended = True
    def get_result(self):
        return self._return
