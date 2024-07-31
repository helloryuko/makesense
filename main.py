from aiogram import Bot, Dispatcher

from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode

from msgspec import json, Struct

import aiofiles
import asyncio
import random

# --- #

class Strings(Struct):
    welcome: str
    no_args: str

class Config(Struct):
    api_token: str
    strings: Strings

    surroundings: list[str]
    base: list[str]
    transformers: list[list[str]]
    phrases: list[str]
    
    log_file: str | None = None

config: Config | None = None

# --- #

text_log_queue: asyncio.Queue[tuple[str, str]] = asyncio.Queue()

async def save_queue_task():
    while True:
        try:
            text = await text_log_queue.get()

            # я не знаю почему не можно юзать один контекст
            # на весь вайл тру но ладно
            async with aiofiles.open(config.log_file, "a") as f:
                await f.write(f'"{text[0]}" -> "{text[1]}"\n')
        except asyncio.QueueEmpty:
            pass

# --- #

dp = Dispatcher()

@dp.message(Command('start'))
async def send_welcome(message: Message):
    await message.answer(config.strings.welcome)

@dp.message(Command('get'))
async def send_phrase(message: Message):
    await message.reply(random.choice(config.phrases))

@dp.message()
async def make_sense(message: Message):
    surround = random.choice(config.surroundings)
    transformer = random.choice(config.transformers)

    ret = message.text

    for (source, replace) in zip(config.base, transformer):
        for to_replace, replacable in zip(source, replace):
            ret = ret.replace(to_replace, replacable)

    ret = f"{surround} {ret} {surround}"

    text_log_queue.put_nowait((message.text, ret)) 

    await message.reply(ret)

# --- #

async def main():
    global config

    try:
        with open("config.json", "r") as f:
            config = json.decode(f.read(), type=Config)
    except FileNotFoundError:
        print("FATAL: config.json doesn't exist.")
        exit(1)

    bot = Bot(
        token = config.api_token,
        default = DefaultBotProperties(
            parse_mode = ParseMode.HTML,
            link_preview_is_disabled = True
        )
    )

    if config.log_file:
        asyncio.create_task(save_queue_task())

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())