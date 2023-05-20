import os
import math
import random
import string
import logging
import asyncio
import pymongo
import requests
from input import tags
from datetime import datetime
from bs4 import BeautifulSoup
from pymongo import DESCENDING
from bot import bot, Mclient, log_group
from pymongo.errors import CursorNotFound
from bot.plugins import is_chat, get_tags_rule34xxx, upload_file

temp = '.temp/'
if not os.path.exists(temp):
    os.makedirs(temp)

db = Mclient["rule"]
collections = {}
for tag in tags:
    collections[tag['tag']] = db[tag['tag']]


async def process(_tag_):
    for x in tags:
        if x['tag'] == _tag_:
            rule = x
            print(rule)

    api_rule_url = "https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&limit=100&tags="
    soup = BeautifulSoup(requests.get(f"{api_rule_url}{_tag_}").content, "lxml-xml")
    count = soup.posts.attrs['count']

    var = 0
    ok_in_chat = 0
    ok = 0
    post = []
    if rule['dump']:
        while var <= math.ceil(int(count) / 100):
            x_rule = f"{api_rule_url}{_tag_}&pid={var}"
            soup = BeautifulSoup(requests.get(x_rule).content, "lxml-xml")
            for x in soup.posts:
                if x == '\n':
                    continue
                post.append(x)
            var += 1
            await asyncio.sleep(1)
    else:
        for x in soup.posts:
            if x == '\n':
                continue
            post.append(x)

    collection = collections[_tag_]

    for x in post:
        item = {"id": x.get('id'), "file_url": x.get('file_url'), "source": x.get('source'), "tag": _tag_,
                "published": False}
        exist = collection.find_one({"id": x.get('id')})
        if not exist:
            collection.insert_one(item)

    _chat_id = await is_chat(bot, rule['channel'])
    if _chat_id is None:
        print(f"error chat id {_chat_id}")
        return

    regi = f"`{_tag_} - {count}items - Posting to{_chat_id}`"
    await bot.send_message(log_group, regi)

    items = collection.find().sort([("$natural", DESCENDING)])

    bound = 0

    for x in items:
        ok_in_chat += 1
        try:
            if bound < 100:
                if not x['published']:  # if x['published'] == False:
                    bound += 1
                    archive = x['file_url']
                    try:
                        response = requests.get(archive)
                    except:
                        regi = f"`Se omite {x['file_url']} con el id {x['id']} , descarga fallida`"
                        await bot.send_message(log_group, regi)
                        continue
                    if response.status_code == 200:
                        path_, ext_ = os.path.splitext(archive)
                        now = datetime.now()
                        date_time = now.strftime("%y%m%d_%H%M%S")
                        random_chars = ''.join(random.choices(string.ascii_letters + string.digits, k=2))
                        filename = f"{date_time}{random_chars}{ext_}"

                        with open(os.path.join(temp, filename), "wb") as f:
                            f.write(response.content)

                        txt = ""
                        try:
                            txt = await get_tags_rule34xxx(x['id'])
                        except Exception as e:
                            logging.error("[R34bOT] - Failed: " + f"{str(e)}")

                        url = x['source']
                        capy = f"""
[✨ SAUCE ✨]({url})

{txt}

{rule['caption']}
"""
                        filepath = f"{temp}{filename}"

                        print(f"{x['file_url']} -- {filepath}")
                        try:
                            await upload_file(bot, filepath, _chat_id, capy, ext_, x)
                            ok += 1
                        except Exception as e:
                            logging.error("[R34bOT] - Failed: " + f"{str(e)}")
                        # await queue.put((bot, filepath, _chat_id, capy, ext_, x))
            elif bound >= 100:
                regi = f"`Archivos procesados {_tag_}\n{ok}/{ok_in_chat}/{count}`"
                await bot.send_message(log_group, regi)
                await asyncio.sleep(10)
                bound = 0
                # asyncio.create_task(upload_from_queue(queue))
                # regi = "`Subiendo bloque de 10 imagenes`"
                # await bot.send_message(log_group, regi)
                # await queue.join()
        except pymongo.errors.CursorNotFound:
            items = collection.find().sort([("$natural", DESCENDING)])
            continue
        if ok_in_chat == count:
            break

    regi = f"`Archivos procesados {_tag_}\n{ok}/{ok_in_chat}/{count}`"
    await bot.send_message(log_group, regi)


async def run():
    ruta_actual = os.getcwd()
    print(ruta_actual)

    await bot.start()
    bot.me = await bot.get_me()

    ruler = tags

    while True:
        tasks = [asyncio.create_task(process(rule['tag'])) for rule in ruler]
        regi = f"`Ejecutando r34`"
        await bot.send_message(log_group, regi)
        await asyncio.gather(*tasks)
        await asyncio.sleep(86400)
    # await pyrogram.idle()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    bot.loop.run_until_complete(run())
