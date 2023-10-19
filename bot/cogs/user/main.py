from nextcord.ext.commands import Bot

from bot.cogs.user import BasicCog, MusicCog, ControlCog, QueueCog


def register_user_cogs(bot: Bot) -> None:
    bot.add_cog(BasicCog(bot))
    bot.add_cog(MusicCog(bot))
    bot.add_cog(ControlCog(bot))
    bot.add_cog(QueueCog(bot))
