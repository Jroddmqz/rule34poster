from pymongo import MongoClient
from pyrogram import Client
import logging
from .config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [r34poster] - %(levelname)s - %(message)s",
)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("apscheduler").setLevel(logging.ERROR)

if not Config.api_id:
    logging.error("No Api-ID Found! Exiting!")
    quit(1)

if not Config.api_hash:
    logging.error("No ApiHash Found! Exiting!")
    quit(1)

if not Config.log_group:
    logging.error("No Log Group ID Found! Exiting!")
    quit(1)

if not Config.bot_token:
    logging.error("No bot_token Found! Exiting!")
    quit(1)

if Config.bot_token:
    bot = Client(
        "r34bot",
        api_id=Config.api_id,
        api_hash=Config.api_hash,
        bot_token=Config.bot_token,
        sleep_threshold=180,
    )
else:
    bot = None

if Config.log_group:
    log_group = Config.log_group

Mclient = MongoClient(Config.mongodb)
