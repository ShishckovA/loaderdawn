import traceback

def a():
    b()
def b():
    c()
def c():
    1 / 0
try:
    a()
except BaseException as e:
    log(type(traceback.format_exc()))