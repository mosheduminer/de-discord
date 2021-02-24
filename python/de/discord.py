import asyncio
from contextlib import asynccontextmanager
from typing import Awaitable

import discord

from de.config import Config
from de.logger import logger


class AlreadyRunningError(Exception):
    pass


class DiscordBot:
    def __init__(self, config: Config):
        self.config = config
        self.client = discord.Client()

    async def start(self):
        logger.info("Starting the Discord bot...")
        await self.client.start(self.config.DISCORD_API_TOKEN)

    async def close(self):
        logger.info("Closing the Discord bot websocket connection...")
        await self.client.close()

    async def wait_until_ready(self):
        await self.client.wait_until_ready()
        logger.info("The bot is ready!")


Seconds = float

CLOSE_TIMEOUT: Seconds = 5.0


@asynccontextmanager
async def discord_bot(config: Config):
    """
    An async context manager for starting the bot long enough to complete a task
    and then closing it. It's not particularly graceful because the bot library is
    designed to "run forever," but it is what it is!
    """
    bot = DiscordBot(config)

    task = asyncio.create_task(bot.start())

    async def raise_task_errors(aw: Awaitable):
        await asyncio.wait([aw, task], return_when=asyncio.FIRST_COMPLETED)

        if task.done():
            exc = task.exception()
            if exc:
                raise exc

    try:
        await raise_task_errors(bot.wait_until_ready())

        yield bot

    except Exception as exc:
        await bot.close()
        await raise_task_errors(asyncio.sleep(CLOSE_TIMEOUT))
        raise exc
    else:
        await bot.close()
        await raise_task_errors(asyncio.sleep(CLOSE_TIMEOUT))
