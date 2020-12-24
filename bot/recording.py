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

    @command(name='room_clean')
    async def msg_room_clean(self, ctx, *, send_to='shawn.c.carroll@gmail.com'):
        channel = ctx.channel.id
        async with ctx.channel.typing():
            email_msg = f"This is a chat log from the {ctx.guild.name} discord server\n"
            email_msg = email_msg + f"\tThis occured in the {ctx.channel.name} channel\n"
            start = False
            async for msg in ctx.channel.history(limit=None,
                                                 oldest_first=True):
                msg_time = msg.created_at.strftime('%Y-%m-%d %H:%M:%S ')
                # TODO: get the author, determine if it is a User or a Member (Members have nicks
                # TODO: get msg.content and parse it for user_ids and replace w/ display_names
                # TODO: use guild.get_member(user_id) to return a member in order to get nick...
                #
                email_msg = email_msg + f"{msg.author.name}({msg.author.display_name}) @ {msg_time} : {msg.content}\n";

            send_msg(to=send_to,subject='Discord Chat Log', body=email_msg)
            deleted = await ctx.channel.purge(oldest_first=True,
                                              bulk=True,
                                              limit=4000000,
                                              check=is_pinned_message,
                                              before=ctx.message)
            await ctx.channel.send('Chat log sent and messages purged')
            await ctx.channel.send(f"\tremoved {len(deleted)} message(s)")
            self._message_log[channel] = None



    @command(name='record_send')
    async def msg_log_send(self, ctx, *, send_to='shawn.c.carroll@gmail.com'):
        channel = ctx.channel.id
        async with ctx.channel.typing():
            email_msg = f"This is a chat log from the {ctx.guild.name} discord server\n"
            email_msg = email_msg + f"\tThis occured in the {ctx.channel.name} channel\n"
            # TODO: get rid of the recording_channels, only use the search
            if channel in self._recording_channels:
                for msg in self._message_log[channel]:
                    msg_time = msg.created_at.strftime('%Y-%m-%d %H:%M:%S ')
                    email_msg = email_msg + f"{msg.author.name}({msg.author.display_name}) @ {msg_time} : {msg.content}\n";
            else:
                start = False
                async for msg in ctx.channel.history(limit=None,
                                                     oldest_first=True):
                    if not start:
                        if "$record_start" not in msg.content:
                            continue
                        else:
                            start = True
                    msg_time = msg.created_at.strftime('%Y-%m-%d %H:%M:%S ')
                    # TODO: get the author, determine if it is a User or a Member (Members have nicks
                    # TODO: get msg.content and parse it for user_ids and replace w/ display_names
                    # TODO: use guild.get_member(user_id) to return a member in order to get nick...
                    #
                    email_msg = email_msg + f"{msg.author.name}({msg.author.display_name}) @ {msg_time} : {msg.content}\n";

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
