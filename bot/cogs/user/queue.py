from discord import slash_command, ApplicationContext, Interaction, Embed, ButtonStyle, Message, Option
from discord.ui import View, Button
from discord.ext.commands import Cog, Bot
from random import shuffle
from bot.misc import Config, GuildPlayData


class QueueCog(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @slash_command(name='now-playing', description='Shows what track is playing now.', dm_permission=False)
    async def now_playing_command(self, ctx: ApplicationContext):
        play_data = GuildPlayData.get_play_data(ctx.guild_id)
        if play_data is None:
            return await ctx.respond(embed=Embed(title='🎵 Current song',
                                                 description='Nothing is playing right now.', color=Config.EMBED_COLOR))

        try:
            cur_song = play_data.queue[play_data.cur_song_idx]
        except IndexError:
            return await ctx.respond('An unexpected error has occurred. Try using the command again.')

        await ctx.respond(embed=Embed(title='🎵 Current song',
                                      description=f'[{cur_song.name}]({cur_song.url})', color=Config.EMBED_COLOR))

    @slash_command(name='shuffle', description='Shuffles the entire queue.', dm_permission=False)
    async def shuffle_command(self, ctx: ApplicationContext):
        vc = ctx.guild.voice_client
        play_data = GuildPlayData.get_play_data(ctx.guild_id)
        if play_data is None or not len(play_data.queue) or vc is None:
            return await ctx.respond('I am not playing any songs for you.')

        if ctx.user.voice is None:
            return await ctx.respond(f'{ctx.user.mention}, You have to be connected to a voice channel.')

        if ctx.user.voice.channel.id != vc.channel.id:
            return await ctx.respond('You are in the wrong channel.')

        if len(play_data.queue) <= 2:
            return await ctx.respond('Not enough songs in queue to shuffle.')

        # saving the current song, as it should always be the first song in the shuffled queue
        cur_song = play_data.queue[play_data.cur_song_idx]

        songs = play_data.queue.copy()
        songs.pop(play_data.cur_song_idx)

        # unique shuffling the songs
        cp = songs.copy()
        while songs == cp:
            shuffle(songs)

        songs.insert(0, cur_song)  # current song is now in shuffled queue and it's first
        play_data.cur_song_idx = 0

        play_data.queue = songs  # replacing the queue
        await ctx.respond('✅ The queue was successfully shuffled.')

    @slash_command(
        name='move',
        description='Moves the specified song to another position in the queue.',
        dm_permission=False)
    async def move_command(self, ctx: ApplicationContext,
                           pos_from: Option(int, description='Position of the song in the queue.', required=True),
                           pos_to: Option(int, description='Position where you want to place the song.', required=True)):
        vc = ctx.guild.voice_client
        play_data = GuildPlayData.get_play_data(ctx.guild_id)
        if play_data is None or not len(play_data.queue) or vc is None:
            return await ctx.respond('I am not playing any songs for you.')

        if ctx.user.voice is None:
            return await ctx.respond(f'{ctx.user.mention}, You have to be connected to a voice channel.')

        if ctx.user.voice.channel.id != vc.channel.id:
            return await ctx.respond('You are in the wrong channel.')

        if pos_from <= 0 or pos_from > len(play_data.queue)\
                or pos_to <= 0 or pos_to > len(play_data.queue):
            return await ctx.respond('One or both of the specified positions are out of the queue.')

        if pos_from == pos_to:
            return await ctx.respond('The positions can\'t be equal.')

        pos_from_idx = pos_from - 1
        pos_to_idx = pos_to - 1

        play_data.queue.insert(pos_to_idx, play_data.queue.pop(pos_from_idx))  # moving the song

        # changing the current pos if needed
        if pos_to_idx <= play_data.cur_song_idx < pos_from_idx:
            play_data.cur_song_idx += 1
        elif pos_from_idx < play_data.cur_song_idx <= pos_to_idx:
            play_data.cur_song_idx -= 1
        elif pos_from_idx == play_data.cur_song_idx:
            play_data.cur_song_idx = pos_to_idx

        await ctx.respond(f'✅ Successfully moved the song from position `{pos_from}` to position `{pos_to}`.')

    @slash_command(
        name='remove',
        description='Removes the specified song from the queue.',
        dm_permission=False)
    async def remove_command(self, ctx: ApplicationContext,
                             position: Option(int, description='Position of the song in the queue.', required=True)):
        vc = ctx.guild.voice_client
        play_data = GuildPlayData.get_play_data(ctx.guild_id)
        if play_data is None or not len(play_data.queue) or vc is None:
            return await ctx.respond('I am not playing any songs for you.')

        if ctx.user.voice is None:
            return await ctx.respond(f'{ctx.user.mention}, You have to be connected to a voice channel.')

        if ctx.user.voice.channel.id != vc.channel.id:
            return await ctx.respond('You are in the wrong channel.')

        if position <= 0 or position > len(play_data.queue):
            return await ctx.respond('The specified position is out of the queue.')

        index = position - 1
        if index > play_data.cur_song_idx:
            play_data.queue.pop(index)
        elif index < play_data.cur_song_idx:
            play_data.queue.pop(index)
            play_data.cur_song_idx -= 1
        else:
            play_data.queue.pop(index)
            play_data.target_song_idx = play_data.cur_song_idx
            vc.stop()

        await ctx.respond(f'✅ Successfully removed the song with a position: `{position}`.')

    @slash_command(
        name='clear',
        description='Clears the entire queue and also disables all loops.',
        dm_permission=False)
    async def clear_command(self, ctx: ApplicationContext) -> None:
        vc = ctx.guild.voice_client
        play_data = GuildPlayData.get_play_data(ctx.guild_id)
        if play_data is None or not len(play_data.queue) or vc is None:
            return await ctx.respond('I am not playing any songs for you.')

        if ctx.user.voice is None:
            return await ctx.respond(f'{ctx.user.mention}, You have to be connected to a voice channel.')

        if ctx.user.voice.channel.id != vc.channel.id:
            return await ctx.respond('You are in the wrong channel.')

        GuildPlayData.remove_play_data(ctx.guild_id)
        ctx.guild.voice_client.stop()
        await ctx.respond('✅ Successfully cleared the queue.')

    @slash_command(name='queue', description='Shows current queue of songs.', dm_permission=False)
    async def queue_command(self, ctx: ApplicationContext):
        play_data = GuildPlayData.get_play_data(ctx.guild_id)
        if play_data is None or not len(play_data.queue):
            return await ctx.respond(embed=Embed(
                title='Current Queue',
                description='Your current queue is empty!',
                color=Config.EMBED_COLOR))

        # splitting the queue into arrays of 15 songs
        divided_queue = play_data.queue
        arrays = []
        while len(divided_queue) > 15:
            piece = divided_queue[:15]
            arrays.append(piece)
            divided_queue = divided_queue[15:]
        arrays.append(divided_queue)
        divided_queue = arrays

        pages = []
        pos = 1

        # filling each page with song titles, their positions in queue, etc.
        for arr in divided_queue:
            page_text = ''
            for queue_item in arr:
                page_text +=\
                        f'{pos}. [{queue_item.name[:97] + "..." if len(queue_item.name) > 100 else queue_item.name}]' \
                        f'({queue_item.url}){" ⟵ current track" if pos-1 == play_data.cur_song_idx else ""}\n'
                pos += 1
            pages.append(page_text)

        additional_info = f'🎶 Total tracks: {len(play_data.queue)}\n' \
                          f'🔁 Queue loop: {"enabled" if play_data.loop_queue else "disabled"} | ' \
                          f'🔂 Current track loop: {"enabled" if play_data.loop else "disabled"}'
        cur_page = 1

        async def update(btn_interaction_msg: Message):
            await btn_interaction_msg.edit(
                embed=Embed(title='Current Queue', description=pages[cur_page-1], color=Config.EMBED_COLOR)
                .set_footer(text=f'📄 Page {cur_page}/{len(pages)} | ' + additional_info))

        async def previous_page_btn_callback(btn_interaction: Interaction) -> None:
            nonlocal cur_page
            if cur_page > 1:
                cur_page -= 1
            await update(btn_interaction.message)
            await btn_interaction.response.defer()

        async def next_page_btn_callback(btn_interaction: Interaction) -> None:
            nonlocal cur_page
            if cur_page < len(pages):
                cur_page += 1
            await update(btn_interaction.message)
            await btn_interaction.response.defer()

        async def first_page_btn_callback(btn_interaction: Interaction) -> None:
            nonlocal cur_page
            cur_page = 1
            await update(btn_interaction.message)
            await btn_interaction.response.defer()

        async def last_page_btn_callback(btn_interaction: Interaction) -> None:
            nonlocal cur_page
            cur_page = len(pages)
            await update(btn_interaction.message)
            await btn_interaction.response.defer()

        previous_page_btn = Button(style=ButtonStyle.primary, emoji='⬅')
        next_page_btn = Button(style=ButtonStyle.primary, emoji='➡')
        first_page_btn = Button(style=ButtonStyle.primary, emoji='⏪')
        last_page_btn = Button(style=ButtonStyle.primary, emoji='⏩')

        previous_page_btn.callback = previous_page_btn_callback
        next_page_btn.callback = next_page_btn_callback
        first_page_btn.callback = first_page_btn_callback
        last_page_btn.callback = last_page_btn_callback

        view = View()
        view.add_item(previous_page_btn)
        view.add_item(next_page_btn)
        view.add_item(first_page_btn)
        view.add_item(last_page_btn)

        # sending a message starting from the first page of the queue
        await ctx.respond(embed=Embed(
            title='Current Queue',
            description=pages[cur_page-1],
            color=Config.EMBED_COLOR
        ).set_footer(text=f'📄 Page {cur_page}/{len(pages)} | ' + additional_info), view=view)
