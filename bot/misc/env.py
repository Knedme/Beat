import os
from abc import ABC
from typing import Final


class Env(ABC):
    TOKEN: Final = os.environ.get('TOKEN', 'Please, define the bot token')
    SPOTIFY_CLIENT_ID: Final = os.environ.get('SPOTIFY_CLIENT_ID', 'Please, define the Spotify client id')
    SPOTIFY_CLIENT_SECRET: Final = os.environ.get('SPOTIFY_CLIENT_SECRET', 'Please, define the Spotify client secret')
