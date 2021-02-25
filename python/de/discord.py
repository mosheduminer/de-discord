import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Awaitable, Dict, List, Optional, Set, Tuple, Union

import discord
import pandas as pd

from de.config import Config
from de.emojis import Emoji, EmojiMapping, image_base64, load_emojis
from de.logger import logger

DiscordID = str

JSValue = Union[str, int, float, bool, None]
JSArray = List[
    Union[
        JSValue,
        Dict[str, Union[JSValue, Dict[str, Any], List[Any]]],
        List[Union[JSValue, Dict[str, Any], List[Any]]],
    ]
]
JSObject = Dict[
    str, Union[JSValue, JSArray, Dict[str, Union[JSValue, Dict[str, Any], List[Any]]]]
]
JSON = Union[JSValue, JSArray, JSObject]


@dataclass
class EmojiResource:
    id: DiscordID
    name: str
    roles: List[DiscordID]
    user: Optional[JSON]
    require_colons: bool
    managed: bool
    animated: bool

    @classmethod
    def from_payload(cls, payload: JSON):
        if not isinstance(payload, dict):
            raise ValueError(f"Expected payload {payload} to be an object!")
        if "id" in payload:
            id_ = str(payload["id"])
        else:
            raise ValueError(f"Expected payload {payload} to include an ID!")

        if "name" in payload:
            name = str(payload["name"])
        else:
            raise ValueError(f"Expected payload {payload} to include a name!")

        if "roles" in payload:
            if isinstance(payload["roles"], list):
                roles: List[DiscordID] = [str(id_) for id_ in payload["roles"]]
            else:
                raise ValueError(
                    f"Expected payload {payload} to have an array of role IDs!"
                )
        else:
            roles = []

        user = payload.get("user", dict())

        if "require_colons" in payload:
            require_colons = bool(payload["require_colons"])
        else:
            raise ValueError(
                f"Expected payload {payload} to include 'require_colons' property!"
            )

        if "managed" in payload:
            managed = bool(payload["managed"])
        else:
            raise ValueError(
                f"Expected payload {payload} to include 'managed' property!"
            )

        if "animated" in payload:
            animated = bool(payload["animated"])
        else:
            raise ValueError(
                f"Expected payload {payload} to include 'animated' property!"
            )

        return cls(
            id=id_,
            name=name,
            roles=roles,
            user=user,
            require_colons=require_colons,
            managed=managed,
            animated=animated,
        )


REPORT_COLS = [
    "name",
    "action",
    "discord_id",
    "path",
    "roles",
    "require_colons",
    "managed",
    "animated",
]

ReportRow = Dict[str, Any]


def report_row(
    name: str,
    action: str,
    *,
    resource: Optional[EmojiResource] = None,
    emoji: Optional[Emoji] = None,
):
    row: ReportRow = dict(name=name, action=action)

    if resource is not None:
        row["discord_id"] = resource.id
        row["roles"] = ", ".join(resource.roles)
        row["require_colons"] = resource.require_colons
        row["managed"] = resource.managed
        row["animated"] = resource.animated

    if emoji is not None:
        row["path"] = emoji.path

    return row


class UpdateAction:
    def __init__(self, slug: str):
        self._slug = slug

    def __str__(self):
        return self._slug

    def __repr__(self):
        return f"<{self._slug}>"


EDIT = UpdateAction("edit")
REPLACE = UpdateAction("replace")


@dataclass
class Changeset:
    update: List[Tuple[str, EmojiResource, Emoji]]
    remove: List[Tuple[str, EmojiResource]]
    create: List[Tuple[str, Emoji]]

    @classmethod
    def diff(cls, upstream: List[EmojiResource], local: EmojiMapping) -> "Changeset":
        upstream_lookup: Dict[str, EmojiResource] = dict()
        upstream_keys: Set[str] = set()
        managed_keys: Set[str] = set()
        local_keys: Set[str] = set(local.keys())

        for up in upstream:
            upstream_lookup[up.name] = up
            if up.managed:
                managed_keys.add(up.name)
                logger.info(f"Emoji {up.name} is managed, so leaving it alone...")
            else:
                upstream_keys.add(up.name)

        return cls(
            update=[
                (key, upstream_lookup[key], local[key])
                for key in upstream_keys & local_keys
            ],
            remove=[(key, upstream_lookup[key]) for key in upstream_keys - local_keys],
            create=[
                (key, local[key]) for key in local_keys - upstream_keys - managed_keys
            ],
        )

    def report(self, update_action: UpdateAction = EDIT) -> pd.DataFrame:
        table: List[ReportRow] = []

        for name, r, e in self.update:
            table.append(report_row(name, str(update_action), resource=r, emoji=e))
        for name, r in self.remove:
            table.append(report_row(name, "remove", resource=r))
        for name, e in self.create:
            table.append(report_row(name, "create", emoji=e))

        df = pd.DataFrame(data=table, columns=REPORT_COLS)

        return df


Seconds = float


class DiscordBot:
    CLOSE_TIMEOUT: Seconds = 5.0

    def __init__(self, config: Config):
        self.config = config
        self.client: discord.Client = discord.Client()

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
        designed to "run forever" and deeply couples the persistent websocket
        connection with the aiohttp session objects we *actually* need, but it is what
        it is!
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
        return [
            EmojiResource.from_payload(raw)
            for raw in await self.client.http.get_all_custom_emojis(
                self.config.BOT_GUILD_ID
            )
        ]

    async def get_custom_emoji_changeset(self):
        local = load_emojis()
        upstream = await self.get_all_custom_emojis()

        return Changeset.diff(upstream, local)

    async def create_custom_emoji(
        self,
        emoji: Emoji,
        *,
        roles: Optional[List[DiscordID]] = None,
        reason: Optional[str] = None,
    ):
        return await self.client.http.create_custom_emoji(
            self.config.BOT_GUILD_ID,
            emoji.name,
            image_base64(emoji.image(), format="png"),
            roles=roles,
            reason=reason,
        )

    async def delete_custom_emoji(self, emoji_id: DiscordID):
        return await self.client.http.delete_custom_emoji(
            self.config.BOT_GUILD_ID, emoji_id
        )

    async def edit_custom_emoji(
        self,
        emoji_id: DiscordID,
        name: str,
        *,
        roles: Optional[List[DiscordID]] = None,
        reason: Optional[str] = None,
    ):
        return await self.client.http.edit_custom_emoji(
            self.config.BOT_GUILD_ID, emoji_id, name, roles=roles, reason=reason
        )

    async def replace_custom_emoji(
        self,
        emoji_id: DiscordID,
        emoji: Emoji,
        *,
        roles: Optional[List[DiscordID]] = None,
        reason: Optional[str] = None,
    ):
        """
        Discord only allows for editing the roles or name of an emoji and not
        the actual image associated with it. This removes the old one and
        creates a new one.
        """

        return (
            await self.delete_custom_emoji(emoji_id),
            await self.create_custom_emoji(emoji, roles=roles, reason=reason),
        )

    async def apply_custom_emoji_changeset(
        self, changeset: Changeset, update_action: UpdateAction = EDIT
    ):
        for name, emoji in changeset.create:
            logger.info(f"Creating emoji {name}...")
            await self.create_custom_emoji(emoji, reason="Creating a fresh emoji!")
        for name, resource in changeset.remove:
            logger.info(f"Removing emoji {name}...")
            await self.delete_custom_emoji(resource.id)
        for name, resource, emoji in changeset.update:
            if update_action == REPLACE:
                logger.info(f"Individually replacing emoji {name}...")
                await self.replace_custom_emoji(
                    resource.id, emoji, reason="Issuing a blind replace!"
                )
            else:
                logger.info(f"I would edit emoji {name} if that were implemented...")
