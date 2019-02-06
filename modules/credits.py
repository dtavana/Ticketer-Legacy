# Base Modules for Bot
import discord
import asyncio
from discord.ext import commands
import traceback

# Misc. Modules
import datetime
import config as cfg

class Credits:
    def __init__(self, bot):
        self.bot = bot

    async def premium_admins(ctx):
        admins = [112762841173368832]
        return ctx.author.id in admins
    
    @commands.check(premium_admins)
    @commands.command(hidden=True)
    async def giftpremium(self, ctx, user: discord.Member, amount = 1):
        embed = discord.Embed(
            title=f"Premium Gift \U0000270d", colour=discord.Colour(0xFFA500))
        embed.set_footer(text=f"Ticketer | {cfg.authorname}")
        embed.add_field(name="User:", value=f"{user.mention}")
        embed.add_field(name="Amount:", value=f"**{amount}**")
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
        
        try:
            await self.bot.db.execute("INSERT INTO premium (userid, credits) VALUES ($1, $2);", user.id, amount)
            
        except:
            await self.bot.db.execute("UPDATE premium SET credits = credits + $1 WHERE userid = $2;", amount, user.id)

        newcredits = await self.bot.db.fetchrow("SELECT credits FROM premium WHERE userid = $1;", user.id)
        newcredits = newcredits['credits']

        embed = discord.Embed(
            title=f"Success \U00002705", colour=discord.Colour(0x32CD32))
        embed.set_footer(text="PGServerManager | TwiSt#2791")
        embed.add_field(name="Data:", value=f"{user.mention} now has {newcredits} premium credits.")
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Credits(bot))
