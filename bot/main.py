from nextcord import Intents, Status, Activity, ActivityType
from nextcord.ext.commands import Bot
from asyncio import run

from bot.misc import Env, Config, SpotifyWrapper
from bot.cogs import register_all_cogs


def start_bot():
    bot = Bot(intents=Intents.default(),
              status=Status.online,
              activity=Activity(type=ActivityType.listening, name=f'/commands | v{Config.BOT_VERSION}'))
    register_all_cogs(bot)

    bot.run(Env.TOKEN)
    run(SpotifyWrapper.close())  # closing the SpotifyWrapper when the bot has stopped
