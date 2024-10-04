from discord.ext.commands import Bot, Cog
from bot.misc import Config, Spotify


class __MainOtherCog(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self) -> None:
        await Spotify.init()
        print(f'🎵 {Config.BOT_NAME} v{Config.BOT_VERSION} launched!')


def register_other_cogs(bot: Bot) -> None:
    bot.add_cog(__MainOtherCog(bot))
