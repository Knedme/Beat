from discord import slash_command, ApplicationContext, Option
from discord.ext.commands import Cog, Bot
from bot.misc import GuildPlayData


class ControlCog(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @slash_command(name='skip', description='Skips current song.', dm_permission=False)
    async def skip_command(self, ctx: ApplicationContext):
        vc = ctx.guild.voice_client
        play_data = GuildPlayData.get_play_data(ctx.guild_id)
        if play_data is None or not len(play_data.queue) or vc is None:
            return await ctx.respond('I am not playing any songs for you.')

        if ctx.user.voice is None:
            return await ctx.respond(f'{ctx.user.mention}, You have to be connected to a voice channel.')

        if ctx.user.voice.channel.id != vc.channel.id:
            return await ctx.respond('You are in the wrong channel.')

        # actually skip a song if it's looped
        if play_data.loop:
            play_data.cur_song_idx += 1

        vc.stop()
        await ctx.respond('✅ Successfully skipped.')

    @slash_command(name='skip-to', description='Skips to a specific position in the queue.', dm_permission=False)
    async def skip_to_command(self, ctx: ApplicationContext,
                              position: Option(int, description='Position in the queue.', required=True)):
        vc = ctx.guild.voice_client
        play_data = GuildPlayData.get_play_data(ctx.guild_id)
        if play_data is None or not len(play_data.queue) or vc is None:
            return await ctx.respond('I am not playing any songs for you.')

        if ctx.user.voice is None:
            return await ctx.respond(f'{ctx.user.mention}, You have to be connected to a voice channel.')

        if ctx.user.voice.channel.id != ctx.guild.voice_client.channel.id:
            return await ctx.respond('You are in the wrong channel.')

        if position <= 0 or position > len(play_data.queue):
            return await ctx.respond('The specified position is out of the queue.')

        play_data.target_song_idx = position - 1
        ctx.guild.voice_client.stop()
        await ctx.respond(f'✅ Successfully skipped to a position: `{position}`.')

    @slash_command(name='pause', description='Pauses current song.', dm_permission=False)
    async def pause_command(self, ctx: ApplicationContext):
        vc = ctx.guild.voice_client
        if vc is None:
            return await ctx.respond('I am not playing any songs for you.')

        if ctx.user.voice is None:
            return await ctx.respond(f'{ctx.user.mention}, You have to be connected to a voice channel.')

        if ctx.user.voice.channel.id != vc.channel.id:
            return await ctx.respond('You are in the wrong channel.')

        vc.pause()
        await ctx.respond('⏸️ Successfully paused.')

    @slash_command(name='resume', description='Resumes current song if it is paused.', dm_permission=False)
    async def resume_command(self, ctx: ApplicationContext):
        vc = ctx.guild.voice_client
        if vc is None:
            return await ctx.respond('I am not playing any songs for you.')

        if ctx.user.voice is None:
            return await ctx.respond(f'{ctx.user.mention}, You have to be connected to a voice channel.')

        if ctx.user.voice.channel.id != vc.channel.id:
            return await ctx.respond('You are in the wrong channel.')

        vc.resume()
        await ctx.respond('▶️ Successfully resumed.')

    @slash_command(name='leave', description='Leaves the voice channel.', dm_permission=False)
    async def leave_command(self, ctx: ApplicationContext):
        vc = ctx.guild.voice_client
        if vc is None:
            return await ctx.respond('I am not connected to any channel.')

        if ctx.user.voice is None:
            return await ctx.respond(f'{ctx.user.mention}, You have to be connected to a voice channel.')

        if ctx.user.voice.channel.id != vc.channel.id:
            return await ctx.respond('You are in the wrong channel.')

        await vc.disconnect()
        await ctx.respond('✅ Successfully disconnected.')

    @slash_command(name='loop', description='Enables/Disables current track loop.', dm_permission=False)
    async def loop_command(self, ctx: ApplicationContext):
        play_data = GuildPlayData.get_play_data(ctx.guild_id)
        if play_data is None or not len(play_data.queue) or ctx.guild.voice_client is None:
            return await ctx.respond('I am not playing any songs for you.')

        if ctx.user.voice is None:
            return await ctx.respond(f'{ctx.user.mention}, You have to be connected to a voice channel.')

        if ctx.user.voice.channel.id != ctx.guild.voice_client.channel.id:
            return await ctx.respond('You are in the wrong channel.')

        if not play_data.loop:
            play_data.loop = True
            await ctx.respond('🔂 Current track loop enabled!')
        else:
            play_data.loop = False
            await ctx.respond('❎ Current track loop disabled!')

    @slash_command(name='loop-queue', description='Enables/Disables queue loop.', dm_permission=False)
    async def loop_queue_command(self, ctx: ApplicationContext):
        play_data = GuildPlayData.get_play_data(ctx.guild_id)
        if play_data is None or not len(play_data.queue) or ctx.guild.voice_client is None:
            return await ctx.respond('I am not playing any songs for you.')

        if ctx.user.voice is None:
            return await ctx.respond(f'{ctx.user.mention}, You have to be connected to a voice channel.')

        if ctx.user.voice.channel.id != ctx.guild.voice_client.channel.id:
            return await ctx.respond('You are in the wrong channel.')

        if not play_data.loop_queue:
            play_data.loop_queue = True
            await ctx.respond('🔁 Queue loop enabled!')
        else:
            play_data.loop_queue = False
            await ctx.respond('❎ Queue loop disabled!')

    @slash_command(name='replay', description='Resets the progress of the current playing song.')
    async def replay_command(self, ctx: ApplicationContext):
        vc = ctx.guild.voice_client
        play_data = GuildPlayData.get_play_data(ctx.guild_id)
        if play_data is None or not len(play_data.queue) or vc is None:
            return await ctx.respond('I am not playing any songs for you.')

        if ctx.user.voice is None:
            return await ctx.respond(f'{ctx.user.mention}, You have to be connected to a voice channel.')

        if ctx.user.voice.channel.id != vc.channel.id:
            return await ctx.respond('You are in the wrong channel.')

        play_data.target_song_idx = play_data.cur_song_idx
        vc.stop()
        await ctx.respond('✅ Successfully replayed.')

    @slash_command(name='replay-queue', description='Resets the progress of the current queue.')
    async def replay_queue_command(self, ctx: ApplicationContext):
        vc = ctx.guild.voice_client
        play_data = GuildPlayData.get_play_data(ctx.guild_id)
        if play_data is None or not len(play_data.queue) or vc is None:
            return await ctx.respond('I am not playing any songs for you.')

        if ctx.user.voice is None:
            return await ctx.respond(f'{ctx.user.mention}, You have to be connected to a voice channel.')

        if ctx.user.voice.channel.id != vc.channel.id:
            return await ctx.respond('You are in the wrong channel.')

        play_data.target_song_idx = 0
        vc.stop()
        await ctx.respond('✅ Successfully replayed current queue.')
