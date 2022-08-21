# Main file

# Beat discord music bot v1.2.3
# Made by Knedme

from youtubesearchpython.__future__ import VideosSearch
import discord
import yt_dlp
import asyncio
import requests
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

loops = {}  # for /loop command
queues = {}  # for current queues
all_queues_info = {}  # all queues info, for /queue command
now_playing_pos = {}  # to display the current song in /queue command correctly
adding_to_queue_ids = []  # to add YouTube playlists or Spotify playlists/albums to the queue correctly


# this function checks if YouTube link is valid
def is_valid_yt_url(url):
    checker_url = 'https://www.youtube.com/oembed?url=' + url
    request = requests.get(checker_url)
    return request.status_code == 200


# this function extracts all info from YouTube video url
def extract_info(yt_url):
    return yt_dlp.YoutubeDL(
        {'format': 'bestaudio/best', 'cookiefile': COOKIES_FILE_PATH}).extract_info(yt_url, download=False)


# this function gets full name of the Spotify track with artists
def get_sp_track_full_name(sp_track_artist_list, sp_track_name):
    artist_names = sp_track_artist_list[0]['name']
    for i in range(len(sp_track_artist_list) - 1):
        artist_names += ', ' + sp_track_artist_list[i + 1]['name']
    return artist_names + ' - ' + sp_track_name


# this function returns the YouTube url of the specified full name of the Spotify track
async def get_sp_track_yt_url(sp_track_full_name):
    # finding track on YouTube Music or YouTube (if not found)
    try:
        event_loop = asyncio.get_event_loop()
        yt_url = 'https://www.youtube.com/watch?v='\
                 + (await event_loop.run_in_executor(ThreadPoolExecutor(),
                                                     ytm_client.search,
                                                     sp_track_full_name,
                                                     'songs'))[0]['videoId']
    except IndexError:
        search_obj = VideosSearch(sp_track_full_name, limit=1)
        try:
            yt_url = (await search_obj.next())['result'][0]['link']
        except IndexError:
            # if track not found even on YouTube, just assigning None
            yt_url = None
    return yt_url


# function, which 'loop' loops, checks the queue and plays the remaining links
def check_new_songs(vc, guild_id):
    global now_playing_pos

    # if the bot is not playing any songs, deleting the queue
    if not vc.is_connected():
        if guild_id in queues:
            del queues[guild_id]
        if guild_id in all_queues_info:
            del all_queues_info[guild_id]
        if guild_id in now_playing_pos:
            del now_playing_pos[guild_id]
        if guild_id in adding_to_queue_ids:
            adding_to_queue_ids.remove(guild_id)
        if guild_id in loops:
            del loops[guild_id]
        return

    # 'loop' track loops
    if guild_id in loops and loops[guild_id] == 'current track':
        src_url = queues[guild_id][0]['src_url']

        # play music
        try:
            play_music(vc, src_url, guild_id)
        except discord.errors.ClientException:
            pass
        return

    if queues[guild_id]:
        queues[guild_id].pop(0)

        try:
            src_url = queues[guild_id][0]['src_url']
            now_playing_pos[guild_id] += 1
        except IndexError:
            # if queue is empty and there are tracks adding to queue, then returning
            if guild_id in adding_to_queue_ids:
                return

            # if queue is empty and there is no queue loop, then deleting the variables and return
            if guild_id not in loops or loops[guild_id] != 'queue':
                del queues[guild_id]
                del all_queues_info[guild_id]
                del now_playing_pos[guild_id]
                if guild_id in loops:
                    del loops[guild_id]
                return

            # queue loop
            for track in all_queues_info[guild_id]:
                queues[guild_id].append({'url': track['url'], 'src_url': track['src_url']})
            now_playing_pos[guild_id] = 0
            src_url = queues[guild_id][0]['src_url']

        # play music
        try:
            play_music(vc, src_url, guild_id)
        except discord.errors.ClientException:
            return


# this function plays music from source url and then calling check_new_songs function
def play_music(vc, src_url, guild_id):
    if src_url is not None:
        vc.play(discord.FFmpegPCMAudio(
            src_url,
            executable=FFMPEG_PATH,
            before_options=FFMPEG_OPTIONS['before_options'],
            options=FFMPEG_OPTIONS['options']
            # calling the check_new_songs function after playing the current music
        ), after=lambda _: check_new_songs(vc, guild_id))
    else:
        check_new_songs(vc, guild_id)


@bot.event
async def on_ready():
    # opening Spotify client
    await spotify_client.get_auth_token_with_client_credentials()
    await spotify_client.create_new_client()

    print('\n🎵 Beat has been launched!')
    print('🔮 By Knedme\n')
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(type=discord.ActivityType.listening, name='/commands | /info'))


@bot.slash_command(name='commands', description='Shows a list of commands.')
async def commands(ctx):
    # adding embed
    embed = discord.Embed(
        title='Beat Commands',
        description='To watch full documentation [click here](https://github.com/Knedme/Beat).',
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
    embed.set_footer(text='v1.2.3')

    await ctx.respond(embed=embed)  # sending a message with embed


@bot.slash_command(name='info', description='Information about the bot.')
async def info(ctx):
    # adding embed
    embed = discord.Embed(title='Information about Beat', color=BOT_COLOR)

    embed.add_field(name='Server count:', value=f'🔺 `{len(bot.guilds)}`', inline=False)
    embed.add_field(name='Bot version:', value=f'✨ `1.2.3`', inline=False)
    embed.add_field(name='The bot is written on:', value=f'🐍 `Pycord`', inline=False)
    embed.add_field(name='Bot created by:', value='🔶 `Knedme`', inline=False)
    embed.add_field(name='GitHub repository:', value='📕 [Click Here](https://github.com/Knedme/Beat)')

    embed.set_thumbnail(url='https://i.imgur.com/pSMdJGW.png')
    embed.set_footer(text='v1.2.3 | Write /commands for the command list.')

    await ctx.respond(embed=embed)  # sending a message with embed


@bot.slash_command(name='support', description='Shows support contact.')
async def support(ctx):
    await ctx.respond(embed=discord.Embed(
        title='Support',
        description='If you have any problems, please write here: `Knedme#3143`',
        color=BOT_COLOR))


@bot.slash_command(name='join', description='Bot joins to your voice channel.')
async def join(ctx):
    if ctx.author.voice is None:
        return await ctx.respond(f'{ctx.author.mention}, You have to be connected to a voice channel.')

    channel = ctx.author.voice.channel

    if ctx.voice_client is None:  # if bot is not connected to a voice channel, connecting to it
        await channel.connect()
    else:  # else, just moving to ctx author voice channel
        await ctx.voice_client.move_to(channel)

    await ctx.guild.change_voice_state(channel=channel, self_mute=False, self_deaf=True)  # self deaf
    await ctx.respond(f'✅ Successfully joined to `{channel}`')


@bot.slash_command(
    name='play',
    description='Bot joins to your voice channel and plays music from a link or search query.')
async def play(ctx, query: discord.Option(str, 'Link or search query.')):
    global queues, all_queues_info, now_playing_pos

    await ctx.response.defer()

    if ctx.author.voice is None:
        return await ctx.respond(f'{ctx.author.mention}, You have to be connected to a voice channel.')

    channel = ctx.author.voice.channel
    if ctx.voice_client is None:  # if bot is not connected to a voice channel, connecting to it
        await channel.connect()
    else:  # else, just moving to ctx author voice channel
        await ctx.voice_client.move_to(channel)

    await ctx.guild.change_voice_state(channel=channel, self_mute=False, self_deaf=True)  # self deaf

    src_query = query  # saving source query
    url = ''
    spotify_link_info = None

    # if the query has a YouTube link, using this link
    if 'youtube.com/' in query or 'youtu.be/' in query:
        for el in query.split():
            if 'youtube.com/' in el or 'youtu.be/' in el:
                url = el
                # if the YouTube link is invalid, returning error
                if not is_valid_yt_url(url):
                    return await ctx.respond('Unknown YouTube url.')
                break

    # else if the query has a Spotify link, extracting info from this link
    elif 'open.spotify.com/' in query:
        for el in query.split():
            if 'open.spotify.com/' in el:
                query = el
                break

        _type = list(filter(None, query.split('/')))[-2]
        _id = list(filter(None, query.split('/')))[-1].split('?')[0]

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
            # if it's Spotify playlist or album, sorting through each track and getting YouTube url of the track

            # getting all tracks
            next_link = spotify_link_info['tracks']['next']
            while next_link:
                next_tracks = await spotify_client.next(next_link)
                spotify_link_info['tracks']['items'] += next_tracks['items']
                next_link = next_tracks['next']

            # if it was Spotify playlist, removing all episodes from it and moving item['track'] to item
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

            if len(spotify_link_info['tracks']['items']) == 0:  # if there is no tracks, returning
                return await ctx.respond('There is no tracks in your Spotify playlist/album.')

            # getting yt_url of the first track
            spotify_link_info['tracks']['items'][0]['full_name'] =\
                get_sp_track_full_name(spotify_link_info['tracks']['items'][0]['artists'],
                                       spotify_link_info['tracks']['items'][0]['name'])
            spotify_link_info['tracks']['items'][0]['yt_url'] =\
                await get_sp_track_yt_url(spotify_link_info['tracks']['items'][0]['full_name'])
            if spotify_link_info['tracks']['items'][0]['yt_url'] is None:
                await ctx.send(f'One of the songs in the album/playlist was not found, so this song will not play.')

    # if the query consists of something else, searching it on YouTube
    else:
        search_obj = VideosSearch(query, limit=1)
        try:
            url = (await search_obj.next())['result'][0]['link']
        except IndexError:
            # if video not found, sending message
            return await ctx.respond(f'Video titled \'{search_obj.data["query"]}\' not found. Try another video title.')

    # extracting source video/track url and playing song as usual
    # if it's not a Spotify playlist/album or a YouTube playlist
    if (spotify_link_info is None or spotify_link_info['type'] == 'track') and 'list=' not in url:
        event_loop = asyncio.get_event_loop()
        information = await event_loop.run_in_executor(ThreadPoolExecutor(), extract_info, url)
        src_url = information['url']
        title = information['title']

        if spotify_link_info is not None:  # changing title and link if it is Spotify track
            title = spotify_link_info['full_name']
            url = spotify_link_info['external_urls']['spotify']

        # filling queues
        if ctx.guild.id in queues:
            queues[ctx.guild.id].append({'url': url, 'src_url': src_url})
            all_queues_info[ctx.guild.id].append({'name': title, 'url': url, 'src_url': src_url})
        else:
            queues[ctx.guild.id] = [{'url': url, 'src_url': src_url}]
            now_playing_pos[ctx.guild.id] = 0
            all_queues_info[ctx.guild.id] = [{'name': title, 'url': url, 'src_url': src_url}]

    elif spotify_link_info is not None\
            and (spotify_link_info['type'] == 'album' or spotify_link_info['type'] == 'playlist'):
        # if it's Spotify playlist/album, adding to queue first track
        # and extracting its source url (if its YouTube url was found)
        first_track_info = spotify_link_info['tracks']['items'][0]
        title = spotify_link_info['name']
        url = spotify_link_info['external_urls']['spotify']

        if first_track_info['yt_url'] is not None:
            event_loop = asyncio.get_event_loop()
            information =\
                await event_loop.run_in_executor(ThreadPoolExecutor(), extract_info, first_track_info['yt_url'])
            src_url = information['url']
        else:
            src_url = None

        if ctx.guild.id in queues:
            queues[ctx.guild.id].append({'url': first_track_info['external_urls']['spotify'], 'src_url': src_url})
            all_queues_info[ctx.guild.id].append(
                {'name': first_track_info['full_name'],
                 'url': first_track_info['external_urls']['spotify'], 'src_url': src_url})
        else:
            queues[ctx.guild.id] = [{'url': first_track_info['external_urls']['spotify'], 'src_url': src_url}]
            now_playing_pos[ctx.guild.id] = 0
            all_queues_info[ctx.guild.id] = [{
                'name': first_track_info['full_name'],
                'url': first_track_info['external_urls']['spotify'], 'src_url': src_url}]
        adding_to_queue_ids.append(ctx.guild.id)

    else:  # if it's YouTube playlist, adding to queue first video and extracting its source url
        playlist = Playlist(url)
        event_loop = asyncio.get_event_loop()
        information = await event_loop.run_in_executor(ThreadPoolExecutor(), extract_info, playlist.video_urls[0])
        src_url = information['url']
        title = playlist.title

        # queuing first song
        if ctx.guild.id in queues:
            queues[ctx.guild.id].append({'url': playlist.video_urls[0], 'src_url': src_url})
            all_queues_info[ctx.guild.id].append(
                {'name': information['title'], 'url': playlist.video_urls[0], 'src_url': src_url})
        else:
            queues[ctx.guild.id] = [{'url': playlist.video_urls[0], 'src_url': src_url}]
            now_playing_pos[ctx.guild.id] = 0
            all_queues_info[ctx.guild.id] = [
                {'name': information['title'], 'url': playlist.video_urls[0], 'src_url': src_url}]
        adding_to_queue_ids.append(ctx.guild.id)

    vc = ctx.voice_client

    # play music
    try:
        play_music(vc, src_url, ctx.guild.id)
    except discord.errors.ClientException:
        pass

    # sending embed, depending on the queue
    if len(queues[ctx.guild.id]) != 1:
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
            if i == 0:
                continue

            if ctx.guild.id not in adding_to_queue_ids:  # if no longer need to add new tracks, returning
                return

            track = spotify_link_info['tracks']['items'][i]

            # getting yt_url of the track
            track['full_name'] = get_sp_track_full_name(track['artists'], track['name'])
            track['yt_url'] = await get_sp_track_yt_url(track['full_name'])
            if track['yt_url'] is None:
                await ctx.send(f'One of the songs in the album/playlist was not found, so this song will not play.')
                continue

            event_loop = asyncio.get_event_loop()
            track_yt_information = await event_loop.run_in_executor(ThreadPoolExecutor(), extract_info, track['yt_url'])
            src_track_url = track_yt_information['url']

            if ctx.guild.id in adding_to_queue_ids:
                # if the previous songs have already been played, then playing current one
                if not queues[ctx.guild.id]:
                    now_playing_pos[ctx.guild.id] += 1
                    try:
                        play_music(vc, src_track_url, ctx.guild.id)
                    except discord.errors.ClientException:
                        pass

                queues[ctx.guild.id].append({'url': track['external_urls']['spotify'], 'src_url': src_track_url})
                all_queues_info[ctx.guild.id].append(
                    {'name': track['full_name'], 'url': track['external_urls']['spotify'], 'src_url': src_track_url})

        adding_to_queue_ids.remove(ctx.guild.id)

        # if all tracks weren't found, returning
        if len(spotify_link_info['tracks']['items']) == 0:
            return await ctx.respond('All tracks from your album/playlist weren\'t found.')

        await ctx.send('✅ Spotify playlist/album was fully added to the queue.')

    elif 'list=' in url:  # adding to queue remaining tracks of YouTube playlist
        playlist = Playlist(url)

        for i in range(len(playlist.video_urls)):
            if i == 0:
                continue

            if ctx.guild.id not in adding_to_queue_ids:  # if no longer need to add new tracks, returning
                return

            event_loop = asyncio.get_event_loop()
            information = await event_loop.run_in_executor(ThreadPoolExecutor(), extract_info,
                                                           playlist.video_urls[i])
            src_video_url = information['url']

            if ctx.guild.id in adding_to_queue_ids:
                # if the previous videos have already been played, then playing current one
                if not queues[ctx.guild.id]:
                    now_playing_pos[ctx.guild.id] += 1
                    try:
                        play_music(vc, src_video_url, ctx.guild.id)
                    except discord.errors.ClientException:
                        pass

                queues[ctx.guild.id].append({'url': playlist.video_urls[i], 'src_url': src_video_url})
                all_queues_info[ctx.guild.id].append(
                    {'name': information['title'], 'url': playlist.video_urls[i], 'src_url': src_video_url})

        adding_to_queue_ids.remove(ctx.guild.id)
        await ctx.send('✅ YouTube playlist was fully added to the queue.')


@bot.slash_command(name='lofi', description='Joins to the channel and plays lofi hip hop.')
async def lofi(ctx):
    await ctx.invoke(bot.get_command('play'), query='lofi hip hop')


@bot.slash_command(name='skip', description='Skips current song.')
async def skip(ctx):
    if ctx.voice_client is None:
        return await ctx.respond('I am not playing any songs for you.')

    if ctx.author.voice is None:
        return await ctx.respond(f'{ctx.author.mention}, You have to be connected to a voice channel.')

    if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
        return await ctx.respond('You are in the wrong channel.')

    ctx.voice_client.stop()  # skipping current track
    await ctx.respond('✅ Successfully skipped.')


@bot.slash_command(name='leave', description='Leaves the voice channel.')
async def leave(ctx):
    if ctx.voice_client is None:
        return await ctx.respond('I am not playing any songs for you.')

    if ctx.author.voice is None:
        return await ctx.respond(f'{ctx.author.mention}, You have to be connected to a voice channel.')

    if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
        return await ctx.respond('You are in the wrong channel.')

    await ctx.voice_client.disconnect()  # leaving a voice channel
    await ctx.respond('✅ Successfully disconnected.')

    # clearing everything
    if ctx.guild.id in queues:
        del queues[ctx.guild.id]
    if ctx.guild.id in all_queues_info:
        del all_queues_info[ctx.guild.id]
    if ctx.guild.id in now_playing_pos:
        del now_playing_pos[ctx.ctx.guild.id]
    if ctx.guild.id in adding_to_queue_ids:
        adding_to_queue_ids.remove(ctx.guild.id)
    if ctx.guild.id in loops:
        del loops[ctx.guild.id]


@bot.slash_command(name='pause', description='Pauses current song.')
async def pause(ctx):
    if ctx.voice_client is None:
        return await ctx.respond('I am not playing any songs for you.')

    if ctx.author.voice is None:
        return await ctx.respond(f'{ctx.author.mention}, You have to be connected to a voice channel.')

    if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
        return await ctx.respond('You are in the wrong channel.')

    ctx.voice_client.pause()  # stopping a music
    await ctx.respond('⏸️ Successfully paused.')


@bot.slash_command(name='resume', description='Resumes current song if it is paused.')
async def resume(ctx):
    if ctx.voice_client is None:
        return await ctx.respond('I am not playing any songs for you.')

    if ctx.author.voice is None:
        return await ctx.respond(f'{ctx.author.mention}, You have to be connected to a voice channel.')

    if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
        return await ctx.respond('You are in the wrong channel.')

    ctx.voice_client.resume()  # resume music
    await ctx.respond('▶️ Successfully resumed.')


@bot.slash_command(name='queue', description='Shows current queue of songs.')
async def queue(ctx):
    if ctx.guild.id in all_queues_info:
        # splitting the queue into queues of 15 songs
        queue_info = all_queues_info[ctx.guild.id]
        arrays = []
        while len(queue_info) > 15:
            piece = queue_info[:15]
            arrays.append(piece)
            queue_info = queue_info[15:]
        arrays.append(queue_info)
        queue_info = arrays
    else:  # if queue is empty, sending empty embed
        return await ctx.respond(embed=discord.Embed(
            title='Current Queue',
            description='Your current queue is empty!',
            color=BOT_COLOR))

    pages = []
    for _ in queue_info:
        pages.append('')
    position = 0
    page = 0

    # filling every page with songs
    for i in queue_info:
        for j in i:
            # shortening the song name if it has more than 100 characters
            name = j['name']
            if len(name) > 100:
                name = name[:97] + '...'

            if position == now_playing_pos[ctx.guild.id]:
                # output the current song
                pages[page] += f'{position + 1}. [{name}]({j["url"]}) ⟵ current track\n'
            else:
                pages[page] += f'{position + 1}. [{name}]({j["url"]})\n'
            position += 1
        if page < len(queue_info) - 1:
            page += 1

    additional_info = f'🎶 Total tracks: {len(all_queues_info[ctx.guild.id])}'  # getting information about total tracks

    # getting information about loops
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

    # sending first page of the queue
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

    # sending a message depending on whether is loop turned on or off
    if ctx.guild.id not in loops:
        loops[ctx.guild.id] = 'queue'
        await ctx.respond('🔁 Queue loop enabled!')
    elif loops[ctx.guild.id] == 'queue':
        loops[ctx.guild.id] = 'current track'
        await ctx.respond('🔁 Current track loop enabled!')
    else:
        del loops[ctx.guild.id]
        await ctx.respond('❎ Loop disabled!')


@bot.slash_command(name='shuffle', description='Shuffles next songs in the queue.')
async def shuffle(ctx):
    global queues
    global all_queues_info

    if ctx.voice_client is None:
        return await ctx.respond('I am not playing any songs for you.')

    if ctx.author.voice is None:
        return await ctx.respond(f'{ctx.author.mention}, You have to be connected to a voice channel.')

    if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
        return await ctx.respond('You are in the wrong channel.')

    if ctx.guild.id not in all_queues_info or len(all_queues_info[ctx.guild.id]) == 0:
        return await ctx.respond('Your queue is empty!')

    # getting next songs from the queue
    next_songs = all_queues_info[ctx.guild.id][now_playing_pos[ctx.guild.id] + 1:]
    # getting previous songs from the queue
    previous_songs = all_queues_info[ctx.guild.id][:now_playing_pos[ctx.guild.id] + 1]

    if len(next_songs) <= 1:
        return await ctx.respond('Not enough songs to shuffle.')

    # shuffling next songs
    shuffled_next_songs = next_songs.copy()
    while shuffled_next_songs == next_songs:
        random.shuffle(shuffled_next_songs)

    # replacing the queue
    all_queues_info[ctx.guild.id] = previous_songs + shuffled_next_songs
    queues[ctx.guild.id] = []
    for song in all_queues_info[ctx.guild.id][now_playing_pos[ctx.guild.id]:]:
        queues[ctx.guild.id].append({'url': song['url'], 'src_url': song['src_url']})

    await ctx.respond('✅ Next songs were successfully shuffled.')


if __name__ == '__main__':
    bot.run(TOKEN)  # bot launch
    asyncio.run(spotify_client.close_client())  # closing Spotify client after exit
