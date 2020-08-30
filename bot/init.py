from discord import Member, User, Colour, Embed, utils, Message, TextChannel
from discord.ext.commands import Cog, Context, command, group, Bot
import dice
import typing as t

UserObj = t.Union[Member, User]

class Utilities(Cog):
    def __init__(self, bot):
        self.bot = bot
        self._recording_channels = {}

    @command(name='test')
    async def test(self, ctx):
        channel_embed = Embed(
            title='Initive Tracker',
            colour=Colour(0xE5E242),
            description="Let's get ready to rumble"
        )
        channel_embed.set_author(name=self.bot.user.display_name,
                                 icon_url=self.bot.user.avatar_url)
        await ctx.send(embed=channel_embed)

    @command(name='record_start')
    async def msg_record(self, ctx):
        recording_requester = ctx.author.name
        recording_channel = ctx.channel
        self._recording_channels[recording_channel.id] = {'channel': recording_channel,
                                                           'request': recording_requester}
        await ctx.send(f'{recording_requester} asked for {recording_channel} to be recorded')

    @Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        channel = message.channel
        if channel.id in self._recording_channels:
            print(f'This channel is recording, {self._recording_channels[channel.id]}')
            logged_msg = f'{message.guild.name} - {message.channel.name} - {message.author.name} - {message.content}'
            # push self.message_log[channel.id], logged_msg
        await self.bot.process_commands(message)

def setup(bot: Bot) -> None:
    bot.add_cog(Utilities(bot))
