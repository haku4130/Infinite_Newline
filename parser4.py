from telethon import TelegramClient, events, errors, functions
from telethon.errors import FloodWaitError
from telethon.tl.functions.channels import JoinChannelRequest
import asyncio
import re
import logging
from telethon.tl.types import PeerUser, Channel

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

api_id = 23190232
api_hash = "4f9bdc4b8898f6b4e48cbb294b48b405"

accounts = {}  # словарь аккаунтов и каналов для них
links = []

client = TelegramClient('test1', api_id, api_hash)
print("~Activated~")


async def join_channel(channel):
    print(f'Joining the requested channel ({channel})')
    try:
        entity = await client.get_entity(channel)
    except errors.FloodWaitError as e:
        print('Flood for', e.seconds)
    try:
        await client(JoinChannelRequest(entity))
    except errors.FloodWaitError as e:
        print('Flood for', e.seconds)
    print('Success')


async def find_keys(dictionary, value):
    keys_list = []
    for key in dictionary:
        for item in dictionary[key]:
            entity = await client.get_entity(item)
            if entity == value:
                keys_list.append(key)
    return keys_list


def get_all_channels_link(dictionary):
    values = []
    for list_ in dictionary.values():
        for value in list_:
            if value not in values:
                values.append(value)
    return values


async def get_all_channels_title(dictionary):
    titles = []
    for list_ in dictionary.values():
        for value in list_:
            entity = await client.get_entity(value)
            if entity.title not in titles:
                titles.append(entity.title)
    return titles


async def get_all_channels_id(dictionary):
    ids = []
    for list_ in dictionary.values():
        for value in list_:
            entity = await client.get_entity(value)
            if entity.id not in ids:
                ids.append(entity.id)
    return ids


async def safe_send_message(chat, message, **kwargs):
    try:
        await client.send_message(chat, message, **kwargs)
    except FloodWaitError as e:
        print(f"Возникла ошибка флуда. Ожидание {e.seconds} секунд.")
        await asyncio.sleep(e.seconds)
        await safe_send_message(client, chat, message, **kwargs)


# @client.on(events.NewMessage(pattern='/start'))
# async def starter(event):
#     sender = await event.get_sender()
#     if sender.username in accounts:
#         await client.send_message(sender, 'Your account is already tracked')
#         return
#     print(f"This account is now tracked: {sender.username}")
#     await client.send_message(sender, 'Your account is now tracked')
#     accounts[sender.username] = []
#     await client.send_message(sender, 'Now you can send me links of one in each message (https://...)')


# @client.on(events.NewMessage(pattern=r"https://\S+"))
# async def channels_joiner(event):
#     sender = await event.get_sender()
#     if sender.username in accounts:
#         channel_link = event.raw_text
#         await join_channel(channel_link)
#         channels_ = accounts.get(sender.username)
#         channels_.append(channel_link)
#         accounts[sender.username] = channels_
#         await client.send_message(sender, 'Successfully added a channel to the track list')
#         print(accounts)
#     else:
#         await client.send_message(sender, 'Your account is not tracked yet, firstly send me "/start"')


@client.on(events.NewMessage())
async def messages(event):
    sender = await event.get_sender()
    if event.raw_text == '/start':
        if sender.username in accounts:
            await client.send_message(sender, 'Your account is already tracked')
            return
        print(f"This account is now tracked: {sender.username}")
        await client.send_message(sender, 'Your account is now tracked')
        accounts[sender.username] = []
        await client.send_message(sender, 'Now you can send me links of one in each message (https://...)')
    if event.raw_text == r"https://\S+":
        if sender.username in accounts:
            channel_link = event.raw_text
            await join_channel(channel_link)
            channels_ = accounts.get(sender.username)
            channels_.append(channel_link)
            accounts[sender.username] = channels_
            await safe_send_message(sender, 'Successfully added a channel to the track list')
            print(accounts)
        else:
            await client.send_message(sender, 'Your account is not tracked yet, firstly send me "/start"')
    if sender.id in await get_all_channels_id(accounts):
        clients = await find_keys(accounts, await client.get_entity(sender))
        for chat in clients:
            tag = f"\n\n [{sender.title}] | [@eazy_news]"
            await client.send_message(
                entity=chat,
                file=event.message.media,
                message=event.raw_text + tag,
                parse_mode='md',
                link_preview=False)


client.start()
client.run_until_disconnected()
