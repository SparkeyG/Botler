#!/usr/bin/python3
import os
import asyncio
import logging
import sys
import traceback

import typing

import d20
import discord
from discord.ext import commands

from dotenv import load_dotenv
load_dotenv(verbose=True)

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

bot = commands.Bot(command_prefix='$')

# -- COGS --
COGS = [ "bot.recording" ]

desc = '''
Botler is a discord RP utility bot that will facilitate LARP
RP on a discord server.
<Info on commands and inviting to a server to come later>
'''

log_formatter = logging.Formatter('%(levelname)s:%(name)s: %(message)s')
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(log_formatter)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)
log = logging.getLogger('botler')

@bot.event
async def on_ready():
    log.info('We have logged in as:')
    log.info(bot.user.name)
    log.info(bot.user.id)
    log.info('---------')
    for guild in bot.guilds:
        log.info(f'{guild.name}(id: {guild.id})')

@bot.event
async def on_resumed():
    log.info('resumed')

@bot.event
async def on_command_error(ctx, error):
    log.warning("Error caused by message: `{}`".format(ctx.message.content))
    for line in traceback.format_exception(type(error), error, error.__traceback__):
        log.warning(line)


for cog in COGS:
    log.info(f'Loading cog: {cog}')
    bot.load_extension(cog)

if __name__ == '__main__':
    log.info(f'Starting to run')
    bot.run(TOKEN)
