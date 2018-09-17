# -*- coding: utf-8 -*-

import re
import os
import sys
import time
import json
import wget
import random
import vk_api
import yadisk
import requests
import traceback
import threading
import linecache
from utils.log import log
from utils.VKAuth import *
from utils.disk_checker import check_disks
from utils.strings import rand_st, cut
from utils.settings_reader import read_settings
from vk_api.longpoll import VkLongPoll, VkEventType


api_v = 5.84

def get_message():
    global session_html
    req = session_html.get("https://vk.com/dev/messages.getHistory")
    
    hash_p = req.content.find(b"Dev.methodRun(")
    hash_st = req.content[hash_p+15 : hash_p+44]

    d = {
        "act": "a_run_method",
        "al" : "1",
        "hash" : hash_st,
        "method" : "messages.getHistory",
        "param_count": "1",
        "param_user_id": settings["vk_group_id"],
        "param_v": api_v
    }
    message = session_html.post("https://vk.com/dev", data=d).content
    decoded_message = message.decode("cp1251")
    pos_resp = decoded_message.find('{"response"')
    decoded_message = decoded_message[pos_resp:]
    result = json.loads(decoded_message)["response"]["items"][0]
    return result

def get_audios(message):
    audios = []
    if "attachments" in message:
        for t in message["attachments"]:
            if t["type"] == "audio":
                log("Audio link:", t["audio"])
                url = t["audio"]["url"]
                if not url:
                    continue
                headers = requests.head(url).headers
                audio = {
                         "title" : t["audio"]["title"],
                        "artist" : t["audio"]["artist"],
                         "vkurl" : url,
                         "url"   : url,
                         "size"  : int(headers["Content-Length"])
                            }
                log(audio["vkurl"])
                audios.append(audio)
                
    if "fwd_messages" in message:
        for fwd_mes in message["fwd_messages"]:
            audios += get_audios(fwd_mes)
    return audios

def download_and_send(audios, aps, user_id):
    for i in range(0, len(audios), aps):
        audios_part = audios[i : min(i + aps, len(audios))]
        for i in range(len(audios_part)):
            audios_part[i]["url"] = get_yadisk_url(audios_part[i])
            log()
        send_audios(audios_part, user_id)
        log("Part is done, message sent\n")
    

def get_yadisk_url(audio):
    c_disk = random.choice(ya_disks)
    ytoken = c_disk["token"]
    disk = c_disk["disk"]

    headers = {
        "Content-Type" : "application/json",
        "Authorization" : c_disk["token"]
    }
    max_try = 10

    log("Choosen disk %s, token %s" % (c_disk["username"], ytoken))
    log("Working with", audio)

    fold = "!!!" + rand_st()

    name = ("%s - %s.mp3" % (audio["artist"], audio["title"])).replace("/", "|")
    name = cut(name, 255)
    path = "disk:/%s/%s" % (fold, name)
    log("path", path)

    mkd = disk.mkdir(fold)["href"]
    log("mkdir req href:", mkd)

    trys = 0
    while trys < max_try:
        trys += 1
        log("Starting uploading...")
        upl = disk.upload_url(audio["vkurl"], path)["href"]
        log("upload req href:", upl)

        st = requests.get(upl, headers=headers).json()["status"]
        while st == "in-progress":
            st = disk.get_operation_status(upl)
        log("Got status", st)
        if requests.get(upl, headers=headers).json()["status"] == "success":
            break
        log("!!Uploading error. Trying again. trys =", trys)
    else:
        log("Max try exceeded")
        raise BaseException("!!!!MAx try!")

    log("Uploaded!")

    log("Getting link") 
    data = disk.publish(path)
    
    log(data)    
    pbl = data["href"]
    log("Publish req href", pbl)
    r = requests.get(data["href"], headers=headers)
    jsn = r.json()
    while not "public_url" in jsn:
        try: 
            log("Searching url...")
            r = requests.get(data["href"], headers=headers, timeout=2)
            jsn = r.json()
        except BaseException:
            pass

    ydisk_url = jsn["public_url"]
    log("Got link", ydisk_url)

    return ydisk_url


def send_audios(audios, user_id):
    text = ""
    for audio in audios:
        text += "%s - %s\n%s\n\n" % (audio["artist"], audio["title"], audio["url"])
    vk.messages.send(user_id=user_id, message=text)

def get_pl_url(message):
    if "attachments" in message:
        for attachment in message["attachments"]:
            if attachment["type"] == "link" and attachment["link"]["caption"] == "Плейлист":
               return attachment["link"]["url"]
    return False

def send_pl(url, user_id):
    pl_audio = []

    html_code = session_html.get(url).content.decode("utf-8")

    for t in [m.start() for m in re.finditer('id="audio', html_code)]:
        first = html_code.find("_", t)
        end = html_code.find("_", first + 1)
        pl_audio.append(tuple(map(int, html_code[t+9:end].split("_"))))
    
    n_mus = len(pl_audio)

    for i in range(0, n_mus, 10):
        at = ",".join(["audio%d_%d" % t for t in pl_audio[i:min(i + 10, n_mus)]])
        vk.messages.send(user_id=user_id, attachment=at)


def process(user_id, message_id, message):
    try:
        audios = get_audios(message)
        log("Found %d audios, starting sending\n\n" % len(audios))
        if audios:
            s = 0
            for elem in audios:
                s += elem["size"]
            log("All size:", s)
            start = time.time()
            log("Start time", start)
            vk.messages.send(user_id=user_id, message="=====================\nАудиозаписей найдено в вашем сообщении: %d, начинаю скачивать!\n=====================" % len(audios))
            download_and_send(audios, 5, user_id)

            log("End time", time.time())
            with open("./logs/times.txt", "a+") as f:
                f.write(str(time.time() - start) + " ") 
                f.write(str(s) + " ") 
                f.write(str(len(audios)) + " ") 
                f.write("\n")


        log("Audios succsedfully sent")

        log("Searching playlist url")
        pl_url = get_pl_url(message)

        if pl_url:
            log("Playlist url found: %s Starting sending playlist" % pl_url)
            send_pl(pl_url, user_id)
        else:
            log("No playlist url found")

        if not audios:
            log("No audios, no playlist. Zachem pisal? Neyasno. ")
            vk.messages.send(user_id=user_id, message="=====================\nПришли мне песню или плейлист, и я помогу тебе скачать твою любимую музыку!\n=====================")
        else:
            time.sleep(0.5)
            vk.messages.send(user_id=user_id, message="=====================\n" +  
                random.choice([
                    "Ура, ещё одно успешное скачивание!", 
                    "Всё получилось!",
                    "Я справился? Класс!",
                    "Порекомендуешь меня друзьям?",
                    ]) + 
                "\n=====================")
        log("Time -", time.time() - start)
        log("Answered!\n\n")

    except BaseException:
        vk.messages.send(user_id=user_id, message="=====================\nОй!\nЧто-то пошло не так. Мне искренне жаль.\nПопробуй ещё раз, что ли...\n=====================")
        log(traceback.format_exc())


log("Getting settings")
settings = read_settings()

log("Got", settings)

ya_disks = check_disks(settings["yadisk_tokens"])
vk_session=vk_api.VkApi(token=settings["vk_group_token"])

vk = vk_session.get_api()

longpoll = VkLongPoll(vk_session)

vkauth = VKAuth(settings["vk_user_login"], settings["vk_user_password"], api_v=api_v)
vkauth.auth()
session_html = vkauth.get_session()

log("Started!")
while 1:
    try:
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                user_id = event.user_id
                message_id = event.message_id
                log("New message: m_id = %d" % message_id)

                vk.messages.markAsRead(peer_id=user_id, start_message_id=message_id)
                vk.messages.setActivity(user_id=user_id, type="typing")
                log("Read, typing")
                
                redir_id = vk.messages.send(forward_messages=message_id, user_id=settings["vk_user_id"])
                log("Message redirected, id = %d" % redir_id)

                message = get_message()["fwd_messages"][0]

                th = threading.Thread(target=process, args=[user_id, message_id, message])
                th.start()

    except KeyboardInterrupt:
        log("Exiting\n\n")
        # stop_all = True
        # session_updater_th.join()
        exit(0)
    except BaseException:
        log(traceback.format_exc())
