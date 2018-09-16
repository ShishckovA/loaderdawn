# -*- coding: utf-8 -*-

import yadisk
from .log import log

def get_disks():
    log("Getting new disk list...")
    with open("tokens") as f:
        token_list = f.read().split()

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
                        "disk"     : c_disk, 
                        "token"    : t, 
                        "username" : info["user"]["login"]
                        })
        except BaseException as e:
            log(e)  
    log("Got %d disks" % len(ya_disks))
    return ya_disks
