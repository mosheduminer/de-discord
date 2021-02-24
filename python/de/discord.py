import asyncio
from contextlib import asynccontextmanager
from typing import Awaitable

import discord

from de.config import Config
from de.logger import logger

Seconds = float


class DiscordBot:
    CLOSE_TIMEOUT: Seconds = 5.0

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

    @asynccontextmanager
    async def connection(self):
        """
        An async context manager for starting the bot long enough to complete a task
        and then closing it. It's not particularly graceful because the bot library is
        designed to "run forever," but it is what it is!
        """

        task = asyncio.create_task(self.start())

        async def raise_task_errors(aw: Awaitable):
            await asyncio.wait([aw, task], return_when=asyncio.FIRST_COMPLETED)

            if task.done():
                exc = task.exception()
                if exc:
                    raise exc

        try:
            await raise_task_errors(self.wait_until_ready())
            yield self
        except Exception as exc:
            await self.close()
            await raise_task_errors(asyncio.sleep(self.CLOSE_TIMEOUT))
            raise exc
        else:
            await self.close()
            await raise_task_errors(asyncio.sleep(self.CLOSE_TIMEOUT))

    async def get_all_custom_emojis(self):
        return await self.client.http.get_all_custom_emojis(self.config.BOT_GUILD_ID)
