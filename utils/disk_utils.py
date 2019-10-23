# -*- coding: utf-8 -*-

import yadisk
import datetime
from .settings_reader import read_settings
import time
from .log import log

def clear_disks(stime=0):
    token_list = read_settings()["yadisk_tokens"]

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
        time.sleep(1)
        disk.remove_trash("/")
        print("Trash cleared!")

def check_disks(token_list):
    log("Getting new disk list...")
    ya_disks = []
    for t in token_list:
        log("Checking token", t)
        c_disk = yadisk.YaDisk(token=t)
        try:
            if c_disk.check_token():
                info = c_disk.get_disk_info()
                log("Username -", info["user"]["login"])
                if info["total_space"] - info["used_space"] > 30 * 2 ** 20: # 30 mb
                    ya_disks.append({
                        "disk"      : c_disk, 
                        "token"     : t, 
                        "username"  : info["user"]["login"],
                        "freeSpace" : info["total_space"] - info["used_space"] 
                        })
        except BaseException as e:
            log(e)  
    log("Got %d disks" % len(ya_disks))
    return ya_disks
