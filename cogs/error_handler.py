import logging
import traceback

import discord
from discord.ext import commands

log = logging.getLogger(__name__)


class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.on_command_error = self._on_command_error
        self.client = None

    async def _on_command_error(self, ctx, error, bypass=False):
        if (
            hasattr(ctx.command, "on_error")
            or (ctx.command and hasattr(ctx.cog, f"_{ctx.command.cog_name}__error"))
            and not bypass
        ):
            return
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f"Sorry, I don't understand `{ctx.message.content}`")
            return
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(
                embed=discord.Embed(
                    title="Command Unavailable",
                    description="This command cannot be used in Direct Message.",
                )
            )
        elif isinstance(error, commands.CommandInvokeError):
            log.error(
                f"{error.original.__class__.__name__}: {error.original} (In {ctx.command.name})\n"
                f"Traceback:\n{''.join(traceback.format_tb(error.original.__traceback__))}"
            )
            try:
                await ctx.send(
                    embed=discord.Embed(
                        title="Unknown Error",
                        description="Please report this in the support server.\n"
                        f"```{error.original.__class__.__name__}: {error.original}```",
                    )
                )
            except Exception:
                pass


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
