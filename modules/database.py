# Base Modules for Bot
import discord
import asyncio
from discord.ext import commands
import traceback
import sys

#Misc. Modules
import datetime
import config as cfg


class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def query(self, ctx, query: str, readOrWrite: str):
        if (readOrWrite not in ["r", "w", "read", "write", "Read", "Write"]):
            await ctx.send(f"{ctx.author.mention} entered an invalid Read/Write value or {readOrWrite}")
            return
        if (readOrWrite in ["r", "read", "Read"]):
            readOrWrite = "Read"
        if(readOrWrite in ["w", "write", "Write"]):
            readOrWrite = "Write"

        await ctx.send("Are you sure you would like to perform the following? If yes, react with a Thumbs Up. Otherwise, reacting with a Thumbs Down")
        embed = discord.Embed(
            title=f"CustomQueryInfo \U0000270d", colour=discord.Colour(0xFFA500))
        embed.set_footer(text=f"Ticketer | {cfg.authorname}")
        #embed.set_thumbnail(url = self.bot.user.avatar_url)
        embed.add_field(name="Query:", value=f"`{query}`")
        embed.add_field(name="Type:", value=f"`{readOrWrite}`")
        message = await ctx.send(embed=embed)
        await message.add_reaction("\U0001f44d")
        await message.add_reaction("\U0001f44e")

        def reactioncheck(reaction, user):
            validreactions = ["\U0001f44d", "\U0001f44e"]
            return user.id == ctx.author.id and reaction.emoji in validreactions
        reaction, user = await self.bot.wait_for('reaction_add', check=reactioncheck, timeout=30)
        # Check if thumbs up
        if reaction.emoji != "\U0001f44d":
            await ctx.send("Command Cancelled")
            return
        if (readOrWrite == "Read"):
            try:
                result = await self.bot.db.fetch(query)
                result = result[0]
                for key, value in result.items():
                    embed = discord.Embed(
                        title=f"Success \U00002705", colour=discord.Colour(0x32CD32))
                    embed.set_footer(text=f"Ticketer | {cfg.authorname}")
                    #embed.set_thumbnail(url = self.bot.user.avatar_url)
                    embed.add_field(name="Key|Value:",
                                    value=f"`{key}`|`{value}`")
                    await ctx.send(embed=embed)
            except:
                await self.bot.sendError(ctx, f"Your query returned `None` or was an invalid query.")
        else:
            try:
                await self.bot.db.execute(query)
                await self.bot.sendSuccess(ctx, f"The command was executed succesfully.")
            except:
                await self.bot.sendError(ctx, f"Your query was invalid.")
    

def setup(bot):
    bot.add_cog(Database(bot))
