import random
from .log import log

def rand_st():
    l = 15
    allowed_symbols = "abcdefghijklmnopqrstuvwxyzABCDEFGHIGKLMNOPQRSTUVWXYZ1234567890_"
    st = ""
    for i in range(l):
        st += allowed_symbols[random.randint(0, len(allowed_symbols) - 1)]
    return st


def cut(string, ln):
    if string.count("."):
        ext = string[string.rfind("."):]
        body = string[:string.rfind(".")]
    else:
        body = string
        ext = ""
    ln_body = ln - len(ext)
    end = body[:ln_body] + ext
    return end
