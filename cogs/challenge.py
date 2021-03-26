import typing as t

from discord import Colour, Embed, Member, User
from discord.ext.commands import Bot, Cog, Context, command

from utils import checks

UserObj = t.Union[Member, User]


class Challenge(Cog):
    def __init__(self, bot):
        self.bot = bot
        self._recording_channels = {}
        self._message_log = {}

    @command(name="shotgun", hidden="True")
    @checks.is_owner()
    async def shotgun(self, ctx: Context, *, blast_size: int):
        """Blast a room with messages for testing"""

    @command(name="test", hidden="True")
    async def test(self, ctx):
        channel_embed = Embed(title="Initive Tracker", colour=Colour(0xE5E242), description="Let's get ready to rumble")
        channel_embed.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.avatar_url)
        await ctx.send(embed=channel_embed)


def setup(bot: Bot) -> None:
    bot.add_cog(Challenge(bot))
