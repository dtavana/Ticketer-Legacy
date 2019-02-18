# Base Modules for Bot
import discord
import asyncio
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
import traceback
import sys

# Misc. Modules
import datetime
import config as cfg

class Credits:
    def __init__(self, bot):
        self.bot = bot

    async def premium_admins(ctx):
        admins = [112762841173368832]
        return ctx.author.id in admins
    
    @commands.command()
    async def redeem(self, ctx):
        try:
            sufficient = await self.bot.db.fetchrow("SELECT credits >= 1 AS sufficient FROM premium WHERE userid = $1;", ctx.author.id)
            sufficient = sufficient['sufficient']
        except:
            prefix = await self.bot.getPrefix(ctx.guild.id)
            await self.bot.sendError(ctx, f"{ctx.author.mention} has no credits to redeem.\n\nUse {prefix}support for a link to our support server to pruchase premium!")
            return
        
        hasPremium = await self.bot.db.fetchrow("SELECT premium FROM servers WHERE serverid = $1;", ctx.guild.id)
        hasPremium = hasPremium['premium']
        if sufficient:
            if not hasPremium:
                await ctx.send("Are you sure you would like to perform the following? If yes, react with a Thumbs Up. Otherwise, reacting with a Thumbs Down")
                embed = discord.Embed(title=f"Redeem Premium \U0000270d", colour=discord.Colour(0xFFA500))
                embed.set_footer(text=f"Ticketer | {cfg.authorname}")
                embed.add_field(name="Server:", value=f"`{ctx.author.guild}`")
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
                await self.bot.db.fetchrow("UPDATE premium SET credits = credits - 1 WHERE userid = $1;", ctx.author.id)
                await self.bot.db.execute("DELETE from premium WHERE credits <= 0 AND userid = $1;", ctx.author.id)
                await self.bot.db.execute("UPDATE servers SET premium = TRUE WHERE serverid = $1;", ctx.guild.id)
                prefix = await self.bot.getPrefix(ctx.guild.id)
                await self.bot.sendSuccess(ctx, f"`{ctx.guild}` now has premium enabled! Rerun `{prefix}setup` in order to utilize premium fully!\n\nThank you for using Ticketer.")
            else:
                await self.bot.sendError(ctx, f"`{ctx.guild}` already has premium enabled!")
        else:
            prefix = await self.bot.getPrefix(ctx.guild.id)
            await self.bot.sendError(f"{ctx.author.mention} has no credits to redeem.\n\nUse {prefix}support for a link to our support server to pruchase premium!")
    
    @commands.cooldown(1, 60, BucketType.user)
    @commands.command()
    async def credits(self, ctx):
        prefix = await self.bot.getPrefix(ctx.guild.id)
        try:
            credit = await self.bot.db.fetchrow("SELECT credits from premium WHERE userid = $1;", ctx.author.id)
            credit = credit['credits']
            await self.bot.sendSuccess(ctx, f"{ctx.author.mention} has {credit} credit(s).\n\n Use `{prefix}redeem` to redeem your premium credit(s).")
        except:
            await self.bot.sendError(ctx, f"{ctx.author.mention} has no credit(s).\n\n Use `{prefix}upgrade` to learn how to upgrade.")
    
    @commands.check(premium_admins)
    @commands.command(hidden=True)
    async def giftpremium(self, ctx, user: discord.Member, amount = 1):
        await ctx.send("Are you sure you would like to perform the following? If yes, react with a Thumbs Up. Otherwise, reacting with a Thumbs Down")
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
        await self.bot.sendSuccess(ctx, f"{user.mention} has received {amount} credits and now has {newcredits} credits.")
    
    @credits.error
    async def credits_handler(self, ctx, error):
        import traceback
        traceback.print_exception(type(error), error, error.__traceback__)
        if isinstance(error, commands.CommandOnCooldown):
            seconds = error.retry_after
            seconds = round(seconds, 2)
            hours, remainder = divmod(int(seconds), 3600)
            minutes, seconds = divmod(remainder, 60)
            await ctx.send(f"You are on cooldown! Please try again in **{seconds} seconds**")

def setup(bot):
    bot.add_cog(Credits(bot))
