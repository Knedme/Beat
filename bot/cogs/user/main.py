from nextcord.ext.commands import Bot

from bot.cogs.user import BasicCommandsCog, MusicCommandsCog, ControlCommandsCog, QueueCommandsCog


def register_user_cogs(bot: Bot) -> None:
    bot.add_cog(BasicCommandsCog(bot))
    bot.add_cog(MusicCommandsCog(bot))
    bot.add_cog(ControlCommandsCog(bot))
    bot.add_cog(QueueCommandsCog(bot))
