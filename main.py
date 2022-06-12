# Main file

# Beat discord music bot v.1.2.0
# Made by Knedme

from youtubesearchpython.__future__ import VideosSearch
import discord
import yt_dlp
import spotipy
import asyncio
import requests
import random
from pytube import Playlist
from spotipy.oauth2 import SpotifyClientCredentials
from ytmusicapi import YTMusic
from concurrent.futures import ThreadPoolExecutor
from config import *

bot = discord.Bot()
spotify_client = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
	client_id=spotify_client_id, client_secret=spotify_client_secret))
ytm_client = YTMusic()

loops = {}  # for /loop command
queues = {}  # for queues
now_playing_pos = {}  # to display the current song in /queue command correctly
all_queues_info = {}  # all queues info, for /queue command


# function, which "loop" loops, checks the queue and replays the remaining links
def check_new_songs(guild_id, vc):
	global queues
	global now_playing_pos
	global all_queues_info

	# if the bot is not playing any songs, deleting the queue
	if not vc.is_connected():
		if guild_id in queues:
			del queues[guild_id]
		if guild_id in all_queues_info:
			del all_queues_info[guild_id]
		if guild_id in loops:
			del loops[guild_id]
		if guild_id in now_playing_pos:
			del now_playing_pos[guild_id]
		return

	# "loop" loops
	if guild_id in loops:
		if loops[guild_id] == "current track":
			src_video_url = queues[guild_id][0]["src_url"]

			# play music
			try:
				vc.play(discord.FFmpegPCMAudio(
					src_video_url,
					executable=ffmpeg,
					before_options=ffmpeg_options["before_options"],
					options=ffmpeg_options["options"]
				), after=lambda a: check_new_songs(guild_id, vc))
			except discord.errors.ClientException:
				pass

			return

	if queues[guild_id]:
		queues[guild_id].pop(0)

		try:
			src_video_url = queues[guild_id][0]["src_url"]
			now_playing_pos[guild_id] += 1
		except IndexError:
			# if queue is empty and there is no queue loop, deleting the variables and return
			if guild_id not in loops or loops[guild_id] != "queue":
				del queues[guild_id]
				del all_queues_info[guild_id]
				del now_playing_pos[guild_id]
				return

			# else looping queue
			for track in all_queues_info[guild_id]:
				queues[guild_id].append({"url": track["url"], "src_url": track["src_url"]})
			now_playing_pos[guild_id] = 0
			src_video_url = queues[guild_id][0]["src_url"]

		# play music
		try:
			vc.play(discord.FFmpegPCMAudio(
				src_video_url,
				executable=ffmpeg,
				before_options=ffmpeg_options["before_options"],
				options=ffmpeg_options["options"]
			), after=lambda a: check_new_songs(guild_id, vc))
		except discord.errors.ClientException:
			return


# this function extracts all info from video url
def extract_info(url):
	try:
		return yt_dlp.YoutubeDL({"format": "bestaudio", "cookiefile": cookies}).extract_info(url, download=False)
	except yt_dlp.utils.ExtractorError and yt_dlp.utils.DownloadError:  # if there is an error, changing format
		return yt_dlp.YoutubeDL({"format": "95", "cookiefile": cookies}).extract_info(url, download=False)


# this function finds YouTube Music track from search query and returns YouTube link to this track
def find_ytm_track(search_query):
	return 'https://www.youtube.com/watch?v=' + ytm_client.search(query=search_query, filter='songs')[0]['videoId']


# this function gets track info from spotify url
def get_info_from_spotify_link(url):
	# adding https if it's not in the url
	if 'https://' not in url and 'http://' not in url:
		url = 'https://' + url

	# getting type of link and id from url
	try:
		link_type = url.split('/')[3]
		_id = url.split('/')[4]
		if '?' in _id:
			_id = _id[:_id.index('?')]
	except IndexError:
		return 'Unknown spotify url'

	# getting the track info depending on the link type
	if link_type == 'track':
		information = spotify_client.track(_id)

		track_name = ''
		for artist in information['artists']:
			if information['artists'].index(artist) == 0:
				track_name += artist['name']
			else:
				track_name += ', ' + artist['name']
		track_name += ' - ' + information['name']

		return {
			'type': 'track',
			'name': track_name,
			'link': information['external_urls']['spotify']
		}
	elif link_type == 'album':
		information = spotify_client.album(_id)

		tracks = []
		for track in information['tracks']['items']:
			track_name = ''
			for artist in track['artists']:
				if track['artists'].index(artist) == 0:
					track_name += artist['name']
				else:
					track_name += ', ' + artist['name']
			track_name += ' - ' + track['name']
			tracks.append({
				'type': 'track',
				'name': track_name,
				'link': track['external_urls']['spotify']
			})

		return {
			'type': 'album',
			'name': information['name'],
			'link': information['external_urls']['spotify'],
			'tracks': tracks
		}
	elif link_type == 'playlist':
		information = spotify_client.playlist(_id)

		tracks = []
		for track in information['tracks']['items']:
			track_name = ''
			for artist in track['track']['artists']:
				if track['track']['artists'].index(artist) == 0:
					track_name += artist['name']
				else:
					track_name += ', ' + artist['name']
			track_name += ' - ' + track['track']['name']
			tracks.append({
				'type': 'track',
				'name': track_name,
				'link': track['track']['external_urls']['spotify']
			})

		return {
			'type': 'playlist',
			'name': information['name'],
			'link': information['external_urls']['spotify'],
			'tracks': tracks
		}
	else:
		return 'Unknown spotify url'


# this function checks if YouTube link is valid
def check_yt_url(url):
	checker_url = 'https://www.youtube.com/oembed?url=' + url
	request = requests.get(checker_url)
	return request.status_code == 200


# this function gets the source url with the best sound quality from the yt-dlp result
def get_best_audio(information):
	best_format = None
	for _format in information['formats']:
		if _format['resolution'] == 'audio only' or _format['protocol'] == 'm3u8_native':
			if best_format is None or int(best_format['format_id']) < int(_format['format_id']):
				best_format = _format

	return best_format['url']


@bot.event
async def on_ready():
	print("\n🎵 Beat has been launched!")
	print("🔮 By Knedme\n")
	await bot.change_presence(
		status=discord.Status.online,
		activity=discord.Activity(type=discord.ActivityType.listening, name="/commands | /info"))


@bot.slash_command(name='commands', description='Shows a list of commands.')
async def commands(ctx):
	# Adding embed
	embed = discord.Embed(
		title="Beat Commands",
		description="To watch full documentation [click here](https://github.com/Knedme/Beat).",
		color=0x515596
	)

	embed.add_field(name="/join", value="Bot joins to your voice channel.", inline=False)
	embed.add_field(
		name="/play youtube-video-link | spotify-link | search-query",
		value="Bot joins to your voice channel and plays music from a link or search query.",
		inline=False
	)
	embed.add_field(name="/lofi", value="Bot joins to your channel and plays lofi.", inline=False)
	embed.add_field(name="/leave", value="Leave the voice channel.", inline=False)
	embed.add_field(name="/skip", value="Skips current track.", inline=False)
	embed.add_field(name="/pause", value="Pause music.", inline=False)
	embed.add_field(name="/resume", value="Resume music.", inline=False)
	embed.add_field(name="/queue", value="Shows current queue.", inline=False)
	embed.add_field(name="/loop", value="Loops current track.", inline=False)
	embed.add_field(name="/shuffle", value="Shuffles next songs in the queue.", inline=False)
	embed.add_field(name="/support", value="Shows support contact.", inline=False)
	embed.add_field(name="/commands", value="Shows a list of commands.", inline=False)
	embed.add_field(name="/info", value="Information about the bot.")
	embed.set_footer(text="v1.2.0")

	await ctx.respond(embed=embed)  # sending a message with embed


@bot.slash_command(name='info', description='Information about the bot.')
async def info(ctx):

	# Adding embed
	embed = discord.Embed(title="Information about Beat", color=0x515596)

	embed.add_field(name="Server count:", value=f"🔺 `{len(bot.guilds)}`", inline=False)
	embed.add_field(name="Bot version:", value=f"💡 `1.2.0`", inline=False)
	embed.add_field(name="The bot is written on:", value=f"🐍 `Pycord`", inline=False)
	embed.add_field(name="Bot created by:", value="🔶 `Knedme`", inline=False)
	embed.add_field(name="GitHub repository:", value="📕 [Click Here](https://github.com/Knedme/Beat)")

	embed.set_thumbnail(url="https://i.imgur.com/pSMdJGW.png")
	embed.set_footer(text="v1.2.0 | Write +commands for the command list.")

	await ctx.respond(embed=embed)  # sending a message with embed


@bot.slash_command(name='support', description='Shows support contact.')
async def support(ctx):
	await ctx.respond(embed=discord.Embed(
		title="Support",
		description="If you have any problems, please write here: `Knedme#3143`",
		color=0x515596
	))


@bot.slash_command(name='join', description='Bot joins to your voice channel.')
async def join(ctx):
	if ctx.author.voice is None:
		return await ctx.respond(f"{ctx.author.mention}, You have to be connected to a voice channel.")

	channel = ctx.author.voice.channel

	if ctx.voice_client is None:  # if bot is not connected to a voice channel, connecting to a voice channel
		await channel.connect()
	else:  # else, just moving to ctx author voice channel
		await ctx.voice_client.move_to(channel)

	await ctx.guild.change_voice_state(channel=channel, self_mute=False, self_deaf=True)  # self deaf

	await ctx.respond(f"✅ Successfully joined to `{channel}`")


# noinspection PyTypeChecker
@bot.slash_command(
	name='play',
	description='Bot joins to your voice channel and plays music from a link or search query.')
async def play(ctx, query: discord.Option(str, 'Link or search query.')):
	global queues
	global now_playing_pos
	global all_queues_info

	await ctx.response.defer()

	if ctx.author.voice is None:
		return await ctx.respond(f"{ctx.author.mention}, You have to be connected to a voice channel.")

	channel = ctx.author.voice.channel
	if ctx.voice_client is None:  # if bot is not connected to a voice channel, connecting to a voice channel
		await channel.connect()
	else:  # else, just moving to ctx author voice channel
		await ctx.voice_client.move_to(channel)

	await ctx.guild.change_voice_state(channel=channel, self_mute=False, self_deaf=True)  # self deaf

	src_query = query  # saving source search query
	url = ''
	spotify_link_info = {}
	spotify_playlist_yt_urls = []

	if "youtube.com/" in query or "youtu.be/" in query:
		for el in query.split():
			if "youtube.com/" in el or "youtu.be/" in el:
				url = el

				# adding https if it's not in the url
				if 'https://' not in url and 'http://' not in url:
					url = 'https://' + url

				# if the YouTube link is invalid, returning error
				if not check_yt_url(url):
					return await ctx.respond('Unknown YouTube url.')

	# else if the query has a Spotify link, extracting info from this link
	elif "open.spotify.com/" in query:
		for el in query.split():
			if "open.spotify.com/" in el:
				query = el

		# getting information about track/album/playlist
		try:
			spotify_link_info = get_info_from_spotify_link(query)
		except spotipy.SpotifyException:
			return await ctx.respond('Something went wrong. If it\'s a link to a spotify playlist, make sure it\'s open.')

		# error handling
		if spotify_link_info == 'Unknown spotify url':
			return await ctx.respond(
				'Unknown spotify url. ' +
				'Make sure you entered the link correctly and that your link leads to spotify track/album/playlist')

		if spotify_link_info['type'] == 'track':
			# if it's single spotify track, finding it on YouTube Music and playing as usual
			try:
				event_loop = asyncio.get_event_loop()
				url = await event_loop.run_in_executor(ThreadPoolExecutor(), find_ytm_track, spotify_link_info['name'])
			except IndexError:
				# if track not found on YouTube Music, sending message
				return await ctx.respond(f'Your song was not found. Try another one.')
		else:
			# if it's spotify playlist or album, sorting through each track, finding it on YouTube Music and
			# adding it to the array of links from YouTube

			for track in spotify_link_info['tracks']:
				try:
					event_loop = asyncio.get_event_loop()
					url_from_yt = await event_loop.run_in_executor(ThreadPoolExecutor(), find_ytm_track, track['name'])
					spotify_playlist_yt_urls.append(url_from_yt)
				except IndexError:
					# if one of the tracks not found on YouTube Music, sending message
					await ctx.send(f'One of the songs in the album/playlist was not found, so it will not play.')

			# if all tracks aren't found, returning
			if len(spotify_playlist_yt_urls) == 0:
				return await ctx.respond('All tracks from your album/playlist was not found.')

	# if the request consists of something else, searching it on YouTube
	else:
		search_obj = VideosSearch(query, limit=1)
		try:
			url = (await search_obj.next())["result"][0]["link"]
		except IndexError:
			# if video not found, sending message
			return await ctx.respond(f'Video titled "{search_obj.data["query"]}" not found. Try another video title.')

	# extracting source video/track url and playing song as usual
	#  if it's not a spotify playlist/album or a YouTube playlist
	if len(spotify_playlist_yt_urls) == 0 and 'list=' not in url:
		event_loop = asyncio.get_event_loop()
		information = await event_loop.run_in_executor(ThreadPoolExecutor(), extract_info, url)
		src_url = get_best_audio(information)
		title = information["title"]

		# changing title and link if it is spotify track
		if len(spotify_link_info) != 0:
			title = spotify_link_info['name']
			url = spotify_link_info['link']

		# filling queues
		if ctx.guild.id in queues:
			queues[ctx.guild.id].append({"url": url, "src_url": src_url})
			all_queues_info[ctx.guild.id].append({"name": title, "url": url, "src_url": src_url})
		else:
			queues[ctx.guild.id] = [{"url": url, "src_url": src_url}]
			now_playing_pos[ctx.guild.id] = 0
			all_queues_info[ctx.guild.id] = [{"name": title, "url": url, "src_url": src_url}]

	elif len(spotify_playlist_yt_urls) != 0:
		# if it's spotify playlist/album, adding to queue first track and extracting its source url
		event_loop = asyncio.get_event_loop()
		information = await event_loop.run_in_executor(ThreadPoolExecutor(), extract_info, spotify_playlist_yt_urls[0])
		src_url = get_best_audio(information)
		first_track_info = spotify_link_info['tracks'][0]
		title = spotify_link_info['name']
		url = spotify_link_info['link']

		if ctx.guild.id in queues:
			queues[ctx.guild.id].append({"url": first_track_info['link'], "src_url": src_url})
			all_queues_info[ctx.guild.id].append(
				{"name": first_track_info['name'], "url": first_track_info['link'], "src_url": src_url})
		else:
			queues[ctx.guild.id] = [{"url": first_track_info['link'], "src_url": src_url}]
			now_playing_pos[ctx.guild.id] = 0
			all_queues_info[ctx.guild.id] = [{
				"name": first_track_info['name'],
				"url": first_track_info['link'], "src_url": src_url}]

	else:  # if it's YouTube playlist, adding to queue first video and extracting its source url
		playlist = Playlist(url)
		event_loop = asyncio.get_event_loop()
		information = await event_loop.run_in_executor(ThreadPoolExecutor(), extract_info, playlist.video_urls[0])
		src_url = get_best_audio(information)
		title = playlist.title

		# queuing first song
		if ctx.guild.id in queues:
			queues[ctx.guild.id].append({"url": playlist.video_urls[0], "src_url": src_url})
			all_queues_info[ctx.guild.id].append(
				{"name": information["title"], "url": playlist.video_urls[0], "src_url": src_url})
		else:
			queues[ctx.guild.id] = [{"url": playlist.video_urls[0], "src_url": src_url}]
			now_playing_pos[ctx.guild.id] = 0
			all_queues_info[ctx.guild.id] = [
				{"name": information["title"], "url": playlist.video_urls[0], "src_url": src_url}]

	vc = ctx.voice_client

	try:
		vc.play(discord.FFmpegPCMAudio(
			src_url,
			executable=ffmpeg,
			before_options=ffmpeg_options["before_options"],
			options=ffmpeg_options["options"]
			# calling the check_new_songs function after playing the current music
		), after=lambda a: check_new_songs(ctx.guild.id, vc))
	except discord.errors.ClientException:
		pass

	# Sending embed, depending on the queue
	if len(queues[ctx.guild.id]) != 1:
		embed = discord.Embed(
			title="Queue",
			description=f"🔎 Searching for `{src_query}`\n\n" +
			f"""✅ [{title}]({url}) - successfully added to queue.""",
			color=0x515596)
	else:
		embed = discord.Embed(
			title="Now playing",
			description=f"✅ Successfully joined to `{channel}`\n\n" +
			f"🔎 Searching for `{src_query}`\n\n" +
			f"""▶️ Now playing - [{title}]({url})""",
			color=0x515596)

	await ctx.respond(embed=embed)

	if len(spotify_playlist_yt_urls) != 0:  # adding to queue remaining tracks of spotify playlist or album
		for track_yt_url in spotify_playlist_yt_urls:
			if spotify_playlist_yt_urls.index(track_yt_url) != 0:
				event_loop = asyncio.get_event_loop()
				track_yt_information = await event_loop.run_in_executor(ThreadPoolExecutor(), extract_info, track_yt_url)
				src_track_url = track_yt_information["formats"][3]["url"]
				track_info = spotify_link_info['tracks'][spotify_playlist_yt_urls.index(track_yt_url)]

				queues[ctx.guild.id].append({"url": track_info['link'], "src_url": src_track_url})
				all_queues_info[ctx.guild.id].append(
					{"name": track_info['name'], "url": track_info['link'], "src_url": src_track_url})

		await ctx.send('✅ Spotify playlist/album was successfully added to the queue.')

	elif 'list=' in url:  # adding to queue remaining tracks of YouTube playlist
		playlist = Playlist(url)

		for i in range(len(playlist.video_urls)):
			if i != 0:
				event_loop = asyncio.get_event_loop()
				information = await event_loop.run_in_executor(ThreadPoolExecutor(), extract_info, playlist.video_urls[i])
				src_video_url = information["formats"][3]["url"]
				queues[ctx.guild.id].append({"url": playlist.video_urls[i], "src_url": src_video_url})
				all_queues_info[ctx.guild.id].append(
					{"name": information['title'], "url": playlist.video_urls[i], "src_url": src_video_url})

		await ctx.send('✅ YouTube playlist was successfully added to the queue.')


@bot.slash_command(name='lofi', description='Joins to the channel and plays lofi hip hop.')
async def lofi(ctx):
	await ctx.invoke(bot.get_command('play'), query='lofi hip hop')


@bot.slash_command(name='skip', description='Skips current song.')
async def skip(ctx):
	if ctx.voice_client is None:
		return await ctx.respond("I am not playing any songs for you.")

	if ctx.author.voice is None:
		return await ctx.respond(f"{ctx.author.mention}, You have to be connected to a voice channel.")

	if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
		return await ctx.respond("You are in the wrong channel.")

	ctx.voice_client.stop()  # skipping current track
	await ctx.respond("✅ Successfully skipped.")


@bot.slash_command(name='leave', description='Leaves the voice channel.')
async def leave(ctx):
	if ctx.voice_client is None:
		return await ctx.respond("I am not playing any songs for you.")

	if ctx.author.voice is None:
		return await ctx.respond(f"{ctx.author.mention}, You have to be connected to a voice channel.")

	if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
		return await ctx.respond("You are in the wrong channel.")

	await ctx.voice_client.disconnect()  # leaving a voice channel
	await ctx.respond("✅ Successfully disconnected.")

	# clearing queues and loops
	if ctx.guild.id in queues:
		del queues[ctx.guild.id]
	if ctx.guild.id in all_queues_info:
		del all_queues_info[ctx.guild.id]
	if ctx.guild.id in loops:
		del loops[ctx.guild.id]
	if ctx.guild.id in now_playing_pos:
		del now_playing_pos[ctx.guild.id]


@bot.slash_command(name='pause', description='Pauses current song.')
async def pause(ctx):
	if ctx.voice_client is None:
		return await ctx.respond("I am not playing any songs for you.")

	if ctx.author.voice is None:
		return await ctx.respond(f"{ctx.author.mention}, You have to be connected to a voice channel.")

	if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
		return await ctx.respond("You are in the wrong channel.")

	ctx.voice_client.pause()  # stopping a music
	await ctx.respond("⏸️ Successfully paused.")


@bot.slash_command(name='resume', description='Resumes current song if it is paused.')
async def resume(ctx):
	if ctx.voice_client is None:
		return await ctx.respond("I am not playing any songs for you.")

	if ctx.author.voice is None:
		return await ctx.respond(f"{ctx.author.mention}, You have to be connected to a voice channel.")

	if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
		return await ctx.respond("You are in the wrong channel.")

	ctx.voice_client.resume()  # resume music
	await ctx.respond("▶️ Successfully resumed.")


@bot.slash_command(name='queue', description='Shows current queue of songs.')
async def queue(ctx):
	global all_queues_info

	position = 0
	if ctx.guild.id in all_queues_info:
		# splitting the queue into queues of 10 songs
		queue_info = all_queues_info[ctx.guild.id]
		arrays = []
		while len(queue_info) > 10:
			pice = queue_info[:10]
			arrays.append(pice)
			queue_info = queue_info[10:]
		arrays.append(queue_info)
		queue_info = arrays
	else:  # if queue is empty, sending empty embed
		return await ctx.respond(embed=discord.Embed(
			title="Current Queue",
			description="Your current queue is empty!",
			color=0x515596))
	content = []
	for _ in queue_info:
		content.append("")
	page = 0

	# filling content with songs
	for i in queue_info:
		for j in i:
			if position == now_playing_pos[ctx.guild.id]:
				content[page] += f"""{position+1}. [{j["name"]}]({j["url"]}) ⟵ current track\n"""  # output the current song
			else:
				content[page] += f"""{position+1}. [{j["name"]}]({j["url"]})\n"""
			position += 1
		if page < len(queue_info) - 1:
			page += 1

	# getting information about loops
	loops_info = ""
	if ctx.guild.id not in loops or loops[ctx.guild.id] == "none":
		loops_info = "🔁 Queue loop: disabled | 🔁 Current track loop: disabled"
	elif loops[ctx.guild.id] == "queue":
		loops_info = "🔁 Queue loop: enabled | 🔁 Current track loop: disabled"
	elif loops[ctx.guild.id] == "current track":
		loops_info = "🔁 Queue loop: disabled | 🔁 Current track loop: enabled"

	# sending the entire queue of 10 songs for each message
	for songs in content:
		if content.index(songs) == 0:
			await ctx.respond(embed=discord.Embed(
				title="Current Queue",
				description=songs,
				color=0x515596)
				.set_footer(text=loops_info))
		else:
			await ctx.send(embed=discord.Embed(
				description=songs,
				color=0x515596)
				.set_footer(text=loops_info))


@bot.slash_command(name='loop', description='Enables/Disables Queue/Track loop.')
async def loop(ctx):
	global loops

	if ctx.voice_client is None:
		return await ctx.respond("I am not playing any songs for you.")

	if ctx.author.voice is None:
		return await ctx.respond(f"{ctx.author.mention}, You have to be connected to a voice channel.")

	if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
		return await ctx.respond("You are in the wrong channel.")

	# sending a message depending on whether is loop turned on or off
	if ctx.guild.id not in loops or loops[ctx.guild.id] == "none":
		loops[ctx.guild.id] = "queue"
		await ctx.respond("🔁 Queue loop enabled!")
	elif loops[ctx.guild.id] == "queue":
		loops[ctx.guild.id] = "current track"
		await ctx.respond("🔁 Current track loop enabled!")
	else:
		loops[ctx.guild.id] = "none"
		await ctx.respond("❎ Loop disabled!")


@bot.slash_command(name='shuffle', description='Shuffles next songs in the queue.')
async def shuffle(ctx):
	global queues
	global all_queues_info

	if ctx.voice_client is None:
		return await ctx.respond("I am not playing any songs for you.")

	if ctx.author.voice is None:
		return await ctx.respond(f"{ctx.author.mention}, You have to be connected to a voice channel.")

	if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
		return await ctx.respond("You are in the wrong channel.")

	if ctx.guild.id not in all_queues_info or len(all_queues_info[ctx.guild.id]) == 0:
		return await ctx.respond('Your queue is empty!')

	# getting next songs from the queue
	next_songs = all_queues_info[ctx.guild.id][now_playing_pos[ctx.guild.id] + 1:]
	# getting previous songs from the queue
	previous_songs = all_queues_info[ctx.guild.id][:now_playing_pos[ctx.guild.id] + 1]

	if len(next_songs) <= 1:
		return await ctx.respond('Not enough songs to shuffle.')

	random.shuffle(next_songs)  # shuffling next songs

	# replacing the queue
	all_queues_info[ctx.guild.id] = previous_songs + next_songs
	queues[ctx.guild.id] = []
	for song in all_queues_info[ctx.guild.id][now_playing_pos[ctx.guild.id]:]:
		queues[ctx.guild.id].append({'url': song['url'], 'src_url': song['src_url']})

	await ctx.respond('✅ Next songs were successfully shuffled.')


if __name__ == "__main__":
	while True:  # auto-reboot if bot crashed
		bot.run(token)  # bot launch
