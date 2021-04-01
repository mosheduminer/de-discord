"""Force reload all emojis

Revision ID: f4cc442b3233
Revises: 
Create Date: 2021-04-01 00:45:27.076123+00:00

"""

import asyncio
from alembic import op
import sqlalchemy as sa

from de.config import Config
from de.discord import DiscordBot, REPLACE
from de.logger import logger


# revision identifiers, used by Alembic.
revision = "f4cc442b3233"
down_revision = None
branch_labels = None
depends_on = None


async def run_migration():
    config = Config.load()
    bot = DiscordBot(config)

    async with bot.connection():
        changeset = await bot.get_custom_emoji_changeset()

        await bot.apply_custom_emoji_changeset(changeset, update_action=REPLACE)


def upgrade():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_migration())


def downgrade():
    pass
