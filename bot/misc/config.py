from abc import ABC
from typing import Final


class Config(ABC):
    FFMPEG_PATH: Final = r'Define the ffmpeg path here'
    COOKIES_FILE_PATH: Final = r'Define the cookies file path here'

    BOT_NAME: Final = 'Beat'
    BOT_VERSION: Final = '1.3.6'
    BOT_LOGO_URL: Final = 'https://raw.githubusercontent.com/Knedme/Beat/master/logo/1x.png'
    EMBED_COLOR: Final = 0x515596  # colour of the embeds

    YDL_OPTIONS: Final = {
        'format': 'bestaudio/best',
        'ignoreerrors': True,  # do not stop on errors
        'quiet': True,  # disables info logging
        'cookiefile': COOKIES_FILE_PATH,
    }
    FFMPEG_OPTIONS: Final = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }
