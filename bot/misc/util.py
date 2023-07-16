from dataclasses import dataclass
from typing import Union, List, Dict


@dataclass
class SongObject:
    """Stores the data needed to play a song or playlist."""
    type_: str
    name: Union[None, str]
    url: Union[None, str]
    src_url: Union[None, str]
    playlist_name: Union[None, str] = None
    playlist_url: Union[None, str] = None
    playlist_remaining_urls: Union[None, List[str]] = None


@dataclass
class QueueItem:
    name: str
    url: str
    src_url: Union[None, str]


class _PlayData:
    """Stores data for playing songs (queue, current song position, loop state, etc.)"""

    def __init__(self):
        self.queue = []
        self.cur_song_idx = 0
        self.target_song_idx = None
        self.loop = False
        self.loop_queue = False
        self.playlists_being_added = 0
        self.waiting_for_next_song = False


class GuildPlayData:
    """Stores _PlayData for each guild."""

    __guild_play_data: Dict[int, _PlayData] = {}

    @classmethod
    def create_play_data(cls, guild_id: int) -> _PlayData:
        """Creates new empty guild play data."""
        cls.__guild_play_data[guild_id] = _PlayData()
        return cls.__guild_play_data[guild_id]

    @classmethod
    def get_play_data(cls, guild_id: int) -> Union[None, _PlayData]:
        """Gets guild play data."""
        if guild_id not in cls.__guild_play_data:
            return None
        return cls.__guild_play_data[guild_id]

    @classmethod
    def remove_play_data(cls, guild_id: int) -> None:
        """Removes guild play data."""
        if guild_id in cls.__guild_play_data:
            del cls.__guild_play_data[guild_id]
