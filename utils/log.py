# -*- coding: utf-8 -*-

import time

def log(*args):
    logfile = open(r"./logs/log.txt", "a")
    print(time.ctime(), end = " ")
    print(time.ctime(), file = logfile, end = " ")
    for t in args:
        print(str(t), end = " ")
        print(str(t), file = logfile, end = " ")
    print()
    print(file = logfile)
    logfile.close()
