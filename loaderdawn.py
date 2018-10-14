# -*- coding: utf-8 -*-

import re
import os
import sys
import time
import json
import wget
import random
import vk_api
import requests
import traceback
import threading
import linecache
from utils.log import log
from utils.VKAuth import *
from utils.downloader import *
from utils.mes_getter import MesGetter
from utils.disk_utils import check_disks
from utils.settings_reader import read_settings
from vk_api.longpoll import VkLongPoll, VkEventType

WORKDIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(WORKDIR)


def get_audios(message):
    audios = []
    if "attachments" in message:
        for t in message["attachments"]:
            if t["type"] == "audio":
                log("Audio link:", t["audio"])
                url = t["audio"]["url"]
                if not url:
                    continue
                headers = requests.head(url, timeout=2).headers
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


def process(user_id, message_id):
    try:
        log("New message: m_id = %d" % message_id)

        vk.messages.markAsRead(peer_id=user_id, start_message_id=message_id)
        vk.messages.setActivity(user_id=user_id, type="typing")
        log("Read, typing")

        message = mgetter.reget_message(message_id)
        audios = get_audios(message)
        log("Found %d audios, starting sending\n\n" % len(audios))
        start = time.time()
        log("Start time", start)
        if audios:
            s = 0
            for elem in audios:
                s += elem["size"]
            log("All size:", s)
            log("Start time", start)
            vk.messages.send(user_id=user_id, message="=====================\nАудиозаписей найдено в вашем сообщении: %d, начинаю скачивать!\n=====================" % len(audios))
            for audios_part in download_by_parts(audios, 5, ya_disks):
                send_audios(audios_part, user_id)
                log("Part is done, message sent\n")

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
        log("End time", time.time())
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

vk_auth = VKAuth(settings["vk_user_login"], settings["vk_user_password"], api_v=settings["api_v"])
vk_auth.auth()
session_html = vk_auth.get_session()

mgetter = MesGetter(vk_auth, vk, settings)

log("Started!")
while 1:
    try:
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                user_id = event.user_id
                message_id = event.message_id

                th = threading.Thread(target=process, args=[user_id, message_id], name="Processing")
                th.start()

    except KeyboardInterrupt:
        log("Exiting\n\n")
        exit(0)
    except BaseException:
        log(traceback.format_exc())
