from abc import ABC
from typing import Final


class Config(ABC):
    FFMPEG_PATH: Final = r'Define the ffmpeg path here'
    COOKIES_FILE_PATH: Final = r'Define the cookies file path here'
    FFMPEG_OPTIONS: Final = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }

    BOT_NAME: Final = 'Beat'
    BOT_VERSION: Final = '1.3.1'
    BOT_LOGO_URL: Final = 'https://raw.githubusercontent.com/Knedme/Beat/master/logo/1x.png'
    EMBED_COLOR: Final = 0x515596  # colour of the embeds

