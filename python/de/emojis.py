import base64
from dataclasses import dataclass, field
from functools import lru_cache
from io import BytesIO
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict

from PIL import Image

from de.config import EMOJIS_DIR


EmojiName = str
EmojiFormat = str


EMOJI_WIDTH = 128  # px
EMOJI_HEIGHT = 128  # px
EMOJI_SIZE = (EMOJI_WIDTH, EMOJI_HEIGHT)


@dataclass(eq=True, frozen=True)
class Emoji:
    name: EmojiName = field(compare=True)
    path: Path

    @classmethod
    def from_listing(cls, lx: str):
        path = EMOJIS_DIR / lx
        return cls(name=path.stem, path=path)

    @lru_cache()
    def image(self):
        original = Image.open(str(self.path))
        im = original.crop(original.getbbox())
        im.thumbnail(size=EMOJI_SIZE)
        return im


EmojiMapping = Dict[EmojiName, Emoji]


def load_emojis() -> EmojiMapping:
    return {
        emoji.name: emoji
        for emoji in (Emoji.from_listing(lx) for lx in os.listdir(EMOJIS_DIR))
    }


SizeInBytes = int

KILOBYTES = 1024
EMOJI_MAX_SIZE: SizeInBytes = 256 * KILOBYTES


def image_size(image: Image, format: str = "png") -> SizeInBytes:
    with NamedTemporaryFile(mode="w+b") as f:
        image.save(f, format=format)
        size = os.stat(f.name).st_size
    return size


ImageData = str


def image_base64(image: Image, format: str = "png") -> ImageData:
    f = BytesIO()
    image.save(f, format=format)
    return (
        f"data:image/{format};base64,{base64.b64encode(f.getbuffer()).decode('ascii')}"
    )
