# Main file

# Beat discord music bot v.1.0.1
# Made by Knedme

import discord
import youtube_dl
from youtubesearchpython import VideosSearch
from discord.ext import commands
from config import *

bot = commands.Bot(command_prefix=prefix)

loops = {}  # for +loop command
queues = {}  # for queues
now_playing_pos = {}  # to display the current song in +queue command correctly
queues_info = {}  # all queue info, for +queue command


# function, which checks the queue and replays the remaining links and "loop" loops
def check_new_songs(guild_id, vc):
	global queues
	global now_playing_pos
	global queues_info

	if not vc.is_connected():
		if guild_id in queues:
			del queues[guild_id]
		if guild_id in queues_info:
			del queues_info[guild_id]
		if guild_id in loops:
			del loops[guild_id]
		if guild_id in now_playing_pos:
			del now_playing_pos[guild_id]
		return

	# "loop" loops
	if guild_id in loops:
		src_video_url = queues[guild_id][0]["src_url"]

		# play music
		try:
			print("[log]: Successfully started to play looped song.")
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

		# if queue is empty, deleting the variables and return
		try:
			src_video_url = queues[guild_id][0]["src_url"]
		except IndexError:
			del queues[guild_id]
			del queues_info[guild_id]
			del now_playing_pos[guild_id]
			return

		now_playing_pos[guild_id] += 1

		# play music
		try:
			vc.play(discord.FFmpegPCMAudio(
				src_video_url,
				executable=ffmpeg,
				before_options=ffmpeg_options["before_options"],
				options=ffmpeg_options["options"]
			), after=lambda a: check_new_songs(guild_id, vc))
			print("[log]: Successfully started to play song.")
		except discord.errors.ClientException:
			return


@bot.event
async def on_ready():
	print("\n🎵 Beat has been launched!")
	print("🔮 By Knedme\n")

	await bot.change_presence(status=discord.Status.online, activity=discord.Game("+commands | +info"))  # setting activity


# on command errors
@bot.event
async def on_command_error(ctx, err):
	print(f"[error]: {err}")
	await ctx.send(embed=discord.Embed(
		title="Error",
		description=err,
		color=0x515596
	))


# commands command
@bot.command(aliases=["comands", "c"])
async def commands(ctx):

	# Adding embed
	embed = discord.Embed(
		title="Beat Commands",
		description="To watch full documentation [click here](https://github.com/Knedme/Beat).",
		color=0x515596
	)

	embed.add_field(
		name="+play youtube-video-link (or search)",
		value="Bot joins to your channel and plays music from a video link.",
		inline=False
	)
	embed.add_field(name="+music", value="Bot joins to your channel and plays lofi.", inline=False)
	embed.add_field(name="+leave", value="Leave the voice channel.", inline=False)
	embed.add_field(name="+skip", value="Skips current track.", inline=False)
	embed.add_field(name="+pause", value="Pause music.", inline=False)
	embed.add_field(name="+resume", value="Resume music.", inline=False)
	embed.add_field(name="+queue", value="Shows current queue.", inline=False)
	embed.add_field(name="+loop", value="Loops current track.", inline=False)
	embed.add_field(name="+commands", value="Shows a list of commands.", inline=False)
	embed.add_field(name="+info", value="Information about the bot.")

	embed.set_footer(text="v1.0.1")

	await ctx.send(embed=embed)  # sending a message with embed


# info command
@bot.command(aliases=["i", "information"])
async def info(ctx):

	# Adding embed
	embed = discord.Embed(title="Information about Beat", color=0x515596)

	embed.add_field(name="Server count:", value=f"🔺 `{len(bot.guilds)}`", inline=False)
	embed.add_field(name="Bot version:", value=f"🔨 `1.0.1`", inline=False)
	embed.add_field(name="The bot is written on:", value=f"🐍 `discord.py`", inline=False)
	embed.add_field(name="Bot created by:", value="🔶 `Knedme`", inline=False)
	embed.add_field(name="GitHub repository:", value="📕 [Click Here](https://github.com/Knedme/Beat)")

	embed.set_thumbnail(url="http://i.piccy.info/i9/af4f19335c0e09f0a8dbda34ece5a68b/1631681493/55409/1440926/1x.png")
	embed.set_footer(text="v1.0.1 | Write +commands for the command list.")

	await ctx.send(embed=embed)  # sending a message with embed


# play command
# noinspection PyTypeChecker
@bot.command(aliases=["p"])
async def play(ctx, *, video=None):
	global queues
	global now_playing_pos
	global queues_info

	if ctx.author.voice is None:
		return await ctx.send(f"{ctx.author.mention}, You have to be connected to a voice channel.")

	channel = ctx.author.voice.channel

	if ctx.voice_client is None:  # if bot is not connected to a voice channel, connecting to a voice channel
		await channel.connect()
		print("[log]: Successfully joined to the channel.")
	else:  # else, just move to ctx author voice channel
		await ctx.voice_client.move_to(channel)

	if video is not None:
		# searching for a video

		video_search = video
		if "https://www.youtube.com/watch?v=" in video or "https://youtu.be/" in video:
			video_url = ""
			for el in video.split():
				if "https://www.youtube.com/watch?v=" in el or "https://youtu.be/" in el:
					if "&list=" in el:
						await ctx.send("Loading playlist...")
					video_url = el
		else:
			print(f"[log]: Searching for \'{video_search}\'...")
			video = VideosSearch(video, limit=1)
			video_url = video.result()["result"][0]["link"]

		is_stream = False

		# finding video
		try:
			try:
				information = youtube_dl.YoutubeDL(
					{"format": "bestaudio", "cookiefile": cookies}).extract_info(video_url, download=False)
			except youtube_dl.utils.ExtractorError and youtube_dl.utils.DownloadError:
				# if there is an error, changing format.
				information = youtube_dl.YoutubeDL(
					{"format": "95", "cookiefile": cookies}).extract_info(video_url, download=False)
				is_stream = True
		except youtube_dl.utils.ExtractorError and youtube_dl.utils.DownloadError:
			# if unknown error
			print("[error]: Error while reading video url.")
			return await ctx.send("Something went wrong.")

		# if it's not a playlist, playing the song as usual
		if "_type" not in information:
			src_video_url = information["formats"][0]["url"]  # source url
			video_title = information["title"]
			if is_stream:
				video_title = video_title[0:-17]

			# filling queues
			if ctx.guild.id in queues:
				queues[ctx.guild.id].append({"url": video_url, "src_url": src_video_url})
				queues_info[ctx.guild.id].append({"name": information["title"], "url": video_url})
			else:
				queues[ctx.guild.id] = [{"url": video_url, "src_url": src_video_url}]
				now_playing_pos[ctx.guild.id] = 0
				queues_info[ctx.guild.id] = [{"name": information["title"], "url": video_url}]

			print("[log]: Successfully queued song.")
		else:  # else queueing playlist
			src_video_url = information["entries"][0]["url"]
			video_title = information["title"]

			# queuing first song
			if ctx.guild.id in queues:
				queues[ctx.guild.id].append({"url": video_url, "src_url": src_video_url})
				queues_info[ctx.guild.id].append({"name": information["entries"][0]["title"], "url": video_url})
			else:
				queues[ctx.guild.id] = [{"url": video_url, "src_url": src_video_url}]
				now_playing_pos[ctx.guild.id] = 0
				queues_info[ctx.guild.id] = [{"name": information["entries"][0]["title"], "url": video_url}]

			# queuing another songs
			for v in information["entries"]:
				if information["entries"].index(v) != 0:
					queues[ctx.guild.id].append({"url": video_url, "src_url": v["url"]})
					queues_info[ctx.guild.id].append({"name": v["title"], "url": video_url})

			print("[log]: Successfully queued playlist.")

		vc = ctx.voice_client

		try:
			vc.play(discord.FFmpegPCMAudio(
				src_video_url,
				executable=ffmpeg,
				before_options=ffmpeg_options["before_options"],
				options=ffmpeg_options["options"]
			), after=lambda a: check_new_songs(ctx.guild.id, vc))  # calling the check_new_songs function after
			print("[log]: Successfully started to play song.")
		# playing the current music
		except discord.errors.ClientException:
			pass

		# Adding embed, depending on the queue
		if len(queues[ctx.guild.id]) != 1:
			embed = discord.Embed(
				title="Queue",
				description=f"🔎 Searching for `{video_search}`\n\n" +
				f"""✅ [{video_title}]({video_url}) - successfully added to queue.""",
				color=0x515596)
		else:
			embed = discord.Embed(
				title="Now playing",
				description=f"✅ Successfully joined to `{channel}`\n\n" +
				f"🔎 Searching for `{video_search}`\n\n" +
				f"""▶️ Now playing - [{video_title}]({video_url})""",
				color=0x515596)

		await ctx.send(embed=embed)


# lofi/music command
# noinspection PyTypeChecker
@bot.command(aliases=["lofi", "lo-fi", "chill"])
async def music(ctx):
	global queues
	global now_playing_pos
	global queues_info

	if ctx.author.voice is None:
		return await ctx.send(f"{ctx.author.mention}, You have to be connected to a voice channel.")

	channel = ctx.author.voice.channel

	if ctx.voice_client is None:  # if bot is not connected to a voice channel, connecting to a voice channel
		await channel.connect()
		print("[log]: Successfully joined to the channel.")
	else:  # else, just move to ctx author voice channel
		await ctx.voice_client.move_to(channel)

	# searching for lofi hip hop
	print(f"[log]: Searching for \'lofi hip hop\'...")
	video = VideosSearch("lofi hip hop", limit=1)
	video_url = video.result()["result"][0]["link"]

	vc = ctx.voice_client

	# finding video
	try:
		information = youtube_dl.YoutubeDL({"format": "95"}).extract_info(video_url, download=False)
	except youtube_dl.utils.ExtractorError and youtube_dl.utils.DownloadError:
		# if unknown error
		print("[error]: Error while reading video url.")
		return await ctx.send("Something went wrong.")

	src_video_url = information["formats"][0]["url"]  # source url
	video_title = information["title"][0:-17]

	# filling queue
	if ctx.guild.id in queues:
		queues[ctx.guild.id].append({"url": video_url, "src_url": src_video_url})
		queues_info[ctx.guild.id].append({"name": information["title"], "url": video_url})
	else:
		queues[ctx.guild.id] = [{"url": video_url, "src_url": src_video_url}]
		now_playing_pos[ctx.guild.id] = 0
		queues_info[ctx.guild.id] = [{"name": information["title"], "url": video_url}]

	print("[log]: Successfully queued song.")

	try:
		vc.play(discord.FFmpegPCMAudio(
			src_video_url,
			executable=ffmpeg,
			before_options=ffmpeg_options["before_options"],
			options=ffmpeg_options["options"]
		), after=lambda a: check_new_songs(ctx.guild.id, vc))  # calling the check_new_songs function after
		# playing the current music
		print("[log]: Successfully started to play song.")
	except discord.errors.ClientException:
		pass

	# Adding embed, depending on the queue
	if len(queues[ctx.guild.id]) != 1:
		embed = discord.Embed(
			title="Queue",
			description=f"🔎 Searching for `lofi hip hop`\n\n" +
			f"""✅ [{video_title}]({video_url}) - successfully added to queue.""",
			color=0x515596)
	else:
		embed = discord.Embed(
			title="Now playing",
			description=f"✅ Successfully joined to `{channel}`\n\n" +
			f"🔎 Searching for `lofi hip hop`\n\n" +
			f"""▶️ Now playing - [{video_title}]({video_url})""",
			color=0x515596)

	await ctx.send(embed=embed)


# skip command
@bot.command(aliases=["s"])
async def skip(ctx):
	if ctx.voice_client is None:
		return await ctx.send("I am not connected to any voice channels.")

	if ctx.author.voice is None:
		return await ctx.send(f"{ctx.author.mention}, You have to be connected to a voice channel.")

	if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
		return await ctx.send("You are in the wrong channel.")

	ctx.voice_client.stop()  # skipping current track
	await ctx.message.add_reaction("✅")  # adding a reaction
	await ctx.send("Successfully skipped.")
	print("[log]: Song skipped successfully.")


# leave command
@bot.command(aliases=["l", "disconnect", "d"])
async def leave(ctx):
	if ctx.voice_client is None:
		return await ctx.send("I am not connected to any voice channels.")

	if ctx.author.voice is None:
		return await ctx.send(f"{ctx.author.mention}, You have to be connected to a voice channel.")

	if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
		return await ctx.send("You are in the wrong channel.")

	await ctx.voice_client.disconnect()  # leaving a voice channel
	await ctx.message.add_reaction("✅")  # adding a reaction
	await ctx.send("Successfully disconnected.")

	# clearing queues and loops
	if ctx.guild.id in queues:
		del queues[ctx.guild.id]
	if ctx.guild.id in queues_info:
		del queues_info[ctx.guild.id]
	if ctx.guild.id in loops:
		del loops[ctx.guild.id]
	if ctx.guild.id in now_playing_pos:
		del now_playing_pos[ctx.guild.id]

	print("[log]: Successfully left the channel.")


# stop command
@bot.command(aliases=["stop"])
async def pause(ctx):
	if ctx.voice_client is None:
		return await ctx.send("I am not connected to any voice channels.")

	if ctx.author.voice is None:
		return await ctx.send(f"{ctx.author.mention}, You have to be connected to a voice channel.")

	if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
		return await ctx.send("You are in the wrong channel.")

	ctx.voice_client.pause()  # stopping a music
	await ctx.message.add_reaction("✅")  # adding a reaction
	await ctx.send("⏸️ Successfully paused.")
	print("[log]: Successfully paused song.")


# continue command
@bot.command(aliases=["continue", "unpause"])
async def resume(ctx):
	if ctx.voice_client is None:
		return await ctx.send("I am not connected to any voice channels.")

	if ctx.author.voice is None:
		return await ctx.send(f"{ctx.author.mention}, You have to be connected to a voice channel.")

	if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
		return await ctx.send("You are in the wrong channel.")

	ctx.voice_client.resume()  # resume music
	await ctx.message.add_reaction("✅")  # adding a reaction
	await ctx.send("▶️ Successfully resumed.")
	print("[log]: Successfully unpaused song.")


# queue command
@bot.command(aliases=["q"])
async def queue(ctx):
	global queues_info

	# if queue is empty, sending empty embed
	if ctx.voice_client is None:
		await ctx.send(embed=discord.Embed(title="Current Queue", description="Your current queue is empty!", color=0x515596))
	else:
		position = 0
		if ctx.guild.id in queues_info:
			# splitting the queue into queues of 10 songs
			array = []
			arr = queues_info[ctx.guild.id]
			while len(arr) > 10:
				pice = queues_info[ctx.guild.id][:10]
				arr.append(pice)
				arr = queues_info[ctx.guild.id][10:]
			array.append(arr)
			queue_info = array
		else:
			return await ctx.send(embed=discord.Embed(
				title="Current Queue",
				description="Your current queue is empty!",
				color=0x515596)
			)
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

		# sending the entire queue of 10 songs for each message
		for songs in content:
			if content.index(songs) == 0:
				await ctx.send(embed=discord.Embed(title="Current Queue", description=songs, color=0x515596))
			else:
				await ctx.send(embed=discord.Embed(description=songs, color=0x515596))


# loop command
@bot.command()
async def loop(ctx):
	global loops

	if ctx.voice_client is None:
		return await ctx.send("I am not connected to any voice channels.")

	if ctx.author.voice is None:
		return await ctx.send(f"{ctx.author.mention}, You have to be connected to a voice channel.")

	if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
		return await ctx.send("You are in the wrong channel.")

	# sending a message depending on whether is loop turned on or off
	if ctx.guild.id not in loops or not loops[ctx.guild.id]:
		await ctx.message.add_reaction("✅")  # adding a reaction
		await ctx.send("Loop enabled!")
		loops[ctx.guild.id] = True
		print("[log]: Successfully enabled loop.")
	else:
		await ctx.message.add_reaction("✅")  # adding a reaction
		await ctx.send("Loop disabled!")
		del loops[ctx.guild.id]
		print("[log]: Successfully disabled loop.")


if __name__ == "__main__":
	bot.run(token)  # bot launch
