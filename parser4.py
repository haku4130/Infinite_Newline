from telethon import TelegramClient, events, errors, functions
from telethon.tl.functions.channels import JoinChannelRequest
import asyncio
import re
import logging
from telethon.tl.types import PeerUser, Channel

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

api_id = 23190232
api_hash = "4f9bdc4b8898f6b4e48cbb294b48b405"

channels = [
    'https://t.me/meduzalive', 'https://t.me/Ateobreaking', 'https://t.me/dvachannel', 'https://t.me/moscowmap',
    'https://t.me/msk_live', 'https://t.me/mosmap', 'https://t.me/something_with_something_s'
]  # откуда

public_channels = []  # откуда, но только открытые

sender = ''  # куда

KEYS = {
    # "ссылка:": "",
    # "Америка": "США",
    # r"@\S+": "Максим",
    # r"https://\S+": "",
    # r"http://\S+": "",
}

Bad_Keys = []

tags = ''  # добавление текста к посту

starter_called = False  # keep track of whether starter function has been called


async def is_public_channel(client, channel_link):
    try:
        entity = await client.get_entity(channel_link)
        return entity.access_hash == 0
    except ValueError:
        return False


async def join_public_channels():
    print('~Joining the requested channels~')
    async with TelegramClient('newline_bot', api_id, api_hash) as client:
        for channel in channels:
            if 1:  # await is_public_channel(client, channel):
                print(channel)
                public_channels.append(channel)
                entity = await client.get_entity(channel)
                await client(JoinChannelRequest(entity))
    print('~Success~')


client_ = TelegramClient('newline_bot', api_id, api_hash)


@client_.on(events.NewMessage)
async def starter(event):
    global starter_called
    # if isinstance(event.message.peer_id, PeerUser):
    if '/start' in event.raw_text:
        global sender
        sender = await event.get_sender()
        print(sender.username)
        starter_called = True
        await client_.send_message(sender, '~Activated~')
        await client_.send_message(sender, 'Send me links to channels you want to see (in one message)')


@client_.on(events.NewMessage(chats=public_channels))
async def messages(event):
    global starter_called  # check global variable
    if starter_called:  # execute only after starter function is called
        await client_.send_message(sender, event.message)


loop = asyncio.get_event_loop()
loop.run_until_complete(join_public_channels())
client_.start()
client_.run_until_disconnected()
