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

accounts = {}  # словарь аккаунтов и каналов для них

KEYS = {
    # "ссылка:": "",
    # "Америка": "США",
    # r"@\S+": "Максим",
    # r"https://\S+": "",
    # r"http://\S+": "",
}

Bad_Keys = []

starter_called = False
joiner_called = False

client_ = TelegramClient('test', api_id, api_hash)
print("~Activated~")


async def join_channel(channel):
    print(f'~Joining the requested channel ({channel})~')
    entity = await client_.get_entity(channel)
    await client_(JoinChannelRequest(entity))
    print('~Success~')


def find_keys(dictionary, value):
    keys_list = []
    for key in dictionary:
        if value in dictionary[key]:
            keys_list.append(key)
    return keys_list


@client_.on(events.NewMessage(pattern='/start'))
async def starter(event):
    sender = await event.get_sender()
    global starter_called
    if starter_called:
        await client_.send_message(sender, 'Your account is already tracked')
        return
    print(f"This account is now tracked: {sender.username}")
    starter_called = True
    await client_.send_message(sender, '~Activated~')
    accounts[sender.username] = []
    await client_.send_message(sender, 'Now you can send me links of one in each message (https://...)')


@client_.on(events.NewMessage(pattern=r"https://\S+"))
async def channels_joiner(event_):
    global starter_called
    if starter_called:
        global joiner_called
        joiner_called = True
        channel_name = event_.raw_text
        await join_channel(channel_name)
        sender = await event_.get_sender()
        channels_ = accounts.get(sender.username)
        channels_.append(channel_name)
        accounts[sender.username] = channels_


@client_.on(events.NewMessage(chats=list(accounts.values())))
async def messages(event):
    global starter_called
    if starter_called and joiner_called:
        reqs_chats = find_keys(accounts, event.get_sender())
        for chat in reqs_chats:
            tag = f"\n\n [{event.get_sender()}] | [@eazy_news]"
            await client_.send_message(
                entity=chat,
                file=event.message.media,
                message=event.raw_text + tag,
                parse_mode='md',
                link_preview=False)


client_.start()
client_.run_until_disconnected()
