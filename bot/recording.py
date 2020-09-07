from discord import Member, User, Colour, Embed, utils, Message, TextChannel
from discord.ext.commands import Cog, Context, command, group, Bot
import typing as t
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import os
from dotenv import load_dotenv
load_dotenv(verbose=True)

UserObj = t.Union[Member, User]

def send_msg(to, subject, body):
    msg= MIMEMultipart()
    msg['From'] = os.getenv('EMAIL_USERNAME')
    msg['To']   = to
    msg['Bcc']  = os.getenv('EMAIL_BCC')
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    s = smtplib.SMTP(host=os.getenv('EMAIL_HOST'), port=os.getenv('EMAIL_PORT'))
    s.starttls()
    s.login(os.getenv('EMAIL_USERNAME'),os.getenv('EMAIL_PASSWORD'))
    s.send_message(msg)

class Recording(Cog):
    def __init__(self, bot):
        self.bot = bot
        self._recording_channels = {}
        self._message_log = {}

    @command(name='record_start')
    async def msg_record(self, ctx):
        recording_requester = ctx.author.name
        recording_channel = ctx.channel
        self._recording_channels[recording_channel.id] = {'channel': recording_channel.name,
                                                          'request': recording_requester}
        self._message_log[recording_channel.id] = []
        await ctx.send(f'{recording_requester} asked for {recording_channel.name} to be recorded')

    @Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.channel.id in self._recording_channels:
            self._message_log[message.channel.id].append(message)

    @command(name='record_send')
    async def msg_log_send(self, ctx, *, send_to='shawn.c.carroll@gmail.com'):
        channel = ctx.channel.id
        if channel in self._recording_channels:
            async with ctx.channel.typing():
                email_msg = f"This is a chat log from the {ctx.guild.name} discord server\n"
                email_msg = email_msg + f"\tThis occured in the {ctx.channel.name} channel\n"
                for msg in self._message_log[channel]:
                    msg_time = msg.created_at.strftime('%Y-%m-%d %H:%M:%S ')
                    email_msg = email_msg + f"{msg.author.name}({msg.author.nick}) @ {msg_time} : {msg.content}\n";
                send_msg(to=send_to,subject='Discord Chat Log', body=email_msg)
                deleted = await ctx.channel.purge(oldest_first=True,
                                                  bulk=True,
                                                  limit=4000000,
                                                  check=is_pinned_message,
                                                  before=ctx.message)
                await ctx.channel.send('Chat log sent and messages purged')
                await ctx.channel.send(f"\tremoved {len(deleted)} message(s)")
                self._message_log[channel] = None

def is_pinned_message(m):
    return not m.pinned

def setup(bot: Bot) -> None:
    bot.add_cog(Recording(bot))
