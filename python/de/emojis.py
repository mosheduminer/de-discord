from dataclasses import dataclass, field
from functools import lru_cache
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, IO

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
        return Image.open(str(self.path)).resize(size=EMOJI_SIZE)


EmojiMapping = Dict[EmojiName, Emoji]


def load_emojis() -> EmojiMapping:
    return {
        emoji.name: emoji
        for emoji in (Emoji.from_listing(lx) for lx in os.listdir(EMOJIS_DIR))
    }


def png_file(image: Image) -> IO[bytes]:
    f = NamedTemporaryFile(mode="w+b")
    image.save(f, format="png")
    f.seek(0)
    return f


SizeInBytes = int

KILOBYTES = 1024
EMOJI_MAX_SIZE: SizeInBytes = 256 * KILOBYTES


def png_size(f: IO[bytes]) -> SizeInBytes:
    return os.stat(f.name).st_size
