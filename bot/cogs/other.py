from nextcord.ext.commands import Bot, Cog

from bot.misc import Config, SpotifyWrapper


class __MainOtherCog(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self) -> None:
        await SpotifyWrapper.init()
        print(f'🎵 Beat v{Config.BOT_VERSION} launched!')


def register_other_cogs(bot: Bot) -> None:
    bot.add_cog(__MainOtherCog(bot))
