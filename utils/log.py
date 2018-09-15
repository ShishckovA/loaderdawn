# -*- coding: utf-8 -*-
import time

def log(*args):
    logfile = open(r"log.txt", "a")
    print(time.ctime(), end = " ")
    print(time.ctime(), file = logfile, end = " ")
    for t in args:
        print(str(t), end = " ")
        print(str(t), file = logfile, end = " ")
    print()
    print(file = logfile)
    logfile.close()

if __name__ == "__main__":
    print("A simple logger. Usage:")
    print("log(\"My log\", 2 + 2)")
    print("This string will log current date and time, and then \"My log 4\" ")

