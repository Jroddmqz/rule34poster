import os
import math
import random
import string
import logging
import asyncio
import pyrogram
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from pymongo import DESCENDING
from bot import bot, Mclient, log_group
from bot.plugins import is_chat, get_tags_rule34xxx, upload_from_queue
from input import tags

temp = '.temp/'
if not os.path.exists(temp):
    os.makedirs(temp)

async def r34():
    regi = "`Ejecutando r34, esto puede tardar algunos minutos`"
    await bot.send_message(log_group, regi)

    async def process(rule):
        api_rule_url = "https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&tags="
        print(rule['tag'])
        soup = BeautifulSoup(requests.get(f"{api_rule_url}{rule['tag']}").content, "lxml-xml")
        count = soup.posts.attrs['count']

        var = 0
        post = []
        while var <= math.ceil(int(count) / 100):
            x_rule = f"{api_rule_url}{rule['tag']}&pid={var}"
            soup = BeautifulSoup(requests.get(x_rule).content, "lxml-xml")
            for x in soup.posts:
                if x == '\n':
                    continue
                post.append(x)
            var += 1
            await asyncio.sleep(1)

        collection = db[f"{rule['tag']}"]

        for x in post:
            item = {"id": x.get('id'), "file_url": x.get('file_url'), "source": x.get('source'), "tag": rule['tag'],
                    "published": False}
            exist = collection.find_one({"id": x.get('id')})
            if not exist:
                collection.insert_one(item)

        _chat_id = await is_chat(bot, rule['channel'])
        if _chat_id is None:
            print(f"error chat id {_chat_id}")
            return

        regi = f"```{rule['tag']} - {count}items - Posting to{_chat_id}```"
        await bot.send_message(log_group, regi)

        items = collection.find().sort([("$natural", DESCENDING)])

        bound = 0

        for x in items:
            if bound < 10:
                if not x['published']:  # if x['published'] == False:
                    bound += 1
                    archive = x['file_url']
                    try:
                        response = requests.get(archive)
                    except:
                        regi = f"```Se omite {x['file_url']} con el id {x['id']} , descarga fallida```"
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

                        await queue.put((bot, filepath, _chat_id, capy, ext_, x))
            elif bound >= 10:
                asyncio.create_task(upload_from_queue(queue))
                regi = "```Subiendo bloque de 10 imagenes```"
                await bot.send_message(log_group, regi)
                await queue.join()
                bound = 0

    queue = asyncio.Queue()
    db = Mclient["rule"]
    ruler = tags

    while True:
        tasks = [asyncio.create_task(process(rule)) for rule in ruler]
        await asyncio.gather(*tasks)
        await asyncio.sleep(1)


async def run():
    ruta_actual = os.getcwd()
    print(ruta_actual)

    await bot.start()
    bot.me = await bot.get_me()
    await r34()

    await pyrogram.idle()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    bot.loop.run_until_complete(run())
