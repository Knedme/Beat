from nextcord import slash_command, Interaction, Embed, ButtonStyle, Message
from nextcord.ui import View, Button
from nextcord.ext.commands import Cog, Bot
from random import shuffle

from bot.misc import Config, GuildPlayData, LoopState


class QueueCommandsCog(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @slash_command(name='now-playing', description='Shows what track is playing now.', dm_permission=False)
    async def now_playing_command(self, interaction: Interaction) -> None:
        play_data = GuildPlayData.get_play_data(interaction.guild_id)
        if play_data is None:
            await interaction.send(embed=Embed(title='🎵 Current song',
                                               description='Nothing is playing right now.', color=Config.EMBED_COLOR))
            return

        try:
            cur_song = play_data.queue[play_data.cur_song_pos]
        except IndexError:
            await interaction.send('An unexpected error has occurred. Try using the command again.')
            return

        await interaction.send(embed=Embed(title='🎵 Current song',
                                           description=f'[{cur_song.name}]({cur_song.url})', color=Config.EMBED_COLOR))

    @slash_command(name='shuffle', description='Shuffles next songs in the queue.', dm_permission=False)
    async def shuffle_command(self, interaction: Interaction) -> None:
        if interaction.guild.voice_client is None:
            await interaction.send('I am not playing any songs for you.')
            return

        if interaction.user.voice is None:
            await interaction.send(f'{interaction.user.mention}, You have to be connected to a voice channel.')
            return

        if interaction.user.voice.channel.id != interaction.guild.voice_client.channel.id:
            await interaction.send('You are in the wrong channel.')
            return

        play_data = GuildPlayData.get_play_data(interaction.guild_id)
        if play_data is None or not len(play_data.queue):
            await interaction.send('Your queue is empty!')
            return

        # getting the next and previous songs from the queue
        next_songs = play_data.queue[play_data.cur_song_pos+1:]
        previous_songs = play_data.queue[:play_data.cur_song_pos+1]

        if len(next_songs) <= 1:
            await interaction.send('Not enough songs to shuffle.')
            return

        # unique shuffling next songs
        shuffled_next_songs = next_songs.copy()
        while shuffled_next_songs == next_songs:
            shuffle(shuffled_next_songs)

        play_data.queue = previous_songs + shuffled_next_songs  # replacing the queue
        await interaction.send('✅ Next songs were successfully shuffled.')

    @slash_command(name='queue', description='Shows current queue of songs.', dm_permission=False)
    async def queue_command(self, interaction: Interaction) -> None:
        play_data = GuildPlayData.get_play_data(interaction.guild_id)
        if play_data is None or not len(play_data.queue):
            await interaction.send(embed=Embed(
                title='Current Queue',
                description='Your current queue is empty!',
                color=Config.EMBED_COLOR))
            return

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
                        f'({queue_item.url}){" ⟵ current track" if pos-1 == play_data.cur_song_pos else ""}\n'
                pos += 1
            pages.append(page_text)

        additional_info = f'🎶 Total tracks: {len(play_data.queue)}\n' \
                          f'🔁 Queue loop: {"enabled" if play_data.loop == LoopState.QUEUE else "disabled"} | ' \
                          f'🔁 Current track loop: {"enabled" if play_data.loop == LoopState.TRACK else "disabled"}'
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
        await interaction.send(embed=Embed(
            title='Current Queue',
            description=pages[cur_page-1],
            color=Config.EMBED_COLOR
        ).set_footer(text=f'📄 Page {cur_page}/{len(pages)} | ' + additional_info), view=view)
