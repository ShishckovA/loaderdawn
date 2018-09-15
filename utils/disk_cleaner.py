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
import threading
import linecache
from VKAuth import *
from vk_api.longpoll import VkLongPoll, VkEventType


api_v = 5.84

with open("tokens") as f:
    token_list = f.readlines()


