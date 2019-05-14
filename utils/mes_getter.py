# -*- coding: utf-8 -*-

import json
import time
import random
import requests
import threading
from .log import log
from .strings import rand_st
from .audiomusic import Audio

def rand():
    return random.randint(1, 10000000)

class MesGetter:
    def __init__(self, vk_user, vk_group, settings):
        self.vk_user = vk_user
        self.vk_user_id = settings["vk_user_id"]
        self.vk_group = vk_group
        self.vk_group_id = settings["vk_group_id"]
        self.api_v = settings["api_v"]

        self.session_user = self.vk_user.get_session()

        self.locked = False


    def reget_message(self, message_id):
        while self.locked:
            pass

        self.locked = True

        try:
            key = rand_st(5)
            redir_id = self.vk_group.messages.send(message=key, forward_messages=message_id, user_id=self.vk_user_id, random_id=rand())
            log("Message with key %s redirected, id = %d" % (key, redir_id))

            m = self.check_message()
            log("Got message back with key = %s" % m["text"])
            if m["text"] != key:
                self.locked = False
                raise Exception("Key is not valid")
        except BaseException as e:
            self.locked = False
            raise Exception(e)    

        self.locked = False
        return m["fwd_messages"][0]


    def check_message(self):
        req = self.session_user.get("https://vk.com/dev/messages.getHistory")
        
        hash_p = req.content.find(b"Dev.methodRun(")
        hash_st = req.content[hash_p+15 : hash_p+44]

        d = {
            "act": "a_run_method",
            "al" : "1",
            "hash" : hash_st,
            "method" : "messages.getHistory",
            "param_count": "1",
            "param_user_id": self.vk_group_id,
            "param_v": self.api_v
        }
        message = self.session_user.post("https://vk.com/dev", data=d).content
        decoded_message = message.decode("cp1251")
        pos_resp = decoded_message.find('{"response"')
        decoded_message = decoded_message[pos_resp:]
        result = json.loads(decoded_message)["response"]["items"][0]
        return result

    def get_vk_audios(self, id_arr):
        aps = 10
        audios = []
        for i in range(0, len(id_arr), aps):

            cids = id_arr[i : min(len(id_arr), i + aps)]
            attachment_st = ""
            for id in cids:
                st = "audio%s_%s" % (id["owner_id"], id["id"])
                if "access_token" in id:
                    st += "_%s" % id["access_token"]
                attachment_st += st + ","


            while self.locked:
                pass
            self.locked = True

            try:
                key = rand_st(5)
                redir_id = self.vk_group.messages.send(message=key, attachment=attachment_st, user_id=self.vk_user_id, random_id=rand())
                print(attachment_st)
                log("Message with key %s redirected, id = %d" % (key, redir_id))

                m = self.check_message()
                log("Got message back with key = %s" % m["text"])
                if m["text"] != key:
                    self.locked = False
                    raise Exception("Key is not valid")
            except BaseException as e:
                self.locked = False
                raise Exception(e)    

            self.locked = False
            for attachment in m["attachments"]:
                url = attachment["audio"]["url"]
                if not url:
                    continue
                headers = requests.head(url, timeout=2).headers
                audio = Audio(title = attachment["audio"]["title"], 
                             artist = attachment["audio"]["artist"], 
                              vkurl = url, 
                               size = int(headers["Content-Length"]))

                log(audio.vkurl)
                audios.append(audio)

        return audios

