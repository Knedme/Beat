from abc import ABC
from typing import Final


class Config(ABC):
    FFMPEG_PATH: Final = 'Define the ffmpeg path here'
    COOKIES_FILE_PATH: Final = 'Define the cookies file path here'

    BOT_VERSION: Final = '1.3'
    EMBED_COLOR: Final = 0x515596  # colour of the embeds
    FFMPEG_OPTIONS: Final = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }
