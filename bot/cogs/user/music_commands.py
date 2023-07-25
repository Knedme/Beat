from nextcord import slash_command, Interaction, VoiceChannel, VoiceClient, SlashOption, FFmpegOpusAudio,\
    ClientException, Embed, Member, VoiceState
from nextcord.ext.commands import Cog, Bot
from typing import Union

from bot.misc import Config, YouTubeWrapper, SpotifyWrapper, GuildPlayData, QueueItem


class MusicCommandsCog(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot
        self.guild_play_data = {}

    @classmethod
    def __play_music(cls, vc: VoiceClient, src_url: Union[None, str]) -> None:
        """Plays music from the source url and then calls the __check_new_songs method."""

        if src_url is None:
            cls.__check_new_songs(vc)
            return

        try:
            vc.play(FFmpegOpusAudio(
                src_url,
                executable=Config.FFMPEG_PATH,
                before_options=Config.FFMPEG_OPTIONS['before_options'],
                options=Config.FFMPEG_OPTIONS['options']
                # this will call the __check_new_songs method after playing song
            ), after=lambda _: cls.__check_new_songs(vc))
        except ClientException:  # do nothing if something is already playing
            return

    @classmethod
    def __check_new_songs(cls, vc: VoiceClient) -> None:
        """Plays the remaining songs if there is any and loops the track or queue."""

        if not vc.is_connected():
            return

        play_data = GuildPlayData.get_play_data(vc.guild.id)
        if play_data is None:
            return

        try:
            if play_data.target_song_idx is not None:  # the ability to play a song in a given position
                play_data.cur_song_idx = play_data.target_song_idx
                play_data.target_song_idx = None
                src_url = play_data.queue[play_data.cur_song_idx].src_url
            else:
                if play_data.loop:  # track loop
                    src_url = play_data.queue[play_data.cur_song_idx].src_url
                else:
                    # getting the next song
                    src_url = play_data.queue[play_data.cur_song_idx + 1].src_url
                    play_data.cur_song_idx += 1
        except IndexError:
            # if the index is out of range, it is the end of the queue

            if play_data.playlists_being_added:
                play_data.waiting_for_next_song = True
                return

            if not play_data.loop_queue:
                GuildPlayData.remove_play_data(vc.guild.id)
                return

            # queue loop
            play_data.cur_song_idx = 0
            src_url = play_data.queue[0].src_url

        cls.__play_music(vc, src_url)

    @staticmethod
    async def __join_user_channel(interaction: Interaction) -> Union[VoiceChannel, None]:
        """Joins to the voice channel where the user is located."""

        channel = interaction.user.voice.channel

        permissions = channel.permissions_for(interaction.guild.me)
        if not permissions.connect:
            await interaction.send(
                f'{interaction.user.mention}, I don\'t have permission to connect to your voice channel.')
            return
        if not permissions.speak:
            await interaction.send(
                f'{interaction.user.mention}, I don\'t have permission to speak in your voice channel.')
            return

        if interaction.guild.voice_client is None:
            await channel.connect()
        else:
            await interaction.guild.voice_client.move_to(channel)

        await interaction.guild.change_voice_state(channel=channel, self_mute=False, self_deaf=True)  # self deaf
        return channel

    @Cog.listener()
    async def on_voice_state_update(self, member: Member, _, after: VoiceState) -> None:
        """Deletes play data when the bot has disconnected from the voice channel."""

        if member.id == self.bot.application_id and after.channel is None\
                and GuildPlayData.get_play_data(member.guild.id) is not None:
            GuildPlayData.remove_play_data(member.guild.id)

    @slash_command(name='join', description='The bot joins to your voice channel.', dm_permission=False)
    async def join_command(self, interaction: Interaction) -> None:
        if interaction.user.voice is None:
            await interaction.send(f'{interaction.user.mention}, you have to be connected to a voice channel.')
            return

        channel = await self.__join_user_channel(interaction)
        if channel is None:
            return

        await interaction.send(f'✅ Successfully joined to `{channel}`')

    @slash_command(
        name='play',
        description='The bot joins to your voice channel and plays music from a known link or a search query.',
        dm_permission=False)
    async def play_command(self, interaction: Interaction,
                           query: str = SlashOption(description='Known link or a search query', required=True)) -> None:
        await interaction.response.defer()

        if interaction.user.voice is None:
            await interaction.send(f'{interaction.user.mention}, you have to be connected to a voice channel.')
            return

        channel = await self.__join_user_channel(interaction)
        if channel is None:
            return

        song_obj, original_url = None, None
        if 'open.spotify.com' not in query.lower():
            if 'youtube.com' in query.lower() or 'youtu.be' in query.lower():
                for el in query.split():  # getting an url from the query
                    if 'youtube.com' in el.lower() or 'youtu.be' in el.lower():
                        original_url = el
                        if not await YouTubeWrapper.is_valid_url(original_url):  # YouTube url validation
                            await interaction.send('Unknown YouTube url.')
                            return
                        break
            else:
                original_url = await YouTubeWrapper.search(query)
                if original_url is None:
                    await interaction.send('No results found for your search query.')
                    return

            if 'list=' not in original_url:  # check if the link leads to a playlist
                song_obj = await YouTubeWrapper.video(original_url)
                if song_obj.src_url is None:  # error handling
                    await interaction.send('An error occurred while processing YouTube video.')
                    return
            else:
                song_obj = await YouTubeWrapper.playlist(original_url)
                if song_obj.src_url is None:
                    await interaction.channel.send(
                        'An error occurred while processing the first video in the playlist.')
        else:
            for el in query.split():
                if 'open.spotify.com' in el.lower():
                    original_url = el
                    break

            if 'track' in original_url:
                song_obj = await SpotifyWrapper.track(original_url)
                if song_obj.name is not None and song_obj.src_url is None:
                    await interaction.send(
                        'An error occurred while processing the Spotify track or this track wasn\'t found.')
                    return
            elif 'album' in original_url:
                song_obj = await SpotifyWrapper.album(original_url)
                if song_obj.name is not None and song_obj.src_url is None:
                    await interaction.channel.send(
                        'An error occurred while processing the first track of the Spotify album or'
                        ' this track wasn\'t found.')
            elif 'playlist' in original_url:
                song_obj = await SpotifyWrapper.playlist(original_url)
                if song_obj.name is not None:
                    if song_obj.playlist_remaining_urls is None:
                        await interaction.send('There is no tracks in this Spotify playlist.')
                        return
                    if song_obj.src_url is None:
                        await interaction.channel.send(
                            'An error occurred while processing the first track of the Spotify playlist or'
                            ' this track wasn\'t found.')

            if song_obj is None or song_obj.name is None:
                await interaction.send('Unknown Spotify url.')
                return

        # if the bot has been disconnected by this moment, stop the command execution
        vc = interaction.guild.voice_client
        if vc is None:
            await interaction.send('The bot was disconnected from the voice channel.')
            return

        # adding song to queue
        play_data = GuildPlayData.get_play_data(interaction.guild_id)
        if play_data is None:
            play_data = GuildPlayData.create_play_data(interaction.guild_id)
        play_data.queue.append(QueueItem(song_obj.name, song_obj.url, song_obj.src_url))
        if 'playlist' in song_obj.type_:
            play_data.playlists_being_added += 1

        if not vc.is_paused():
            self.__play_music(vc, song_obj.src_url)

        display_name = song_obj.name
        display_url = song_obj.url
        if 'playlist' in song_obj.type_:
            display_name = song_obj.playlist_name
            display_url = song_obj.playlist_url

        # sending embed, depending on queue
        if len(GuildPlayData.get_play_data(interaction.guild_id).queue) > 1:
            await interaction.send(embed=Embed(
                title='Queue',
                description=f'🔎 Searching for `{query}`\n\n' +
                            f'✅ [{display_name}]({display_url}) - successfully added to queue.',
                color=Config.EMBED_COLOR))
        else:
            await interaction.send(embed=Embed(
                title='Now playing',
                description=f'✅ Successfully joined to `{channel}`\n\n' +
                            f'🔎 Searching for `{query}`\n\n' +
                            f'▶️ Now playing - [{display_name}]({display_url})',
                color=Config.EMBED_COLOR))

        # adding the remaining videos from the YouTube playlist to queue
        if song_obj.type_ == 'youtube_playlist':
            for video_url in song_obj.playlist_remaining_urls:
                video = await YouTubeWrapper.video(video_url)
                if video.src_url is None:
                    await interaction.channel.send(
                        'An error occurred while processing one of the playlist videos.')
                    continue

                play_data = GuildPlayData.get_play_data(interaction.guild_id)
                if play_data is None:
                    return

                play_data.queue.append(QueueItem(video.name, video.url, video.src_url))
                if play_data.waiting_for_next_song:  # if the bot is waiting for next song, playing it
                    play_data.waiting_for_next_song = False
                    play_data.cur_song_idx += 1
                    self.__play_music(vc, video.src_url)

            play_data.playlists_being_added -= 1
            await interaction.channel.send('✅ YouTube playlist was fully added to the queue.')

        # adding the remaining videos from the Spotify album/playlist to queue
        elif song_obj.type_ == 'spotify_playlist':
            for track_url in song_obj.playlist_remaining_urls:
                track = await SpotifyWrapper.track(track_url)
                if track.src_url is None:
                    await interaction.channel.send(
                        'An error occurred while processing one of the Spotify album/playlist tracks or'
                        ' this track wasn\'t found.')
                    continue

                play_data = GuildPlayData.get_play_data(interaction.guild_id)
                if play_data is None:
                    return

                play_data.queue.append(QueueItem(track.name, track.url, track.src_url))
                if play_data.waiting_for_next_song:
                    play_data.waiting_for_next_song = False
                    play_data.cur_song_idx += 1
                    self.__play_music(vc, track.src_url)

            play_data.playlists_being_added -= 1
            await interaction.channel.send('✅ Spotify album/playlist was fully added to the queue.')

    @slash_command(name='lofi', description='Joins to the channel and plays lofi hip hop.', dm_permission=False)
    async def lofi_command(self, interaction: Interaction) -> None:
        # just calling play_command method with 'lofi hip hop radio' query
        await self.play_command(interaction, 'lofi hip hop radio')
