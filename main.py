# Main file

# Beat discord music bot v1.2.4
# by Knedme

# TODO: brand new bot structure in v1.3

from youtubesearchpython.__future__ import VideosSearch
import discord
import yt_dlp
import asyncio
import aiohttp
import random
from pytube import Playlist
from async_spotify import SpotifyApiClient
from async_spotify.authentification.authorization_flows import ClientCredentialsFlow
from async_spotify.spotify_errors import SpotifyBaseError
from ytmusicapi import YTMusic
from concurrent.futures import ThreadPoolExecutor
from config import *

bot = discord.Bot()
spotify_client = SpotifyApiClient(authorization_flow=ClientCredentialsFlow(
    application_id=SPOTIFY_CLIENT_ID, application_secret=SPOTIFY_CLIENT_SECRET))
ytm_client = YTMusic()

loops = {}  # stores the loop state for each server
queue_info = {}  # stores queue info (the queue itself, song position, etc.) for each server


# this function extracts all info (including the source audio url) from YouTube video url
def extract_yt_info(yt_url):
    return yt_dlp.YoutubeDL(
        {'format': 'bestaudio/best', 'cookiefile': COOKIES_FILE_PATH}).extract_info(yt_url, download=False)


# this function gets full name (including the artists) of the Spotify track
def get_sp_track_full_name(sp_track_artist_list, sp_track_name):
    artist_names = sp_track_artist_list[0]['name']
    for i in range(len(sp_track_artist_list) - 1):
        artist_names += ', ' + sp_track_artist_list[i + 1]['name']
    return artist_names + ' - ' + sp_track_name


# this function founds the YouTube url of the specified full name of the Spotify track
async def get_sp_track_yt_url(sp_track_full_name):
    try:
        event_loop = asyncio.get_event_loop()
        # running a function in ThreadPoolExecutor so as not to block the asyncio event loop
        yt_url = 'https://www.youtube.com/watch?v='\
                 + (await event_loop.run_in_executor(ThreadPoolExecutor(),
                                                     ytm_client.search,
                                                     sp_track_full_name,
                                                     'songs'))[0]['videoId']
    except IndexError:  # if track wasn't found on YouTube Music searching for it on YouTube
        search_obj = VideosSearch(sp_track_full_name, limit=1)
        try:
            yt_url = (await search_obj.next())['result'][0]['link']
        except IndexError:
            yt_url = None  # if track even not found on YouTube, just assigning None
    return yt_url


# this function is called when a song has been played, it plays remaining songs and loops tracks/queue
def check_new_songs(vc, guild_id):
    global queue_info, loops

    # if the bot has been disconnected from a voice channel, clearing variables
    if not vc.is_connected():
        if guild_id in queue_info:
            del queue_info[guild_id]
        if guild_id in loops:
            del loops[guild_id]
        return

    if guild_id not in queue_info:
        return

    # track loop
    if guild_id in loops and loops[guild_id] == 'track':
        src_url = queue_info[guild_id]['queue'][queue_info[guild_id]['queue_pos']]['src_url']
        play_music(vc, src_url, guild_id)
        return

    try:  # trying to get the next song
        src_url = queue_info[guild_id]['queue'][queue_info[guild_id]['queue_pos'] + 1]['src_url']
        queue_info[guild_id]['queue_pos'] += 1
    except IndexError:
        # if next songs are being added to queue now, then waiting for the next song
        if queue_info[guild_id]['adding_songs_to_queue']:
            queue_info[guild_id]['waiting_for_next_song'] = True
            return

        # if there is no queue loop, then clearing the variables and exiting the function
        if guild_id not in loops or loops[guild_id] != 'queue':
            del queue_info[guild_id]
            if guild_id in loops:
                del loops[guild_id]
            return

        # queue loop
        queue_info[guild_id]['queue_pos'] = 0
        src_url = queue_info[guild_id]['queue'][0]['src_url']

    play_music(vc, src_url, guild_id)


# this function plays music from source url and then calling check_new_songs function
def play_music(vc, src_url, guild_id):
    if src_url is None:  # if url is None, just calling check_new_songs function
        check_new_songs(vc, guild_id)
    else:
        try:
            vc.play(discord.FFmpegPCMAudio(
                src_url,
                executable=FFMPEG_PATH,
                before_options=FFMPEG_OPTIONS['before_options'],
                options=FFMPEG_OPTIONS['options']
                # this will call the check_new_songs function after playing the current song
            ), after=lambda _: check_new_songs(vc, guild_id))
        except discord.ClientException:  # do nothing if song is already playing
            pass


@bot.event
async def on_ready():
    # opening Spotify client
    await spotify_client.get_auth_token_with_client_credentials()
    await spotify_client.create_new_client()

    print('🎵 Beat v1.2.4 launched!')

    # bot status
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(type=discord.ActivityType.listening, name='/commands | /info'))


@bot.slash_command(name='commands', description='Shows a list of commands.')
async def commands(ctx):
    embed = discord.Embed(
        title='Beat Commands',
        color=BOT_COLOR)
    embed.add_field(name='/join', value='Bot joins to your voice channel.', inline=False)
    embed.add_field(
        name='/play youtube-video-link | spotify-link | search-query',
        value='Bot joins to your voice channel and plays music from a link or search query.',
        inline=False)
    embed.add_field(name='/lofi', value='Bot joins to your channel and plays lofi.', inline=False)
    embed.add_field(name='/leave', value='Leave the voice channel.', inline=False)
    embed.add_field(name='/skip', value='Skips current track.', inline=False)
    embed.add_field(name='/pause', value='Pause music.', inline=False)
    embed.add_field(name='/resume', value='Resume music.', inline=False)
    embed.add_field(name='/queue', value='Shows current queue.', inline=False)
    embed.add_field(name='/loop', value='Loops current track.', inline=False)
    embed.add_field(name='/shuffle', value='Shuffles next songs in the queue.', inline=False)
    embed.add_field(name='/support', value='Shows support contact.', inline=False)
    embed.add_field(name='/commands', value='Shows a list of commands.', inline=False)
    embed.add_field(name='/info', value='Information about the bot.')
    embed.set_footer(text='v1.2.4')

    await ctx.respond(embed=embed)


@bot.slash_command(name='info', description='Information about the bot.')
async def info(ctx):
    embed = discord.Embed(title='Information about Beat', color=BOT_COLOR)
    embed.add_field(name='Server count:', value=f'🔺 `{len(bot.guilds)}`', inline=False)
    embed.add_field(name='Bot version:', value=f'✨ `1.2.4`', inline=False)
    embed.add_field(name='The bot is written on:', value=f'🐍 `Pycord`', inline=False)
    embed.add_field(name='Bot created by:', value='🔶 `Knedme`', inline=False)
    embed.add_field(name='GitHub repository:', value='📕 [Click Here](https://github.com/Knedme/Beat)')
    embed.set_thumbnail(url='https://i.imgur.com/pSMdJGW.png')
    embed.set_footer(text='v1.2.4 | Write /commands for the command list.')

    await ctx.respond(embed=embed)


@bot.slash_command(name='support', description='Shows support contact.')
async def support(ctx):
    await ctx.respond(embed=discord.Embed(
        title='Support',
        description='If you have any problems, please write here: `Knedme@yandex.com`',
        color=BOT_COLOR))


@bot.slash_command(name='join', description='Bot joins to your voice channel.')
async def join(ctx):
    if ctx.author.voice is None:
        return await ctx.respond(f'{ctx.author.mention}, You have to be connected to a voice channel.')

    channel = ctx.author.voice.channel

    if ctx.voice_client is None:  # if bot is not connected to a voice channel, connecting to it
        await channel.connect()
    else:  # else, just moving to voice channel where the message author
        await ctx.voice_client.move_to(channel)

    await ctx.guild.change_voice_state(channel=channel, self_mute=False, self_deaf=True)  # self deaf
    await ctx.respond(f'✅ Successfully joined to `{channel}`')


@bot.slash_command(
    name='play',
    description='Bot joins to your voice channel and plays music from a link or search query.')
async def play(ctx, query: discord.Option(str, 'Link or search query.')):
    global queue_info, loops

    await ctx.response.defer()

    if ctx.author.voice is None:
        return await ctx.respond(f'{ctx.author.mention}, You have to be connected to a voice channel.')

    channel = ctx.author.voice.channel

    if ctx.voice_client is None:  # if bot is not connected to a voice channel, connecting to it
        await channel.connect()
    else:  # else, just moving to voice channel where the message author
        await ctx.voice_client.move_to(channel)

    await ctx.guild.change_voice_state(channel=channel, self_mute=False, self_deaf=True)  # self deaf

    src_query = query  # saving source query (for correct display in the embed)
    url = ''
    spotify_link_info = None

    if 'youtube.com/' in query or 'youtu.be/' in query:
        for el in query.split():
            if 'youtube.com/' in el or 'youtu.be/' in el:
                url = el

                # YouTube url validation
                async with aiohttp.ClientSession() as session:
                    checker_url = 'https://www.youtube.com/oembed?url=' + url
                    async with session.get(checker_url) as resp:
                        if resp.status != 200:
                            return await ctx.respond('Unknown YouTube url.')

                break

    elif 'open.spotify.com/' in query:
        for el in query.split():
            if 'open.spotify.com/' in el:
                query = el
                break

        _type = list(filter(None, query.split('/')))[-2]
        _id = list(filter(None, query.split('/')))[-1].split('?')[0]

        # Spotify url validation
        try:
            if _type == 'track':
                spotify_link_info = await spotify_client.track.get_one(_id)
            elif _type == 'album':
                spotify_link_info = await spotify_client.albums.get_one(_id)
            elif _type == 'playlist':
                spotify_link_info = await spotify_client.playlists.get_one(_id)
            else:
                raise TypeError
        except SpotifyBaseError and TypeError:
            return await ctx.respond(
                f'Unknown Spotify url. Make sure you entered the link correctly and that your link leads to opened ' +
                'Spotify track/album/playlist.')

        if spotify_link_info['type'] == 'track':
            # if it's single Spotify track, getting his YouTube url and playing as usual
            spotify_link_info['full_name'] =\
                get_sp_track_full_name(spotify_link_info['artists'], spotify_link_info['name'])
            spotify_link_info['yt_url'] = await get_sp_track_yt_url(spotify_link_info['full_name'])
            if spotify_link_info['yt_url'] is None:  # error handling
                return await ctx.respond(f'Your song was not found. Try another one.')
            url = spotify_link_info['yt_url']

        else:
            # if it's Spotify playlist or album, getting all of its songs and the YouTube url of first song

            next_link = spotify_link_info['tracks']['next']
            while next_link:
                next_tracks = await spotify_client.next(next_link)
                spotify_link_info['tracks']['items'] += next_tracks['items']
                next_link = next_tracks['next']

            # if it is a Spotify playlist, removing all episodes from it and moving item['track'] to item
            if spotify_link_info['type'] == 'playlist':
                episode_indexes = []

                for i in range(len(spotify_link_info['tracks']['items'])):
                    if not spotify_link_info['tracks']['items'][i]['track']:
                        episode_indexes.append(i)
                    else:
                        spotify_link_info['tracks']['items'][i].update(spotify_link_info['tracks']['items'][i]['track'])
                        del spotify_link_info['tracks']['items'][i]['track']

                episode_indexes.reverse()
                for episode_index in episode_indexes:
                    spotify_link_info['tracks']['items'].pop(episode_index)

            if len(spotify_link_info['tracks']['items']) == 0:  # if there are no tracks, sending an error message
                return await ctx.respond('There is no tracks in your Spotify playlist/album.')

            # getting YouTube url of the first track
            spotify_link_info['tracks']['items'][0]['full_name'] =\
                get_sp_track_full_name(spotify_link_info['tracks']['items'][0]['artists'],
                                       spotify_link_info['tracks']['items'][0]['name'])
            spotify_link_info['tracks']['items'][0]['yt_url'] =\
                await get_sp_track_yt_url(spotify_link_info['tracks']['items'][0]['full_name'])
            if spotify_link_info['tracks']['items'][0]['yt_url'] is None:
                await ctx.send(f'One of the songs in the album/playlist was not found, so this song will not play.')

    # if there are no more known urls in the queue, searching for videos on YouTube for this queue
    else:
        search_obj = VideosSearch(query, limit=1)
        try:
            url = (await search_obj.next())['result'][0]['link']
        except IndexError:
            # if video not found, sending an error message
            return await ctx.respond(f'Video titled \'{search_obj.data["query"]}\' not found. Try another video title.')

    # if it's YouTube video or Spotify track, extracting its source url and playing song as usual
    if (spotify_link_info is None or spotify_link_info['type'] == 'track') and 'list=' not in url:
        event_loop = asyncio.get_event_loop()
        information = await event_loop.run_in_executor(ThreadPoolExecutor(), extract_yt_info, url)
        src_url = information['url']
        title = information['title']

        if spotify_link_info is not None:  # changing title and link if it is Spotify track
            title = spotify_link_info['full_name']
            url = spotify_link_info['external_urls']['spotify']

        # adding song to queue
        if ctx.guild.id in queue_info:
            queue_info[ctx.guild.id]['queue'].append({'name': title, 'url': url, 'src_url': src_url})
        else:
            queue_info[ctx.guild.id] = {
                'queue': [{'name': title, 'url': url, 'src_url': src_url}],
                'queue_pos': 0,
                'adding_songs_to_queue': False,
                'waiting_for_next_song': False
            }

    # if it's Spotify playlist or album, adding to queue its first track
    # and extracting track's source url (if YouTube url of the track was found)
    elif spotify_link_info is not None\
            and (spotify_link_info['type'] == 'album' or spotify_link_info['type'] == 'playlist'):
        first_track_info = spotify_link_info['tracks']['items'][0]
        title = spotify_link_info['name']
        url = spotify_link_info['external_urls']['spotify']

        if first_track_info['yt_url'] is not None:
            event_loop = asyncio.get_event_loop()
            information =\
                await event_loop.run_in_executor(ThreadPoolExecutor(), extract_yt_info, first_track_info['yt_url'])
            src_url = information['url']
        else:
            src_url = None

        # adding song to queue
        if ctx.guild.id in queue_info:
            queue_info[ctx.guild.id]['queue'].append(
                {'name': first_track_info['full_name'],
                 'url': first_track_info['external_urls']['spotify'], 'src_url': src_url})
            queue_info[ctx.guild.id]['adding_songs_to_queue'] = True  #
        else:
            queue_info[ctx.guild.id] = {
                'queue': [{'name': first_track_info['full_name'],
                           'url': first_track_info['external_urls']['spotify'], 'src_url': src_url}],
                'queue_pos': 0,
                'adding_songs_to_queue': True,
                'waiting_for_next_song': False
            }

    # if it's YouTube playlist, adding to queue its first video and extracting source url of this video
    else:
        playlist = Playlist(url)
        event_loop = asyncio.get_event_loop()
        information = await event_loop.run_in_executor(ThreadPoolExecutor(), extract_yt_info, playlist.video_urls[0])
        src_url = information['url']
        title = playlist.title

        # adding to queue first song
        if ctx.guild.id in queue_info:
            queue_info[ctx.guild.id]['queue'].append(
                {'name': information['title'], 'url': playlist.video_urls[0], 'src_url': src_url})
            queue_info[ctx.guild.id]['adding_songs_to_queue'] = True
        else:
            queue_info[ctx.guild.id] = {
                'queue': [{'name': information['title'], 'url': playlist.video_urls[0], 'src_url': src_url}],
                'queue_pos': 0,
                'adding_songs_to_queue': True,
                'waiting_for_next_song': False
            }

    vc = ctx.voice_client

    play_music(vc, src_url, ctx.guild.id)

    # creating embed, depending on the queue
    if len(queue_info[ctx.guild.id]['queue']) != 1:
        embed = discord.Embed(
            title='Queue',
            description=f'🔎 Searching for `{src_query}`\n\n' +
                        f'✅ [{title}]({url}) - successfully added to queue.',
            color=BOT_COLOR)
    else:
        embed = discord.Embed(
            title='Now playing',
            description=f'✅ Successfully joined to `{channel}`\n\n' +
                        f'🔎 Searching for `{src_query}`\n\n' +
                        f'▶️ Now playing - [{title}]({url})',
            color=BOT_COLOR)

    await ctx.respond(embed=embed)

    # adding to queue remaining tracks of Spotify playlist or album
    if spotify_link_info is not None\
            and (spotify_link_info['type'] == 'album' or spotify_link_info['type'] == 'playlist'):
        for i in range(len(spotify_link_info['tracks']['items'])):
            if i == 0:  # ignoring first track because it's already added to queue
                continue

            # if message author guild was removed from queue_info, stop adding the remaining tracks to the queue
            if ctx.guild.id not in queue_info:
                return

            track = spotify_link_info['tracks']['items'][i]

            # getting YouTube url of the track
            track['full_name'] = get_sp_track_full_name(track['artists'], track['name'])
            track['yt_url'] = await get_sp_track_yt_url(track['full_name'])
            if track['yt_url'] is None:
                await ctx.send(f'One of the songs in the album/playlist was not found, so this song will not play.')
                continue

            event_loop = asyncio.get_event_loop()
            track_yt_information =\
                await event_loop.run_in_executor(ThreadPoolExecutor(), extract_yt_info, track['yt_url'])
            src_track_url = track_yt_information['url']

            if ctx.guild.id in queue_info:
                queue_info[ctx.guild.id]['queue'].append(
                    {'name': track['full_name'], 'url': track['external_urls']['spotify'], 'src_url': src_track_url})

                # if the previous track already been played, then playing current one
                if queue_info[ctx.guild.id]['waiting_for_next_song']:
                    queue_info[ctx.guild.id]['waiting_for_next_song'] = False
                    queue_info[ctx.guild.id]['queue_pos'] += 1
                    play_music(vc, src_track_url, ctx.guild.id)

        queue_info[ctx.guild.id]['adding_songs_to_queue'] = False

        # if all tracks weren't found, sending error message
        if len(spotify_link_info['tracks']['items']) == 0:
            return await ctx.respond('All tracks from your album/playlist weren\'t found.')

        await ctx.send('✅ Spotify playlist/album was fully added to the queue.')

    # adding to queue remaining tracks of YouTube playlist
    elif 'list=' in url:
        playlist = Playlist(url)

        for i in range(len(playlist.video_urls)):
            if i == 0:  # ignoring first video because it's already added to queue
                continue

            # if message author guild was removed from queue_info, stop adding the remaining tracks to the queue
            if ctx.guild.id not in queue_info:
                return

            event_loop = asyncio.get_event_loop()
            information = await event_loop.run_in_executor(ThreadPoolExecutor(), extract_yt_info,
                                                           playlist.video_urls[i])
            src_video_url = information['url']

            if ctx.guild.id in queue_info:
                queue_info[ctx.guild.id]['queue'].append(
                    {'name': information['title'], 'url': playlist.video_urls[i], 'src_url': src_video_url})

                # if the previous video have already been played, then playing current one
                if queue_info[ctx.guild.id]['waiting_for_next_song']:
                    queue_info[ctx.guild.id]['waiting_for_next_song'] = False
                    queue_info[ctx.guild.id]['queue_pos'] += 1
                    play_music(vc, src_video_url, ctx.guild.id)

        queue_info[ctx.guild.id]['adding_songs_to_queue'] = False
        await ctx.send('✅ YouTube playlist was fully added to the queue.')


@bot.slash_command(name='lofi', description='Joins to the channel and plays lofi hip hop.')
async def lofi(ctx):
    # just invoking play command with 'lofi hip hop' query
    await ctx.invoke(bot.get_command('play'), query='lofi hip hop')


@bot.slash_command(name='skip', description='Skips current song.')
async def skip(ctx):
    if ctx.voice_client is None:
        return await ctx.respond('I am not playing any songs for you.')

    if ctx.author.voice is None:
        return await ctx.respond(f'{ctx.author.mention}, You have to be connected to a voice channel.')

    if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
        return await ctx.respond('You are in the wrong channel.')

    ctx.voice_client.stop()  # skipping current track using stop function
    await ctx.respond('✅ Successfully skipped.')


@bot.slash_command(name='leave', description='Leaves the voice channel.')
async def leave(ctx):
    if ctx.voice_client is None:
        return await ctx.respond('I am not playing any songs for you.')

    if ctx.author.voice is None:
        return await ctx.respond(f'{ctx.author.mention}, You have to be connected to a voice channel.')

    if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
        return await ctx.respond('You are in the wrong channel.')

    # clearing variables
    if ctx.guild.id in queue_info:
        del queue_info[ctx.guild.id]
    if ctx.guild.id in loops:
        del loops[ctx.guild.id]

    await ctx.voice_client.disconnect()  # leaving a voice channel
    await ctx.respond('✅ Successfully disconnected.')


@bot.slash_command(name='pause', description='Pauses current song.')
async def pause(ctx):
    if ctx.voice_client is None:
        return await ctx.respond('I am not playing any songs for you.')

    if ctx.author.voice is None:
        return await ctx.respond(f'{ctx.author.mention}, You have to be connected to a voice channel.')

    if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
        return await ctx.respond('You are in the wrong channel.')

    ctx.voice_client.pause()  # stopping a music using pause command
    await ctx.respond('⏸️ Successfully paused.')


@bot.slash_command(name='resume', description='Resumes current song if it is paused.')
async def resume(ctx):
    if ctx.voice_client is None:
        return await ctx.respond('I am not playing any songs for you.')

    if ctx.author.voice is None:
        return await ctx.respond(f'{ctx.author.mention}, You have to be connected to a voice channel.')

    if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
        return await ctx.respond('You are in the wrong channel.')

    ctx.voice_client.resume()  # resuming music
    await ctx.respond('▶️ Successfully resumed.')


@bot.slash_command(name='queue', description='Shows current queue of songs.')
async def queue(ctx):
    if ctx.guild.id in queue_info and queue_info[ctx.guild.id]:
        # splitting the queue into arrays of 15 songs
        divided_queue = queue_info[ctx.guild.id]['queue']
        arrays = []
        while len(divided_queue) > 15:
            piece = divided_queue[:15]
            arrays.append(piece)
            divided_queue = divided_queue[15:]
        arrays.append(divided_queue)
        divided_queue = arrays
    else:  # if queue is empty, sending empty embed
        return await ctx.respond(embed=discord.Embed(
            title='Current Queue',
            description='Your current queue is empty!',
            color=BOT_COLOR))

    pages = []
    for _ in divided_queue:
        pages.append('')
    position = 0
    page = 0

    # filling each page with song titles, their positions in queue, etc.
    for i in divided_queue:
        for j in i:
            # if the song name has more than 100 characters, shortening it
            name = j['name']
            if len(name) > 100:
                name = name[:97] + '...'

            if position == queue_info[ctx.guild.id]['queue_pos']:
                pages[page] += f'{position + 1}. [{name}]({j["url"]}) ⟵ current track\n'  # displaying the current song
            else:
                pages[page] += f'{position + 1}. [{name}]({j["url"]})\n'
            position += 1
        if page < len(divided_queue) - 1:
            page += 1

    additional_info = f'🎶 Total tracks: {len(queue_info[ctx.guild.id]["queue"])}'

    if ctx.guild.id not in loops:
        additional_info += '\n🔁 Queue loop: disabled | 🔁 Current track loop: disabled'
    elif loops[ctx.guild.id] == 'queue':
        additional_info += '\n🔁 Queue loop: enabled | 🔁 Current track loop: disabled'
    else:
        additional_info += '\n🔁 Queue loop: disabled | 🔁 Current track loop: enabled'

    # queue page flipping buttons

    page = 0
    previous_page_btn = discord.ui.Button(label='Previous page', style=discord.ButtonStyle.primary, emoji='⬅')
    next_page_btn = discord.ui.Button(label='Next page', style=discord.ButtonStyle.primary, emoji='➡')
    first_page_btn = discord.ui.Button(label='First page', style=discord.ButtonStyle.primary, emoji='⏪')
    last_page_btn = discord.ui.Button(label='Last page', style=discord.ButtonStyle.primary, emoji='⏩')

    view = discord.ui.View()
    view.add_item(previous_page_btn)
    view.add_item(next_page_btn)
    view.add_item(first_page_btn)
    view.add_item(last_page_btn)

    async def update_msg(interaction_message):
        await interaction_message.edit(
            embed=discord.Embed(title='Current Queue', description=pages[page], color=BOT_COLOR)
            .set_footer(text=f'📄 Page {page + 1}/{len(pages)} | ' + additional_info))

    async def previous_page_btn_callback(interaction):
        nonlocal page
        if page > 0:
            page -= 1
        await update_msg(interaction.message)
        await interaction.response.defer()

    async def next_page_btn_callback(interaction):
        nonlocal page
        if page < len(pages) - 1:
            page += 1
        await update_msg(interaction.message)
        await interaction.response.defer()

    async def first_page_btn_callback(interaction):
        nonlocal page
        page = 0
        await update_msg(interaction.message)
        await interaction.response.defer()

    async def last_page_btn_callback(interaction):
        nonlocal page
        page = len(pages) - 1
        await update_msg(interaction.message)
        await interaction.response.defer()

    previous_page_btn.callback = previous_page_btn_callback
    next_page_btn.callback = next_page_btn_callback
    first_page_btn.callback = first_page_btn_callback
    last_page_btn.callback = last_page_btn_callback

    # sending a message starting from the first page of the queue
    await ctx.respond(embed=discord.Embed(title='Current Queue', description=pages[page], color=BOT_COLOR)
                      .set_footer(text=f'📄 Page {page+1}/{len(pages)} | ' + additional_info), view=view)


@bot.slash_command(name='loop', description='Enables/Disables Queue/Track loop.')
async def loop(ctx):
    global loops

    if ctx.voice_client is None:
        return await ctx.respond('I am not playing any songs for you.')

    if ctx.author.voice is None:
        return await ctx.respond(f'{ctx.author.mention}, You have to be connected to a voice channel.')

    if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
        return await ctx.respond('You are in the wrong channel.')

    if ctx.guild.id not in loops:
        loops[ctx.guild.id] = 'queue'
        await ctx.respond('🔁 Queue loop enabled!')
    elif loops[ctx.guild.id] == 'queue':
        loops[ctx.guild.id] = 'track'
        await ctx.respond('🔁 Current track loop enabled!')
    else:
        del loops[ctx.guild.id]
        await ctx.respond('❎ Loop disabled!')


@bot.slash_command(name='shuffle', description='Shuffles next songs in the queue.')
async def shuffle(ctx):
    global queue_info

    if ctx.voice_client is None:
        return await ctx.respond('I am not playing any songs for you.')

    if ctx.author.voice is None:
        return await ctx.respond(f'{ctx.author.mention}, You have to be connected to a voice channel.')

    if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
        return await ctx.respond('You are in the wrong channel.')

    if ctx.guild.id not in queue_info or len(queue_info[ctx.guild.id]['queue']) == 0:
        return await ctx.respond('Your queue is empty!')

    # getting the next and previous songs from the queue
    next_songs = queue_info[ctx.guild.id]['queue'][queue_info[ctx.guild.id]['queue_pos'] + 1:]
    previous_songs = queue_info[ctx.guild.id]['queue'][:queue_info[ctx.guild.id]['queue_pos'] + 1]

    if len(next_songs) <= 1:
        return await ctx.respond('Not enough songs to shuffle.')

    # unique shuffling next songs
    shuffled_next_songs = next_songs.copy()
    while shuffled_next_songs == next_songs:
        random.shuffle(shuffled_next_songs)

    # replacing the queue
    queue_info[ctx.guild.id]['queue'] = previous_songs + shuffled_next_songs
    await ctx.respond('✅ Next songs were successfully shuffled.')


if __name__ == '__main__':
    bot.run(TOKEN)  # bot launch
    asyncio.run(spotify_client.close_client())  # closing Spotify client before exit
