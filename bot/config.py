# -*- encoding: utf-8 -*-
"""Config vars module"""
import os

from dotenv import load_dotenv

load_dotenv()


class Config(object):
    api_id = int(os.environ.get('API_ID'))
    api_hash = os.environ.get('API_HASH', None)
    bot_token = os.environ.get('BOT_TOKEN', None)
    log_group = int(os.environ.get('LOG_GROUP', False))
    mongodb = os.environ.get('MONGODB')