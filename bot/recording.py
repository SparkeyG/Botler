from discord import Member, User, Colour, Embed, utils, Message, TextChannel
from discord.ext.commands import Cog, Context, command, group, Bot
import typing as t
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pprint import pprint
import os
import yaml

from dotenv import load_dotenv
load_dotenv(verbose=True)

UserObj = t.Union[Member, User]
def send_msg(bcc, to, subject, body):
    msg= MIMEMultipart()
    msg['From'] = os.getenv('EMAIL_USERNAME')
    msg['To']   = to
    msg['Bcc']  = bcc
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    s = smtplib.SMTP(host=os.getenv('EMAIL_HOST'), port=os.getenv('EMAIL_PORT'))
    s.starttls()
    s.login(os.getenv('EMAIL_USERNAME'),os.getenv('EMAIL_PASSWORD'))
    s.send_message(msg)

class Recording(Cog):
    """These commands will assist in recording and sending logs of a room's
    messages. They will also clean a room
    More documentation can be found at: https://sparkeyg.github.io/Botler
    """
    def __init__(self, bot):
        self.bot = bot
        self._recording_channels = {}
        self._message_log = {}
        self._time_fmt_str = '%Y-%m-%d %H:%M:%S UTC '
        with open('email.yaml') as file:
            self._email_list = yaml.load(file, Loader=yaml.FullLoader)

    @command(name='record_start')
    async def msg_record(self, ctx):
        """ $record_start is used to signal the bot to start recording
        $record_start
        """
        recording_requester = ctx.author.display_name
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
    async def msg_room_clean(self, ctx, *, send_to=None):
        """ $room_clean is used to erase the whole room
        You may send the room's contents to an email address
        $room_clean
        $room_clean test@test.com
        """
        channel = ctx.channel.id
        async with ctx.channel.typing():
            email_msg = f"This is a chat log from the {ctx.guild.name} discord server\n"
            email_msg = email_msg + f"\tThis occured in the {ctx.channel.name} channel\n"
            start = False
            async for msg in ctx.channel.history(limit=None,
                                                 oldest_first=True):
                msg_time = msg.created_at.strftime(self._time_fmt_str)
                email_msg = email_msg + f"{msg.author.name}({msg.author.display_name}) @ {msg_time} : {msg.clean_content}\n";

            if send_to:
                sent_to = self._email_list[ctx.guild.id]['email-bcc']
            send_msg(bcc=self._email_list[ctx.guild.id]['email-bcc'],
                     to=send_to,subject='Discord Chat Log', body=email_msg)
            deleted = await ctx.channel.purge(oldest_first=True,
                                              bulk=True,
                                              limit=4000000,
                                              check=is_pinned_message,
                                              before=ctx.message)
            await ctx.channel.send('Chat log sent and messages purged')
            await ctx.channel.send(f"\tremoved {len(deleted)} message(s)")
            self._message_log[channel] = None


    @command(name='record_send')
    async def msg_log_send(self, ctx, *, send_to=None):
        """ $record_send is used to stop recording and send to one or more email
        addresses. The room will then be cleared of non-pinned messages
        $record_send test@test.com
        $record_send test@test.com, bob@test.com

        """
        channel = ctx.channel.id
        if send_to is None:
            await ctx.channel.send('Chat log cannot be sent, please try again and add a receipent')
        else:
            async with ctx.channel.typing():
                email_msg = f"This is a chat log from the {ctx.guild.name} discord server\n"
                email_msg = email_msg + f"\tThis occured in the {ctx.channel.name} channel\n"
                # TODO: get rid of the recording_channels, only use the search
                if channel in self._recording_channels:
                    for msg in self._message_log[channel]:
                        edited_msg = ''
                        if msg.edited_at:
                            edited_msg = '(edited)'
                        msg_time = msg.created_at.strftime(self._time_fmt_str)
                        email_msg = email_msg + f"{msg.author.name}({msg.author.display_name}) @ {msg_time} : {msg.clean_content} {edited_msg}\n";
                else:
                    start = False
                    async for msg in ctx.channel.history(limit=None,
                                                         oldest_first=True):
                        if not start:
                            if "$record_start" not in msg.content:
                                continue
                            else:
                                start = True
                        msg_time = msg.created_at.strftime(self._time_fmt_str)
                        author_as_member = ctx.guild.get_member(msg.author.id)
                        email_msg = email_msg + f"{author_as_member.name}({author_as_member.nick}) @ {msg_time} : {msg.clean_content}\n";
                    if not start:
                        await ctx.channel.send('Trying to send log w/o $record_start will not send anything. Try $room_clean')
                        return

                send_msg(bcc=self._email_list[ctx.guild.id]['email-bcc'],
                         to=send_to,
                         subject='Discord Chat Log',
                         body=email_msg)
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
