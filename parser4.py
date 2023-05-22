import asyncio
import logging
import re
import numpy as np
import gensim.downloader as api
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from natasha import MorphVocab, Doc, Segmenter
from telethon import TelegramClient, events, errors, functions
from telethon import types
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.errors import (
    ChannelPrivateError,
    UserBannedInChannelError,
    FloodWaitError,
    ChannelsTooMuchError,
    ChatAdminRequiredError,
)

morph_vocab = MorphVocab()

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

api_id = 23190232
api_hash = "4f9bdc4b8898f6b4e48cbb294b48b405"

accounts = {}  # словарь аккаунтов и каналов для них
posts = {}  # словарь аккаунтов и отправленных им постов
links = []
model_path = "fasttext-wiki-news-subwords-300"

client = TelegramClient('test', api_id, api_hash)
print("~Activated~")


def preprocess_text(text):
    words = text.split()
    words = [word for word in words if word in model.key_to_index]
    return ' '.join(words)


async def text_similarity(text1, text2):
    segmenter = Segmenter()

    doc1 = Doc(text1)
    doc2 = Doc(text2)

    doc1.segment(segmenter)
    doc2.segment(segmenter)

    doc1.tokens = [_.text.lower() for _ in doc1.tokens]
    doc2.tokens = [_.text.lower() for _ in doc2.tokens]

    intersection = set(doc1.tokens) & set(doc2.tokens)
    return len(intersection) / len(set(doc1.tokens) | set(doc2.tokens))


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


async def was_post(posts_, new_post):
    if not posts_:
        return False
    for post in posts_:
        sim = await text_similarity(post, new_post)
        print(sim)
        if sim > 0.6:
            return True
    return False


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
        posts[sender.username] = []
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
            if not await was_post(posts[chat], event.raw_text):
                tag = f"\n\n [{sender.title}] | [@eazy_news]"
                if isinstance(event.message.media, (types.MessageMediaPhoto, types.MessageMediaDocument)):
                    # Extract URLs from the message
                    urls = re.findall(r'(https?://\S+)', event.raw_text)
                    # Create a string with Markdown links
                    links_text = '\n'.join([f"[{url}]({url})" for url in urls])
                    # Add links to the message
                    message = f"{event.raw_text}\n{links_text}{tag}"
                    await client.send_message(
                        entity=chat,
                        file=event.message.media,
                        message=message,
                        parse_mode='md',
                        link_preview=False)
                    posts[chat].append(event.raw_text)
                else:
                    # Extract URLs from the message
                    urls = re.findall(r'(https?://\S+)', event.raw_text)
                    # Create a string with Markdown links
                    links_text = '\n'.join([f"[{url}]({url})" for url in urls])
                    # Add links to the message
                    message = f"{event.raw_text}\n{links_text}{tag}"
                    await client.send_message(
                        entity=chat,
                        message=message,
                        parse_mode='md',
                        link_preview=False)
                    posts[chat].append(event.raw_text)
            else:
                print("Caught a copyright")

    else:
        try:
            await client.send_message(sender, 'I don`t understand you. To start send "/start"')
        except ChatAdminRequiredError:
            print(f"Error: ChatAdminRequiredError, cannot send message to {sender.username}")


client.start()
client.run_until_disconnected()
