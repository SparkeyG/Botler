from discord import Member, User, Colour, Embed, utils, Message, TextChannel
from discord.ext import commands
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
    msg = MIMEMultipart()
    msg['From'] = os.getenv('EMAIL_USERNAME')
    msg['To'] = to
    msg['Bcc'] = bcc
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    s = smtplib.SMTP(host=os.getenv('EMAIL_HOST'),
                     port=os.getenv('EMAIL_PORT'))
    s.starttls()
    s.login(os.getenv('EMAIL_USERNAME'), os.getenv('EMAIL_PASSWORD'))
    s.send_message(msg)


def is_pinned_message(m):
    return not m.pinned


def is_configured():
    async def predicate(ctx):
        if ctx.guild.id not in Recording._email_list:
            await ctx.send(embed=Recording.not_configured_embed)
            return False
        else:
            return True

    return commands.check(predicate)


class Recording(commands.Cog):
    """These commands will assist in recording and sending logs of a room's
    messages. They will also clean a room
    More documentation can be found at: https://sparkeyg.github.io/Botler
    """
    _email_list = None
    not_configured_embed = None

    def __init__(self, bot):
        self.bot = bot
        self._recording_channels = {}
        self._message_log = {}
        self._time_fmt_str = '%Y-%m-%d %H:%M:%S UTC '
        Recording.not_configured_embed= Embed(
            description="It appears that I am new here.\n"
            f"Please have an admin run `{bot.command_prefix}change_bcc_email` to receive logs\n"
            'Recording cannot start without it',
            colour=Colour(0x880000),
        )

        with open('email.yaml') as file:
            Recording._email_list = yaml.load(file, Loader=yaml.FullLoader)

    @commands.Cog.listener()
    @is_configured()
    async def on_guild_join(self, guild):
        await guild.system_channel.send(
            'Hello, I am a friendly bot to manage rooms.')
        await guild.system_channel.send(
            'For more information, `$help` to get more info,')
        if guild.id not in Recording._email_list:
            await guild.system_channel.send(embed=Recording.not_configured_embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.channel.id in self._recording_channels:
            self._message_log[message.channel.id].append(message)

    @commands.command(name='change_bcc_email', hidden=True)
    async def change_bcc_email(self, ctx, *, bcc_email=None):
        """ $change_bcc_email is used to set/change the bcc email address
        $change_bcc_email admin@test.com
        """
        change_requestor = ctx.author
        has_admin_rights = change_requestor.guild_permissions.administrator
        if not has_admin_rights:
            await ctx.channel.send('You are not an admin and cannot do that')
        elif not bcc_email:
            await ctx.channel.send('You need to supply the address to use')
        else:
            if ctx.guild.id not in Recording._email_list:
                Recording._email_list[ctx.guild.id] = {}
            Recording._email_list[ctx.guild.id]['email-bcc'] = bcc_email
            with open('email.yaml', 'w') as file:
                yaml.dump(Recording._email_list, file)
                # TODO all cogs need to know to reread yaml....
            await ctx.channel.send('Setting the email-bcc for this server')

    @commands.command(name='record_start')
    @is_configured()
    async def msg_record(self, ctx):
        """ $record_start is used to signal the bot to start recording
        $record_start
        """
        recording_requester = ctx.author.display_name
        recording_channel = ctx.channel
        await ctx.send(
            f'{recording_requester} asked for {recording_channel.name} to be recorded'
        )

    @commands.command(name='record_send')
    @is_configured()
    async def msg_log_send(self, ctx, *, send_to=None):
        """ $record_send is used to stop recording and send to one or more email
        addresses. The room will then be cleared of non-pinned messages
        $record_send test@test.com
        $record_send test@test.com, bob@test.com

        """
        channel = ctx.channel.id
        if send_to is None:
            await ctx.channel.send(
                'Chat log cannot be sent, please try again and add a receipent'
            )
        else:
            start = False
            async with ctx.channel.typing():
                email_msg = f"This is a chat log from the {ctx.guild.name} discord server\n"
                email_msg = email_msg + f"\tThis occured in the {ctx.channel.name} channel\n"
                async for msg in ctx.channel.history(limit=None,
                                                     oldest_first=True):
                    if not start:
                        if "$record_start" not in msg.content:
                            continue
                        else:
                            start = msg
                            await msg.delete()
                    edited_msg = ''
                    if msg.edited_at:
                        edited_msg = '(edited)'
                    msg_time = msg.created_at.strftime(self._time_fmt_str)
                    author_as_member = ctx.guild.get_member(msg.author.id)
                    email_msg = email_msg + f"{author_as_member.name}({author_as_member.nick}) @ {msg_time} : {msg.clean_content} {edited_msg}\n"
                if not start:
                    await ctx.channel.send(
                        'Trying to send log w/o $record_start will not send anything. Try $room_clean'
                    )
                    return

                send_msg(bcc=self._email_list[ctx.guild.id]['email-bcc'],
                         to=send_to,
                         subject='Discord Chat Log',
                         body=email_msg)
                deleted = await ctx.channel.purge(oldest_first=True,
                                                  bulk=True,
                                                  limit=4000000,
                                                  check=is_pinned_message,
                                                  before=ctx.message,
                                                  after=start)
                await ctx.message.delete()
                await ctx.channel.send('Chat log sent and messages purged')
                await ctx.channel.send(f"\tremoved {len(deleted)} message(s)")
                self._message_log[channel] = None

    @commands.command(name='room_clean')
    @is_configured()
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
            first_msg = False
            async for msg in ctx.channel.history(limit=None,
                                                 oldest_first=True):
                if not first_msg:
                    first_msg = msg
                msg_time = msg.created_at.strftime(self._time_fmt_str)
                email_msg = email_msg + f"{msg.author.name}({msg.author.display_name}) @ {msg_time} : {msg.clean_content}\n"

            if send_to:
                sent_to = self._email_list[ctx.guild.id]['email-bcc']
            send_msg(bcc=self._email_list[ctx.guild.id]['email-bcc'],
                     to=send_to,
                     subject='Discord Chat Log',
                     body=email_msg)
            deleted = await ctx.channel.purge(oldest_first=True,
                                              bulk=True,
                                              limit=4000000,
                                              check=is_pinned_message,
                                              after=first_msg,
                                              before=ctx.message)
            await ctx.channel.send('Chat log sent and messages purged')
            await ctx.channel.send(f"\tremoved {len(deleted)} message(s)")
            self._message_log[channel] = None


def setup(bot):
    bot.add_cog(Recording(bot))
