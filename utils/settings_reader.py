# -*- coding: utf-8 -*-

def next_good(lines, i):
    i += 1
    while i < len(lines):
        if i >= 0 and lines[i] and not lines[i].startswith("#"):
            return i
        i += 1
    return -1

def read_settings():
    settings = {}
    setting_keys = ["vk_login", "vk_password", "vk_id", "vk_group_token", "vk_group_id"]
    line_n = -1
    with open("settings") as f:
        lines = f.read().split("\n")
        for key in setting_keys:
            line_n = next_good(lines, line_n)
            settings[key] = lines[line_n]
    line_n = next_good(lines, line_n)    
    settings["yadisk_tokens"] = []
    while line_n != -1:
        settings["yadisk_tokens"].append(lines[line_n])
        line_n = next_good(lines, line_n)
    return settings
