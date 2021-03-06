# -*- coding: utf-8 -*-

import os
import wget
import time
import random
import requests
import traceback
from .log import log
from .strings import rand_st, cut
from .multiprocess import rethread


def download_by_parts(audios, aps, ya_disks):
    for i in range(0, len(audios), aps):
        audios_part = audios[i : min(i + aps, len(audios))]
        rethreads = []
        for i in range(len(audios_part)):
            reth = rethread(target=get_yadisk_url_2, args=(audios_part[i], ya_disks), name=audios_part[i].title)
            reth.start()
            rethreads.append(reth)
        while 1:
            for i in range(len(audios_part)):
                if rethreads[i].alive():
                    break
                else:
                    audios_part[i].url = rethreads[i].result()
            else:
                break
        yield audios_part
    

def get_yadisk_url(audio, ya_disks):
    c_disk = random.choice(ya_disks)
    print(audio.vkurl)
    ytoken = c_disk["token"]
    disk = c_disk["disk"]
    headers = {
        "Content-Type" : "application/json",
        "Authorization" : c_disk["token"]
    }
    max_try = -1
    log("Choosen disk %s, token %s" % (c_disk["username"], ytoken))
    log("Working with", audio)

    fold = "!!!" + rand_st(15)

    name = ("%s - %s.mp3" % (audio.artist, audio.title)).replace("/", "|")
    name = cut(name, 255)
    path = "disk:/%s/%s" % (fold, name)
    log("path", path)

    mkd = disk.mkdir(fold)["href"]
    log("mkdir req href:", mkd)

    trys = 0
    while trys != max_try:
        trys += 1
        log("Starting uploading...")
        upl = disk.upload_url(audio.vkurl, path)["href"]
        log("upload req href:", upl)

        st = disk.get_operation_status(upl)
        while st == "in-progress":
            log("Got status", st)
            st = disk.get_operation_status(upl)
        log("Got status", st)
        try:
            if st == "success":
                break
        except BaseException as e:
            log(e)
        log("!!Uploading error. Trying again. trys =", trys)
    else:
        log("Max try exceeded")
        raise BaseException("!!!!MAx try!")

    log("Uploaded!")

    while 1:
        try:
            log("Getting link") 
            data = disk.publish(path)
            
            log(data)    
            pbl = data["href"]
            log("Publish req href", pbl)
            r = requests.get(data["href"], headers=headers, timeout=2)
            jsn = r.json()
            if "public_url" in jsn:
                break 
            time.sleep(0.5)
        except BaseException:
            log(traceback.format_exc())
         


    ydisk_url = jsn["public_url"]
    log("Got link", ydisk_url)

    return ydisk_url


def get_yadisk_url_2(audio, ya_disks):
    c_disk = random.choice(ya_disks)
    ytoken = c_disk["token"]
    disk = c_disk["disk"]
    headers = {
        "Content-Type" : "application/json",
        "Authorization" : c_disk["token"]
    }
    max_try = -1
    log("Choosen disk %s, token %s" % (c_disk["username"], ytoken))
    log("Working with", audio)

    fold = "!!!" + rand_st(15)
    name = ("%s - %s.mp3" % (audio.artist, audio.title)).replace("/", "|")
    name = cut(name, 128)
    path = "disk:/%s/%s" % (fold, name)
    log("path", path)


    mkd = disk.mkdir(fold)["href"]
    log("mkdir req href:", mkd)

    os.mkdir(fold)  
    os.system("wget -q -O \"./%s/%s\" %s" % (fold, name, audio.vkurl))
    log("Downloaded!")

    disk.upload("./%s/%s" % (fold, name), path)

    log("Uploaded!")

    while 1:
        try:
            log("Getting link") 
            data = disk.publish(path)
            
            log(data)    
            pbl = data["href"]
            log("Publish req href", pbl)
            r = requests.get(data["href"], headers=headers, timeout=2)
            jsn = r.json()
            if "public_url" in jsn:
                break 
            time.sleep(0.5)
        except BaseException:
            log(traceback.format_exc())
         

    os.remove("./%s/%s" % (fold, name));
    os.rmdir("./%s" % fold);

    ydisk_url = jsn["public_url"]
    log("Got link", ydisk_url)

    return ydisk_url