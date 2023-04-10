from telethon import TelegramClient, events, errors, functions
from telethon.tl import types
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.errors import (
    ChannelPrivateError,
    UserBannedInChannelError,
    FloodWaitError,
    ChannelsTooMuchError,
    ChatAdminRequiredError,
)
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

client = TelegramClient('test', api_id, api_hash)
print("~Activated~")


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


async def join_channel(channel, user):
    if channel in accounts.values():
        print("Already joined that channel")
        await client.send_message(user, "I already follow this channel")
        return 0
    print(f'Joining the requested by {user.username} channel ({channel})')
    entity = await client.get_entity(channel)
    try:
        await client(JoinChannelRequest(entity))
    except ChannelsTooMuchError:
        await client.send_message(user, "I have reached the maximum number of channels")
        return 1
    except ChannelPrivateError:
        await client.send_message(user, "Error: The channel specified is private and I lack permission to access it.")
        return 1
    except UserBannedInChannelError:
        await client.send_message(user, "Error: I am banned from this channel")
        return 1
    except FloodWaitError as e:
        await client.send_message(user, f"Error: FloodWaitError, waiting {e.seconds} seconds")
        await asyncio.sleep(e.seconds)
        return await join_channel(channel, user)
    except Exception as e:
        print(f"Error: {e}")
        return 1
    print("Success")
    await client.send_message(user, "Success")
    return 0


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

    elif re.match(r"https://\S+", event.raw_text):
        if sender.username in accounts:
            channel_link = event.raw_text
            if not await join_channel(channel_link, sender):
                channels_ = accounts.get(sender.username)
                channels_.append(channel_link)
                accounts[sender.username] = channels_
                await client.send_message(sender, 'Successfully added a channel to the track list')
        else:
            await client.send_message(sender, 'Your account is not tracked yet, firstly send me "/start"')

    elif sender.id in await get_all_channels_id(accounts):
        clients = await find_keys(accounts, await client.get_entity(sender))
        for chat in clients:
            tag = f"\n\n [{sender.title}] | [@eazy_news]"
            if isinstance(event.message.media, (types.MessageMediaPhoto, types.MessageMediaDocument)):
                await client.send_message(
                    entity=chat,
                    file=event.message.media,
                    message=event.raw_text + tag,
                    parse_mode='md',
                    link_preview=False)
            else:
                await client.send_message(
                    entity=chat,
                    message=event.raw_text + tag,
                    parse_mode='md',
                    link_preview=False)

    else:
        try:
            await client.send_message(sender, 'I don`t understand you. To start send "/start"')
        except ChatAdminRequiredError:
            print(f"Error: ChatAdminRequiredError, cannot send message to {sender.username}")


client.start()
client.run_until_disconnected()
