import discord
import asyncio
from discord.ext import commands
import traceback
import sys

#Misc. Modules
import datetime
import config as cfg


class Errors(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if hasattr(ctx.command, 'on_error'):
            return
        ignored = (commands.CommandNotFound, commands.CheckFailure, commands.CommandOnCooldown)
        error = getattr(error, 'original', error)
        if (isinstance(error, ignored)):
            return 
        elif (isinstance(error, commands.MissingRequiredArgument)):
            return await self.bot.sendError(ctx, f"`{error.param.name}` is a missing argument that is required!")
        elif (isinstance(error, commands.BadArgument)):
            return await self.bot.sendError(ctx, f"Invalid argument: `{error}`")
        elif (isinstance(error, commands.DisabledCommand)):
            return await self.bot.sendError(ctx, f'{ctx.command} has been disabled.')
        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

def setup(bot):
    bot.add_cog(Errors(bot))
