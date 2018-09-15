# -*- coding: utf-8 -*-

import yadisk
from log import log
import datetime

api_v = 5.84
def clear_disks(stime=0):
    with open("../tokens") as f:
        token_list = f.read().split()

    for t in token_list:
        disk = yadisk.YaDisk(token=t)
        info = disk.get_disk_info()
        log("Opening disk %s with token %s" % (info["user"]["login"], t))
        lstdr = list(disk.listdir("/"))
        for fold in lstdr:
            if fold["type"] == "dir" and fold["name"].startswith("!!!"):
                if int(fold["created"].timestamp()) > stime:
                    disk.remove(fold["path"]) 
                    print("Removed %s" % fold["path"])
        disk.remove_trash("/")
        print("Trash cleared!")
if __name__ == "__main__":
    clear_disks()