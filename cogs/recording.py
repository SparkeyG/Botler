import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import yaml
from discord import Colour, Embed
from discord.ext import commands

import config


def send_msg(bcc, to, subject, body):
    msg = MIMEMultipart()
    msg["From"] = config.email["username"]
    msg["To"] = to
    msg["Bcc"] = bcc
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    s = smtplib.SMTP(host=config.email["host"], port=config.email["port"])
    s.starttls()
    s.login(config.email["username"], config.email["password"])
    s.send_message(msg)


def is_pinned_message(m):
    return not m.pinned


def chunk(lst):
    for i in range(0, len(lst), 100):
        yield lst[i:i+100]


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
        self._date_fmt_str = "%Y-%m-%d"
        self._time_fmt_str = "%H:%M:%S UTC "
        Recording.not_configured_embed = Embed(
            description="It appears that I am new here.\n"
            f"Please have an admin run `{bot.command_prefix}change_bcc_email` to receive logs\n"
            "Recording cannot start without it",
            colour=Colour(0x880000),
        )

        with open("email.yaml") as file:
            Recording._email_list = yaml.load(file, Loader=yaml.FullLoader)

    @commands.Cog.listener()
    @is_configured()
    async def on_guild_join(self, guild):
        await guild.system_channel.send("Hello, I am a friendly bot to manage rooms.")
        await guild.system_channel.send("For more information, `$help` to get more info,")
        if guild.id not in Recording._email_list:
            await guild.system_channel.send(embed=Recording.not_configured_embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.channel.id in self._recording_channels:
            self._message_log[message.channel.id].append(message)

    @commands.command(name="change_bcc_email", hidden=True)
    async def change_bcc_email(self, ctx, *, bcc_email=None):
        """$change_bcc_email is used to set/change the bcc email address
        $change_bcc_email admin@test.com
        """
        change_requestor = ctx.author
        has_admin_rights = change_requestor.guild_permissions.administrator
        if not has_admin_rights:
            await ctx.channel.send("You are not an admin and cannot do that")
        elif not bcc_email:
            await ctx.channel.send("You need to supply the address to use")
        else:
            if ctx.guild.id not in Recording._email_list:
                Recording._email_list[ctx.guild.id] = {}
            Recording._email_list[ctx.guild.id]["email-bcc"] = bcc_email
            with open("email.yaml", "w") as file:
                yaml.dump(Recording._email_list, file)
            await ctx.channel.send("Setting the email-bcc for this server")
    """
    @commands.command(name="flood_room", hidden=True)
    @is_configured()
    async def flood_room(self, ctx):
        for i in range(0, 120):
            await ctx.channel.send(f'flooding {i}')
    """

    @commands.command(name="record_start")
    @is_configured()
    async def msg_record(self, ctx):
        """$record_start is used to signal the bot to start recording
        $record_start
        """
        recording_requester = ctx.author.display_name
        recording_channel = ctx.channel
        await ctx.send(f"{recording_requester} asked for {recording_channel.name} to be recorded")

    @commands.command(name="record_send")
    @is_configured()
    async def msg_log_send(self, ctx, *, send_to=None):
        """$record_send is used to stop recording and send to one or more email
        addresses. The room will then be cleared of non-pinned messages
        $record_send test@test.com
        $record_send test@test.com, bob@test.com

        """
        if send_to is None:
            await ctx.channel.send("Chat log cannot be sent, please try again and add a receipent")
            return

        async with ctx.channel.typing():
            first_msg = False
            async for message in ctx.channel.history(limit=None, oldest_first=True):
                if "$record_start" in message.content:
                    first_msg = message
                    break
            if not first_msg:
                await ctx.channel.send("Trying to send log w/o $record_start will not send anything. Try $room_clean")
                return
            await self._send_and_clean(first=first_msg, last=ctx.message, send_to=send_to, ctx=ctx)

    @commands.command(name="room_clean")
    @is_configured()
    async def msg_room_clean(self, ctx, *, send_to=None):
        """$room_clean is used to erase the whole room
        You may send the room's contents to an email address
        $room_clean
        $room_clean test@test.com
        """
        first_msg = False

        async with ctx.channel.typing():
            async for msg in ctx.channel.history(limit=1, oldest_first=True):
                first_msg = msg
            if not send_to:
                send_to = self._email_list[ctx.guild.id]["email-bcc"]
            await self._send_and_clean(first=first_msg, last=ctx.message, send_to=send_to, ctx=ctx)

    async def _send_and_clean(self, first, last, send_to, ctx):
        # TODO: variable checking
        now = datetime.now()
        date_time = now.strftime(self._date_fmt_str)
        room_name = ""
        if ctx.channel.category is not None:
            room_name = f"{ctx.channel.category}/{ctx.channel.name}"
        else:
            room_name = ctx.channel.name
        email_subject = f"Discord Chat Log: {ctx.guild.name} - {room_name} - {date_time}"
        email_msg = f"This is a chat log from the {ctx.guild.name} discord server\n"
        email_msg = email_msg + f"\tThis occured in the {ctx.channel.name} channel\n"
        msg_count = 1
        msg_list = []
        email_msg, last_name, last_date = await self._append_message(ctx, email_msg, first, '', '')
        async for message in ctx.channel.history(limit=None, after=first, before=last, oldest_first=True):
            if message.pinned:
                continue
            email_msg, last_name, last_date = await self._append_message(ctx, email_msg, message, last_date, last_name)
            msg_list.append(message)
            msg_count += 1
        email_msg, author_name, msg_date = await self._append_message(ctx, email_msg, last, last_date, last_name)
        send_msg(bcc=self._email_list[ctx.guild.id]["email-bcc"], to=send_to, subject=email_subject, body=email_msg)
        await ctx.channel.send("Chat log has been sent")
        await ctx.channel.send("I will now delete messages")
        if not first.pinned:
            await first.delete()
        await last.delete()
        # for msgs_chunk in chunk(msg_list):
        # await ctx.channel.delete_messages(msgs_chunk)
        # await ctx.channel.send(f"Messages purged: removed {len(msg_list)} message(s)")
        deleted = await ctx.channel.purge(
            oldest_first=True, bulk=True, limit=msg_count,
            check=is_pinned_message, after=first, before=last
        )
        await ctx.channel.send(f"Messages purged: removed {len(deleted)} message(s)")

    async def _append_message(self, ctx, email_msg, message, last_date, last_name):
        display_name = ""
        edited_msg = ""
        author_name = message.author.name
        msg_date = message.created_at.strftime(self._date_fmt_str)
        if msg_date != last_date:
            email_msg = email_msg + f"Message date is {msg_date}"
        if author_name == last_name:
            prefix_string = "                                     "
        else:
            author_as_member = ctx.guild.get_member(message.author.id)
            if author_as_member:
                display_name = author_as_member.nick
            else:
                display_name = message.author.display_name
            msg_time = message.created_at.strftime(self._time_fmt_str)
            prefix_string = f"\n{author_name!s:<10.10}({display_name!s:^10.10}) @ {msg_time!s:<12.12}"
        if message.edited_at:
            edited_msg = "(edited)"
        email_msg = email_msg + f"{prefix_string} : {message.clean_content} {edited_msg}\n"
        for attachment in message.attachments:
            email_msg = email_msg + f"{attachment.url}"
        last_name = author_name
        last_date = msg_date
        return email_msg, last_name, last_date


def setup(bot):
    bot.add_cog(Recording(bot))
