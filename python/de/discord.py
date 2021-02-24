import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Awaitable, Dict, List, Set, Tuple, Union

import discord
import pandas as pd

from de.config import Config
from de.emojis import Emoji, EmojiMapping, load_emojis
from de.logger import logger

Seconds = float

DiscordID = str
EmojiPayloadRolesSet = List[DiscordID]
DiscordValue = Union[str, bool, DiscordID]

# mypy is extremely bad at handling recursive types, so we cheese it as hard as
# we can! And we need to, because the discord.py types are Any for all inputs
DiscordUnsafeObject = Dict[str, Union[DiscordValue, Dict[str, Any], List[Any]]]
DiscordUnsafeArray = List[Union[DiscordValue, DiscordUnsafeObject, List[Any]]]
DiscordArray = List[Union[DiscordValue, DiscordUnsafeObject, DiscordUnsafeArray]]
DiscordObject = Dict[str, Union[DiscordValue, DiscordArray, DiscordUnsafeObject]]


@dataclass
class Changeset:
    update: List[Tuple[str, DiscordObject, Emoji]]
    remove: List[Tuple[str, DiscordObject]]
    create: List[Tuple[str, Emoji]]

    @classmethod
    def diff(cls, upstream: List[DiscordObject], local: EmojiMapping) -> "Changeset":
        upstream_lookup: Dict[str, DiscordObject] = dict()
        upstream_keys: Set[str] = set()
        local_keys: Set[str] = set(local.keys())

        for up in upstream:
            if "name" in up and isinstance(up["name"], str):
                upstream_keys.add(up["name"])
                upstream_lookup[up["name"]] = up
            else:
                raise ValueError(f"Expected {up} to have a name!")

        return cls(
            update=[
                (key, upstream_lookup[key], local[key])
                for key in upstream_keys & local_keys
            ],
            remove=[(key, upstream_lookup[key]) for key in upstream_keys - local_keys],
            create=[(key, local[key]) for key in local_keys - upstream_keys],
        )

    def report(self) -> pd.DataFrame:
        table: List[List[str]] = []

        for name, _, _ in self.update:
            table.append([name, "UPDATE"])
        for name, _ in self.remove:
            table.append([name, "REMOVE"])
        for name, _ in self.create:
            table.append([name, "CREATE"])

        df = pd.DataFrame(data=table, columns=["name", "action"])

        return df


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

    async def get_custom_emoji_changeset(self):
        local = load_emojis()
        upstream = await self.get_all_custom_emojis()

        return Changeset.diff(upstream, local)
