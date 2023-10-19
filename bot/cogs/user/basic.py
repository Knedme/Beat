from nextcord import slash_command, Interaction, Embed
from nextcord.ext.commands import Cog, Bot
from math import isnan, isinf

from bot.misc import Config


class BasicCog(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @slash_command(name='info', description='Information about the bot.')
    async def info_command(self, interaction: Interaction):
        embed = Embed(title=f'Information about {Config.BOT_NAME}', color=Config.EMBED_COLOR)
        embed.add_field(name='Server count:', value=f'🔺 `{len(self.bot.guilds)}`', inline=False)
        embed.add_field(name='Bot version:', value=f'✨ `{Config.BOT_VERSION}`', inline=False)
        embed.add_field(name='The bot is written on:', value='🐍 `Nextcord`', inline=False)
        embed.add_field(name='Bot created by:', value='🔶 `Knedme`', inline=False)
        embed.add_field(name='GitHub repository:', value='📕 [Click Here](https://github.com/Knedme/Beat)')
        embed.set_thumbnail(url=Config.BOT_LOGO_URL)
        embed.set_footer(text=f'v{Config.BOT_VERSION} | Write /commands for the command list.')
        await interaction.send(embed=embed)

    @slash_command(name='commands', description='Shows a list of commands')
    async def commands_command(self, interaction: Interaction):
        embed = Embed(
            title=f'{Config.BOT_NAME} commands',
            color=Config.EMBED_COLOR)
        embed.add_field(name='/join', value='The bot joins to your voice channel.', inline=False)
        embed.add_field(
            name='/play _youtube-video-link | spotify-link | search-query_',
            value='The bot joins to your voice channel and plays music from a link or search query.',
            inline=False)
        embed.add_field(name='/lofi', value='The bot joins to your channel and plays lofi.', inline=False)
        embed.add_field(name='/leave', value='Leave the voice channel.', inline=False)
        embed.add_field(name='/clear', value='Clears the entire queue and also disables all loops.')
        embed.add_field(name='/skip', value='Skips current song.', inline=False)
        embed.add_field(name='/skip-to _position_', value='Skips to a specific position in the queue.', inline=False)
        embed.add_field(name='/pause', value='Pauses current song.', inline=False)
        embed.add_field(name='/resume', value='Resumes current song if it is paused.', inline=False)
        embed.add_field(name='/queue', value='Shows current queue.', inline=False)
        embed.add_field(name='/now-playing', value='Shows what song is playing now.', inline=False)
        embed.add_field(name='/loop', value='Enables/Disables current track loop.', inline=False)
        embed.add_field(name='/loop-queue', value='Enables/Disables queue loop.', inline=False)
        embed.add_field(name='/replay', value='Resets the progress of the current playing song.', inline=False)
        embed.add_field(name='/replay-queue', value='Resets the progress of the current queue.', inline=False)
        embed.add_field(name='/remove _position_', value='Removes the specified song from the queue.')
        embed.add_field(name='/move _pos-from_ _pos-to_',
                        value='Moves the specified song to another position in the queue.', inline=False)
        embed.add_field(name='/shuffle', value='Shuffles the entire queue.', inline=False)
        embed.add_field(name='/latency', value='Checks bot\'s response time to Discord.', inline=False)
        embed.add_field(name='/commands', value='Shows a list of commands.', inline=False)
        embed.add_field(name='/info', value='Shows information about the bot.')
        embed.set_footer(text=f'v{Config.BOT_VERSION}')
        await interaction.send(embed=embed)

    @slash_command(
        name='latency',
        description='Checks bot\'s response time to Discord.',
        dm_permission=False)
    async def latency_command(self, interaction: Interaction):
        bot_latency = self.bot.latency
        if isnan(bot_latency):  # bot latency can be NaN
            return await interaction.send('Couldn\'t get the latency.')
        info = f'Bot latency is: **`{round(bot_latency * 1000)}ms`**'

        vc = interaction.guild.voice_client
        if vc is not None:
            vc_latency = vc.latency
            if not isinf(vc_latency):  # vc latency can be infinite
                info += f'\nAudio latency is: **`{round(vc_latency * 1000)}ms`**'

        await interaction.send(info)
