# -*- coding: utf-8 -*-

import json
import time
import threading
from .log import log
from .strings import rand_st

class MesGetter:
    def __init__(self, vk_user, vk_group, settings):
        self.vk_user = vk_user
        self.vk_user_id = settings["vk_user_id"]
        self.vk_group = vk_group
        self.vk_group_id = settings["vk_group_id"]
        self.api_v = settings["api_v"]

        self.session_user = self.vk_user.get_session()

        # self.updater_thr = threading.Thread(target=self.updater, args=(5,))
        # self.updater_thr.start()
        # self.locked = False
        # log("asdasdasdasdasdasd")

    # def updater(self, timeout):
    #     while 1:
    #         self.session_user.get("https://vk.com/dev/messages.getHistory")
    #         time.sleep(0.5)
    #         print(1)

            

    def reget_message(self, message_id):
        self.updater_thr.kill()
        while self.locked:
            pass

        self.locked = True

        key = rand_st(5)
        redir_id = self.vk_group.messages.send(message=key, forward_messages=message_id, user_id=self.vk_user_id)
        log("Message with key %s redirected, id = %d" % (key, redir_id))

        m = self.check_message()
        log("Got message back with key = %s" % m["text"])
        if m["text"] != key:
            raise Exception("Key is not valid")

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