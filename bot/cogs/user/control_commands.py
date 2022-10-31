from nextcord import slash_command, Interaction
from nextcord.ext.commands import Cog, Bot

from bot.misc import GuildPlayData, LoopState


class ControlCommandsCog(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @slash_command(name='skip', description='Skips current song.', dm_permission=False)
    async def skip_command(self, interaction: Interaction) -> None:
        if interaction.guild.voice_client is None:
            await interaction.send('I am not playing any songs for you.')
            return

        if interaction.user.voice is None:
            await interaction.send(f'{interaction.user.mention}, You have to be connected to a voice channel.')
            return

        if interaction.user.voice.channel.id != interaction.guild.voice_client.channel.id:
            await interaction.send('You are in the wrong channel.')
            return

        interaction.guild.voice_client.stop()
        await interaction.send('✅ Successfully skipped.')

    @slash_command(name='pause', description='Pauses current song.', dm_permission=False)
    async def pause_command(self, interaction: Interaction) -> None:
        if interaction.guild.voice_client is None:
            await interaction.send('I am not playing any songs for you.')
            return

        if interaction.user.voice is None:
            await interaction.send(f'{interaction.user.mention}, You have to be connected to a voice channel.')
            return

        if interaction.user.voice.channel.id != interaction.guild.voice_client.channel.id:
            await interaction.send('You are in the wrong channel.')
            return

        interaction.guild.voice_client.pause()
        await interaction.send('⏸️ Successfully paused.')

    @slash_command(name='resume', description='Resumes current song if it is paused.', dm_permission=False)
    async def resume_command(self, interaction: Interaction) -> None:
        if interaction.guild.voice_client is None:
            await interaction.send('I am not playing any songs for you.')
            return

        if interaction.user.voice is None:
            await interaction.send(f'{interaction.user.mention}, You have to be connected to a voice channel.')
            return

        if interaction.user.voice.channel.id != interaction.guild.voice_client.channel.id:
            await interaction.send('You are in the wrong channel.')
            return

        interaction.guild.voice_client.resume()
        await interaction.send('▶️ Successfully resumed.')

    @slash_command(name='leave', description='Leaves the voice channel.', dm_permission=False)
    async def leave_command(self, interaction: Interaction) -> None:
        if interaction.guild.voice_client is None:
            await interaction.send('I am not connected to any channel.')
            return

        if interaction.user.voice is None:
            await interaction.send(f'{interaction.user.mention}, You have to be connected to a voice channel.')
            return

        if interaction.user.voice.channel.id != interaction.guild.voice_client.channel.id:
            await interaction.send('You are in the wrong channel.')
            return

        await interaction.guild.voice_client.disconnect()
        await interaction.send('✅ Successfully disconnected.')

    @slash_command(name='loop', description='Enables/Disables Queue/Track loop.', dm_permission=False)
    async def loop_command(self, interaction: Interaction) -> None:
        play_data = GuildPlayData.get_play_data(interaction.guild_id)
        if play_data is None or interaction.guild.voice_client is None:
            await interaction.send('I am not playing any songs for you.')
            return

        if interaction.user.voice is None:
            await interaction.send(f'{interaction.user.mention}, You have to be connected to a voice channel.')
            return

        if interaction.user.voice.channel.id != interaction.guild.voice_client.channel.id:
            await interaction.send('You are in the wrong channel.')
            return

        if play_data.loop == LoopState.NONE:
            play_data.loop = LoopState.QUEUE
            await interaction.send('🔁 Queue loop enabled!')
        elif play_data.loop == LoopState.QUEUE:
            play_data.loop = LoopState.TRACK
            await interaction.send('🔁 Current track loop enabled!')
        else:
            play_data.loop = LoopState.NONE
            await interaction.send('❎ Loop disabled!')
