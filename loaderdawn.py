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
from utils.audiomusic import Audio
from utils.mes_getter import MesGetter
from utils.disk_utils import check_disks
from utils.settings_reader import read_settings
from vk_api.longpoll import VkLongPoll, VkEventType

WORKDIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(WORKDIR)

def rand():
    return random.randint(1, 10000000)

def get_attached_audio_info(message):
    audios = []
    if "attachments" in message:
        for t in message["attachments"]:
            if t["type"] == "audio":
                audio = {
                          "id" : t["audio"]["id"],
                    "owner_id" : t["audio"]["owner_id"],
                      "artist" : t["audio"]["artist"],
                       "title" : t["audio"]["title"]
                }
                if "url" in t["audio"]:
                    audio["url"] = t["audio"]["url"]
                if "access_token" in t["audio"]:
                    audio["access_token"] = t["audio"]["access_token"]
                audios.append(audio)

    if "fwd_messages" in message:
        for fwd_mes in message["fwd_messages"]:
            audios += get_attached_audio_info(fwd_mes)
    return audios

def send_audios(audios, user_id):
    text = ""
    for audio in audios:
        text += "%s - %s\n%s\n\n" % (audio.artist, audio.title, audio.url)
    vk.messages.send(user_id=user_id, message=text, random_id=rand())

def get_pl_url(message):
    if "attachments" in message:
        for attachment in message["attachments"]:
            if attachment["type"] == "link" and attachment["link"]["caption"] == "Плейлист":
               return attachment["link"]["url"]
    if "fwd_messages" in message:
        for fwd_mes in message["fwd_messages"]:
            t = get_pl_url(fwd_mes)
            if t:
                return t
    return False

def send_pl(url, user_id):
    pl_audio = []

    html_code = vk_session.http.get(url).content.decode("utf-8")

    for t in [m.start() for m in re.finditer('id="audio', html_code)]:
        first = html_code.find("_", t)
        end = html_code.find("_", first + 1)
        pl_audio.append(tuple(map(int, html_code[t+9:end].split("_"))))
    
    n_mus = len(pl_audio)

    d = []
    for t in pl_audio:
        d.append({"owner_id" : t[0], "id" : t[1]})
    audios = mgetter.get_vk_audios(d)
    for audios_part in download_by_parts(audios, 5, ya_disks):
        send_audios(audios_part, user_id)
        log("Part is done, message sent\n")

def get_wall_audio_info(message):
    audios = []
    for bigat in message["attachments"]:
        if bigat["type"] == "wall":
            for t in bigat["wall"]["attachments"]:
                if t["type"] == "audio":
                    audio = {
                              "id" : t["audio"]["id"],
                        "owner_id" : t["audio"]["owner_id"],
                          "artist" : t["audio"]["artist"],
                           "title" : t["audio"]["title"]
                    }
                    if "access_token" in t["audio"]:
                        audio["access_token"] = t["audio"]["access_token"]
                    audios.append(audio)

    if "fwd_messages" in message:
        for fwd_mes in message["fwd_messages"]:
            audios += get_wall_audio_info(fwd_mes)
    return audios

def process(user_id, message_id):
    try:
        log("New message: m_id = %d" % message_id)

        log("Read, typing")

        message = vk.messages.getById(message_ids=message_id)["items"][0]
        log(message)

        infos = []
        infos += get_attached_audio_info(message)
        infos += get_wall_audio_info(message)
        withurl = []
        nourl = []
        for elem in infos:
            if "url" in elem:
                withurl.append(elem)
            else:
                nourl.append(elem)

        log("Infos:", infos)
        log("\nWith url:", withurl)
        log("\nNo url:", nourl)

        audios = []
        for elem in withurl:
            audios.append(Audio(
                   title = elem["title"], 
                  artist = elem["artist"], 
                   vkurl = elem["url"]
                ))
        audios += mgetter.get_vk_audios(nourl)
        log("Found %d audios, starting sending\n\n" % len(audios))
        start = time.time()
        log("Start time", start)
        if audios:
            all_size = 0
            for audio in audios:
                all_size += audio.size
            log("All size:", all_size)
            log("Start time", start)
            vk.messages.send(user_id=user_id, message="=====================\nАудиозаписей найдено в вашем сообщении: %d, начинаю создавать ссылки!\n=====================" % len(audios), random_id=rand())
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

        if not audios and not pl_url:
            log("No audios, no playlist. Zachem pisal? Neyasno. ")
            vk.messages.send(user_id=user_id, message="=====================\nПришли мне песню или плейлист, и я помогу тебе скачать твою любимую музыку!\n=====================", random_id=rand())
        else:
            time.sleep(0.5)
            vk.messages.send(user_id=user_id, random_id=rand(), message="=====================\n" +  
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

    except Exception:
        vk.messages.send(user_id=user_id, random_id=rand(), message="=====================\nОй!\nЧто-то пошло не так. Мне искренне жаль.\nПопробуй ещё раз, что ли...\n=====================")
        log(traceback.format_exc())


log("Getting settings")
settings = read_settings()

log("Got", settings)

ya_disks = check_disks(settings["yadisk_tokens"])
vk_session = vk_api.VkApi(token=settings["vk_group_token"])

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
