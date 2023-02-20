from nextcord import slash_command, Interaction, Embed
from nextcord.ext.commands import Cog, Bot

from bot.misc import Config


class BasicCommandsCog(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @slash_command(name='info', description='Information about the bot.')
    async def info_command(self, interaction: Interaction) -> None:
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
    async def commands_command(self, interaction: Interaction) -> None:
        embed = Embed(
            title=f'{Config.BOT_NAME} commands',
            color=Config.EMBED_COLOR)
        embed.add_field(name='/join', value='The bot joins to your voice channel.', inline=False)
        embed.add_field(
            name='/play youtube-video-link | spotify-link | search-query',
            value='The bot joins to your voice channel and plays music from a link or search query.',
            inline=False)
        embed.add_field(name='/lofi', value='The bot joins to your channel and plays lofi.', inline=False)
        embed.add_field(name='/leave', value='Leave the voice channel.', inline=False)
        embed.add_field(name='/skip', value='Skips current song.', inline=False)
        embed.add_field(name='/pause', value='Pauses current song.', inline=False)
        embed.add_field(name='/resume', value='Resumes current song if it is paused.', inline=False)
        embed.add_field(name='/queue', value='Shows current queue.', inline=False)
        embed.add_field(name='/now-playing', value='Shows what song is playing now.', inline=False)
        embed.add_field(name='/loop', value='Enables/Disables Queue/Track loop.', inline=False)
        embed.add_field(name='/shuffle', value='Shuffles next songs in the queue.', inline=False)
        embed.add_field(name='/support', value='Shows support contact.', inline=False)
        embed.add_field(name='/commands', value='Shows a list of commands.', inline=False)
        embed.add_field(name='/info', value='Shows information about the bot.')
        embed.set_footer(text=f'v{Config.BOT_VERSION}')
        await interaction.send(embed=embed)

    @slash_command(name='support', description='Shows support contact.')
    async def support_command(self, interaction: Interaction) -> None:
        await interaction.send(embed=Embed(
            title='Support',
            description='If you have any problems, please write here: `supknedme@yandex.com`',
            color=Config.EMBED_COLOR))
