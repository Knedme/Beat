from youtubesearchpython.__future__ import VideosSearch
from abc import ABC
from aiohttp import ClientSession
from typing import Union
from asyncio import get_event_loop
from concurrent.futures import ThreadPoolExecutor
from yt_dlp import YoutubeDL
from pytube import Playlist
from ytmusicapi import YTMusic

from bot.misc import SongObject, Config


class YouTube(ABC):

    @staticmethod
    async def is_valid_url(url: str) -> bool:
        """Checks the YouTube video/playlist url for validity."""

        async with ClientSession() as session:
            checker_url = 'https://www.youtube.com/oembed?url=' + url
            async with session.get(checker_url) as resp:
                return resp.status == 200

    @staticmethod
    async def search(query: str) -> Union[str, None]:
        """Searches for video on YouTube."""

        try:
            return (await VideosSearch(query, limit=1).next())['result'][0]['link']
        except IndexError:
            return None

    @staticmethod
    async def search_ytm(query: str) -> Union[str, None]:
        """Searches for video on YouTube Music."""

        try:
            # execution of the function in the ThreadPoolExecutor, so as not to block the event loop
            return (await get_event_loop().run_in_executor(
                ThreadPoolExecutor(), YTMusic().search, query, 'songs'))[0]['videoId']
        except IndexError:
            return None

    @staticmethod
    async def extract_video_info(url: str) -> dict:
        """Extracts all info (including the source audio url) from video."""

        return await get_event_loop().run_in_executor(
            ThreadPoolExecutor(),
            YoutubeDL(Config.YDL_OPTIONS).extract_info, url, False)

    @classmethod
    async def video(cls, url: str) -> SongObject:
        """Extracts the data needed to play the video."""

        video_info = await cls.extract_video_info(url)
        if video_info is None:  # if an error occurs, return an empty SongObject
            return SongObject('youtube_video', None, None, None)
        return SongObject('youtube_video', video_info['fulltitle'], video_info['original_url'], video_info['url'])

    @classmethod
    async def playlist(cls, url: str) -> SongObject:
        """Extracts the data needed to play the first video of the playlist
        and saves the remaining video urls of the playlist."""

        def get_playlist_info() -> tuple:
            playlist = Playlist(url)
            playlist.video_urls.generate_all()
            return playlist.title, playlist.playlist_url, list(playlist.video_urls)

        playlist_name, playlist_url, video_urls =\
            await get_event_loop().run_in_executor(ThreadPoolExecutor(), get_playlist_info)
        first_video = await cls.video(video_urls.pop(0))

        return SongObject('youtube_playlist',
                          first_video.name, first_video.url, first_video.src_url,
                          playlist_name, playlist_url, video_urls)
