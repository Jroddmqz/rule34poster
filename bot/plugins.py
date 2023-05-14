import os
import asyncio
import logging
import requests
from PIL import Image
from bot import Mclient
from bs4 import BeautifulSoup


def resizer(_image_):
    with Image.open(_image_) as img:
        width, height = img.size
        img = img.convert("RGB")

    if width * height > 5242880 or width > 4096 or height > 4096:
        new_width, new_height = width, height
        while new_width * new_height > 5242880 or new_width > 4096 or new_height > 4096:
            new_width = int(new_width * 0.9)
            new_height = int(new_height * 0.9)

        resized_img = img.resize((new_width, new_height))
    else:
        resized_img = img

    path_, ext_ = os.path.splitext(_image_)
    newname = path_ + "lite" + ext_
    resized_img.save(newname)
    return newname


async def is_chat(client, item):
    try:
        chat_id = int(item)
        try:
            chat = await client.get_chat(chat_id)
        except:
            return None
        chat_id = chat.id
    except ValueError:
        if not item.startswith("@"):
            return None
        try:
            chat = await client.get_chat(item)
        except:
            return None
        chat_id = chat.id
    return chat_id


async def get_tags_rule34xxx(_id_):
    url = f"https://rule34.xxx/index.php?page=post&s=view&id={_id_}"
    headers = {
        "User-Agent": "Mi Agente de Usuario Personalizado",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")

        c = soup.find_all("li", class_="tag-type-character tag")
        character_ = []
        for li in c:
            a_tag = li.find_all_next("a", href=True)
            character_.append(a_tag[1].text)

        q = soup.find_all("li", class_="tag-type-copyright tag")
        copyright_ = []
        for li in q:
            a_tag = li.find_all_next("a", href=True)
            copyright_.append(a_tag[1].text)

        a = soup.find_all("li", class_="tag-type-artist tag")
        artist_ = []
        for li in a:
            a_tag = li.find_all_next("a", href=True)
            artist_.append(a_tag[1].text)
    else:
        print("Error al hacer la solicitud:", response.status_code)

    char_txt = ""
    for x in character_:
        char_txt = f"{char_txt} {x} "

    brand_txt = ""
    for x in copyright_:
        brand_txt = f"{brand_txt} {x} "

    artist_txt = ""
    for x in artist_:
        artist_txt = f"{artist_txt} {x} "

    txt = f"CHAR: {char_txt}\nBRAND: {brand_txt}\nARTIST: {artist_txt}"

    return txt


async def upload_file(client, file_path, chat_id, capy, ext_, x_item=False):
    print(f"{x_item['file_url']} -- {file_path}")
    if ext_.lower() in {'.jpg', '.png', '.webp', '.jpeg'}:
        new_file = resizer(file_path)
        try:
            sended = await client.send_photo(chat_id, photo=new_file, caption=str(capy))
            await asyncio.sleep(1)
            await client.send_document(chat_id, document=file_path)
        except:
            try:
                sended = await client.send_document(chat_id, document=file_path, caption=str(capy))
            except Exception as e:
                logging.error("[KBNIBOT] - Failed: " + f"{str(e)}")
        if os.path.exists(new_file):
            os.remove(new_file)
    elif ext_.lower() in {'.mp4', '.avi', '.mkv', '.mov'}:
        try:
            sended = await client.send_video(chat_id, video=file_path, caption=str(capy))
            await asyncio.sleep(1)
            await client.send_document(chat_id, document=file_path)
        except:
            try:
                sended = await client.send_document(chat_id, document=file_path, caption=str(capy))
            except Exception as e:
                logging.error("[KBNIBOT] - Failed: " + f"{str(e)}")
    else:
        try:
            sended = await client.send_document(chat_id, document=file_path, caption=str(capy))
        except Exception as e:
            logging.error("[KBNIBOT] - Failed: " + f"{str(e)}")

    os.remove(file_path)

    if x_item is None:
        pass
    else:
        db = Mclient["rule"]
        collect = db[f"{x_item['tag']}"]
        if sended != None:
            if not x_item['published']:
                filter = {'id': x_item['id']}
                update = {'$set': {'published': True}}
                collect.update_one(filter, update)


async def upload_from_queue(queue):
    while True:
        if not queue.empty():
            task = await queue.get()
            client, file_path, chat_id, capy, ext_, x = task
            await upload_file(client, file_path, chat_id, capy, ext_, x)
            queue.task_done()
        await asyncio.sleep(1)
