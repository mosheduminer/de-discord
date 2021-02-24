import pytest

from de.emojis import (
    EMOJI_HEIGHT,
    EMOJI_MAX_SIZE,
    EMOJI_WIDTH,
    load_emojis,
    png_file,
    png_size,
)


EMOJIS = load_emojis()


def test_emojis_loaded():
    assert len(EMOJIS), "At least some emojis should have loaded"


@pytest.mark.parametrize("name,emoji", [(n, e) for n, e in EMOJIS.items()])
def test_emojis_well_formed(name, emoji):
    image = emoji.image()
    assert (
        image.width == EMOJI_WIDTH
    ), f"Emoji {name} should be {EMOJI_WIDTH} pixels wide!"
    assert (
        image.height == EMOJI_HEIGHT
    ), f"Emoji {name} should be {EMOJI_HEIGHT} pixels tall!"
    with png_file(image) as png:
        assert (
            png_size(png) <= EMOJI_MAX_SIZE
        ), f"Emoji {name} should be less than {EMOJI_MAX_SIZE} bytes in size!"
