from discord import Member, User, Colour, Embed, utils, Message, TextChannel
from discord.ext.commands import Cog, Context, command, group, Bot
import typing as t
import logging
from pprint import pprint
import os
import sys
import yaml

from dotenv import load_dotenv
load_dotenv(verbose=True)


class Room(Cog):
    """These commands will assist with channel managment, with the paradigm
    that each category channel is a building and each channel within a category
    is a room in that building.
    More documentation will be found at: https://sparkeyg.github.io/Botler
    """

    def __init__(self, bot):
        self.bot = bot
        self.building_map = []
        for guild in bot.guilds:
            for room in guild.channel:
                self.building_map.append(f'{guild.name} - {room.category} -> {room.name}')

    @command(name='enter_building', hidden='True')
    async def building_enter(self, ctx, *, building=None):
        building_name = building
        await ctx.send(self.building_map)
        await ctx.send(f"Trying to enter the {building_name}")


def setup(bot: Bot) -> None:
    bot.add_cog(Room(bot))
