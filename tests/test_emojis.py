import pytest

from de.emojis import (
    EMOJI_HEIGHT,
    EMOJI_MAX_SIZE,
    EMOJI_WIDTH,
    image_base64,
    image_size,
    load_emojis,
)


EMOJIS = load_emojis()


def test_emojis_loaded():
    assert len(EMOJIS), "At least some emojis should have loaded"


@pytest.mark.parametrize("name,emoji", list(EMOJIS.items()))
def test_emojis_well_formed(name, emoji):
    image = emoji.image()
    assert (
        image.width <= EMOJI_WIDTH
    ), f"Emoji {name} should be at most {EMOJI_WIDTH} pixels wide!"
    assert (
        image.height <= EMOJI_HEIGHT
    ), f"Emoji {name} should be at most {EMOJI_HEIGHT} pixels tall!"
    assert (
        image_size(image) <= EMOJI_MAX_SIZE
    ), f"Emoji {name} should be less than {EMOJI_MAX_SIZE} bytes in size!"
    assert "image/png;base64" in image_base64(image), "It should base64 encode!"
