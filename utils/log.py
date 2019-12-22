# -*- coding: utf-8 -*-

import threading
import time

def log(*args):
    logfile = open(r"./logs/log.txt", "a")
    ct = time.ctime().split()
    wt = ct[2] + "." + ct[1] + "." + ct[4] + ":" + ct[3]
    print(wt, ", in", sep="", end = " ")
    print(wt, ", in", file = logfile, sep="", end = " ")
    print(threading.currentThread().getName(), end = ": ")
    print(threading.currentThread().getName(), file = logfile, end = ": ")

    for t in args:
        print(str(t), end = " ")
        print(str(t), file = logfile, end = " ")
    print()
    print(file = logfile)
    logfile.close()
