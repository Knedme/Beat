from nextcord import slash_command, Interaction, SlashOption
from nextcord.ext.commands import Cog, Bot

from bot.misc import GuildPlayData


class ControlCog(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @slash_command(name='skip', description='Skips current song.', dm_permission=False)
    async def skip_command(self, interaction: Interaction):
        vc = interaction.guild.voice_client
        play_data = GuildPlayData.get_play_data(interaction.guild_id)
        if play_data is None or not len(play_data.queue) or vc is None:
            return await interaction.send('I am not playing any songs for you.')

        if interaction.user.voice is None:
            return await interaction.send(f'{interaction.user.mention}, You have to be connected to a voice channel.')

        if interaction.user.voice.channel.id != vc.channel.id:
            return await interaction.send('You are in the wrong channel.')

        # actually skip a song if it's looped
        if play_data.loop:
            play_data.cur_song_idx += 1

        vc.stop()
        await interaction.send('✅ Successfully skipped.')

    @slash_command(name='skip-to', description='Skips to a specific position in the queue.', dm_permission=False)
    async def skip_to_command(self, interaction: Interaction,
                              position: int = SlashOption(description='Position in the queue.', required=True)):
        vc = interaction.guild.voice_client
        play_data = GuildPlayData.get_play_data(interaction.guild_id)
        if play_data is None or not len(play_data.queue) or vc is None:
            return await interaction.send('I am not playing any songs for you.')

        if interaction.user.voice is None:
            return await interaction.send(f'{interaction.user.mention}, You have to be connected to a voice channel.')

        if interaction.user.voice.channel.id != interaction.guild.voice_client.channel.id:
            return await interaction.send('You are in the wrong channel.')

        if position <= 0 or position > len(play_data.queue):
            return await interaction.send('The specified position is out of the queue.')

        play_data.target_song_idx = position - 1
        interaction.guild.voice_client.stop()
        await interaction.send(f'✅ Successfully skipped to a position: `{position}`.')

    @slash_command(name='pause', description='Pauses current song.', dm_permission=False)
    async def pause_command(self, interaction: Interaction):
        vc = interaction.guild.voice_client
        if vc is None:
            return await interaction.send('I am not playing any songs for you.')

        if interaction.user.voice is None:
            return await interaction.send(f'{interaction.user.mention}, You have to be connected to a voice channel.')

        if interaction.user.voice.channel.id != vc.channel.id:
            return await interaction.send('You are in the wrong channel.')

        vc.pause()
        await interaction.send('⏸️ Successfully paused.')

    @slash_command(name='resume', description='Resumes current song if it is paused.', dm_permission=False)
    async def resume_command(self, interaction: Interaction):
        vc = interaction.guild.voice_client
        if vc is None:
            return await interaction.send('I am not playing any songs for you.')

        if interaction.user.voice is None:
            return await interaction.send(f'{interaction.user.mention}, You have to be connected to a voice channel.')

        if interaction.user.voice.channel.id != vc.channel.id:
            return await interaction.send('You are in the wrong channel.')

        vc.resume()
        await interaction.send('▶️ Successfully resumed.')

    @slash_command(name='leave', description='Leaves the voice channel.', dm_permission=False)
    async def leave_command(self, interaction: Interaction):
        vc = interaction.guild.voice_client
        if vc is None:
            return await interaction.send('I am not connected to any channel.')

        if interaction.user.voice is None:
            return await interaction.send(f'{interaction.user.mention}, You have to be connected to a voice channel.')

        if interaction.user.voice.channel.id != vc.channel.id:
            return await interaction.send('You are in the wrong channel.')

        await vc.disconnect()
        await interaction.send('✅ Successfully disconnected.')

    @slash_command(name='loop', description='Enables/Disables current track loop.', dm_permission=False)
    async def loop_command(self, interaction: Interaction):
        play_data = GuildPlayData.get_play_data(interaction.guild_id)
        if play_data is None or not len(play_data.queue) or interaction.guild.voice_client is None:
            return await interaction.send('I am not playing any songs for you.')

        if interaction.user.voice is None:
            return await interaction.send(f'{interaction.user.mention}, You have to be connected to a voice channel.')

        if interaction.user.voice.channel.id != interaction.guild.voice_client.channel.id:
            return await interaction.send('You are in the wrong channel.')

        if not play_data.loop:
            play_data.loop = True
            await interaction.send('🔂 Current track loop enabled!')
        else:
            play_data.loop = False
            await interaction.send('❎ Current track loop disabled!')

    @slash_command(name='loop-queue', description='Enables/Disables queue loop.', dm_permission=False)
    async def loop_queue_command(self, interaction: Interaction):
        play_data = GuildPlayData.get_play_data(interaction.guild_id)
        if play_data is None or not len(play_data.queue) or interaction.guild.voice_client is None:
            return await interaction.send('I am not playing any songs for you.')

        if interaction.user.voice is None:
            return await interaction.send(f'{interaction.user.mention}, You have to be connected to a voice channel.')

        if interaction.user.voice.channel.id != interaction.guild.voice_client.channel.id:
            return await interaction.send('You are in the wrong channel.')

        if not play_data.loop_queue:
            play_data.loop_queue = True
            await interaction.send('🔁 Queue loop enabled!')
        else:
            play_data.loop_queue = False
            await interaction.send('❎ Queue loop disabled!')

    @slash_command(name='replay', description='Resets the progress of the current playing song.')
    async def replay_command(self, interaction: Interaction):
        vc = interaction.guild.voice_client
        play_data = GuildPlayData.get_play_data(interaction.guild_id)
        if play_data is None or not len(play_data.queue) or vc is None:
            return await interaction.send('I am not playing any songs for you.')

        if interaction.user.voice is None:
            return await interaction.send(f'{interaction.user.mention}, You have to be connected to a voice channel.')

        if interaction.user.voice.channel.id != vc.channel.id:
            return await interaction.send('You are in the wrong channel.')

        play_data.target_song_idx = play_data.cur_song_idx
        vc.stop()
        await interaction.send('✅ Successfully replayed.')

    @slash_command(name='replay-queue', description='Resets the progress of the current queue.')
    async def replay_queue_command(self, interaction: Interaction):
        vc = interaction.guild.voice_client
        play_data = GuildPlayData.get_play_data(interaction.guild_id)
        if play_data is None or not len(play_data.queue) or vc is None:
            return await interaction.send('I am not playing any songs for you.')

        if interaction.user.voice is None:
            return await interaction.send(f'{interaction.user.mention}, You have to be connected to a voice channel.')

        if interaction.user.voice.channel.id != vc.channel.id:
            return await interaction.send('You are in the wrong channel.')

        play_data.target_song_idx = 0
        vc.stop()
        await interaction.send('✅ Successfully replayed current queue.')
