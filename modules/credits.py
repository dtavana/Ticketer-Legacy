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

class Credits(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def premium_admins(ctx):
        admins = [112762841173368832]
        return ctx.author.id in admins
    
    @commands.command()
    @commands.guild_only()
    async def withdraw(self, ctx):
        """Withdraws premium for a server and gives the user their credit back. **NOTE:** can only be run by the user that redeemed premium"""
        prefix = await self.bot.getPrefix(ctx.guild.id)
        hasPremium = await self.bot.db.fetchrow("SELECT premium FROM servers WHERE serverid = $1;", ctx.guild.id)
        hasPremium = hasPremium['premium']
        if hasPremium:
            premium_owner = await self.bot.get_premiumowner(ctx.guild.id)
            if premium_owner != 0:
                premium_owner = ctx.guild.get_member(premium_owner)
            else:
                premium_owner = ctx.author
            if ctx.author != premium_owner:
                return await self.bot.sendError(ctx, f"Only the user that redeemed premium for this server may run this command.", ctx.message, ctx.guild)
            await self.bot.db.execute("UPDATE servers SET premium = False WHERE serverid = $1;", ctx.guild.id)
            try:
                await self.bot.db.execute("INSERT INTO premium (userid, credits) VALUES ($1, 1);", ctx.author.id) 
            except:
                await self.bot.db.execute("UPDATE premium SET credits = credits + 1 WHERE userid = $1;", ctx.author.id)
            await self.bot.sendSuccess(ctx, f"{ctx.author.mention} has gained a credit and this server has lost premium.", ctx.message, ctx.guild)
        else:
            await self.bot.sendError(ctx, f"This server currently does not have premium enabled. Please use the `{prefix}upgrade` command to get more information about premium.", ctx.message, ctx.guild)

    @commands.command()
    async def transfer(self, ctx, target: discord.Member, amount: int = 1):
        """Transfer a premium credit to a friend"""
        try:
            sufficient = await self.bot.db.fetchrow("SELECT credits >= $1 AS sufficient FROM premium WHERE userid = $2;", amount, ctx.author.id)
            sufficient = sufficient['sufficient']
            if sufficient == False:
                prefix = await self.bot.getPrefix(ctx.guild.id)
                return await self.bot.sendError(ctx, f"{ctx.author.mention} does not have enough credits to transfer **{amount}**.\n\nUse {prefix}credits to view your current credits!", ctx.message, ctx.guild)
        except:
            prefix = await self.bot.getPrefix(ctx.guild.id)
            return await self.bot.sendError(ctx, f"{ctx.author.mention} has no credits to transfer.\n\nUse {prefix}upgrade to buy a premium credit or vote for us on DBL!", ctx.message, ctx.guild)
        try:
            await self.bot.db.execute("INSERT INTO premium (userid, credits) VALUES ($1, $2);", target.id, amount) 
        except:
            await self.bot.db.execute("UPDATE premium SET credits = credits + $1 WHERE userid = $2;", amount, target.id)
        await self.bot.db.execute("UPDATE premium SET credits = credits - $1 WHERE userid = $2;", amount, ctx.author.id)
        await self.bot.sendSuccess(ctx, f"{ctx.author.mention} has given {target.mention} **{amount} credits**.", ctx.message, ctx.guild)
        

    
    @commands.command()
    @commands.guild_only()
    async def redeem(self, ctx):
        """Redeem a premium credit to the current server. Use the `upgrade` command for more info on getting premium"""
        try:
            sufficient = await self.bot.db.fetchrow("SELECT credits >= 1 AS sufficient FROM premium WHERE userid = $1;", ctx.author.id)
            sufficient = sufficient['sufficient']
        except:
            prefix = await self.bot.getPrefix(ctx.guild.id)
            await self.bot.sendError(ctx, f"{ctx.author.mention} has no credits to redeem.\n\nUse {prefix}support for a link to our support server to purchase premium!", ctx.message, ctx.guild)
            return
        hasPremium = await self.bot.db.fetchrow("SELECT premium FROM servers WHERE serverid = $1;", ctx.guild.id)
        hasPremium = hasPremium['premium']
        if sufficient:
            if not hasPremium:
                initQuestion = await ctx.send("Are you sure you would like to perform the following? If yes, react with a Thumbs Up. Otherwise, reacting with a Thumbs Down")
                embed = discord.Embed(title=f"Redeem Premium \U0000270d", colour=discord.Colour(0xFFA500))
                embed.set_footer(text=f"Ticketer | {cfg.authorname}")
                #embed.set_thumbnail(url = self.bot.user.avatar_url)
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
                    return await self.bot.sendError(ctx, "Command Cancelled", [ctx.message, initQuestion, message], ctx.guild)
                await self.bot.db.fetchrow("UPDATE premium SET credits = credits - 1 WHERE userid = $1;", ctx.author.id)
                await self.bot.db.execute("DELETE from premium WHERE credits <= 0 AND userid = $1;", ctx.author.id)
                await self.bot.db.execute("UPDATE servers SET premium = TRUE, userid = $1 WHERE serverid = $2;", ctx.author.id, ctx.guild.id)
                prefix = await self.bot.getPrefix(ctx.guild.id)
                await self.bot.sendSuccess(ctx, f"`{ctx.guild}` now has premium enabled! Take a look at `{prefix}help` under the settings category in order to utilize premium fully!\n\nThank you for using Ticketer.", [ctx.message, initQuestion, message], ctx.guild)
            else:
                await self.bot.sendError(ctx, f"`{ctx.guild}` already has premium enabled!", ctx.message, ctx.guild)
        else:
            prefix = await self.bot.getPrefix(ctx.guild.id)
            await self.bot.sendError(f"{ctx.author.mention} has no credits to redeem.\n\nUse {prefix}support for a link to our support server to pruchase premium!", ctx.message, ctx.guild)
    
    @commands.cooldown(1, 60, BucketType.user)
    @commands.command()
    async def vote(self, ctx):
        """Displays a link to vote on has on DBL"""
        await self.bot.sendSuccess(ctx, f"[Click here to vote for me](https://discordbots.org/bot/542709669211275296/vote)", ctx.message, ctx.guild)
        
    @commands.cooldown(1, 60, BucketType.user)
    @commands.command()
    async def votes(self, ctx):
        """Displays the current amount of votes one has on DBL"""
        prefix = await self.bot.getPrefix(ctx.guild.id)
        try:
            votes = await self.bot.db.fetchrow("SELECT count from votes WHERE userid = $1;", ctx.author.id)
            votes = votes['count']
            await self.bot.sendSuccess(ctx, f"{ctx.author.mention} has **{votes} vote(s)** for me on DBL.\n\n Use `{prefix}vote` to vote for me to receive a premium credit.", ctx.message, ctx.guild)
        except:
            await self.bot.sendError(ctx, f"{ctx.author.mention} has no vote(s).\n\n Use `{prefix}vote` to vote for me on DBL.", ctx.message, ctx.guild)
    
    @commands.cooldown(1, 60, BucketType.user)
    @commands.command()
    async def credits(self, ctx):
        """Displays the current amount of credits one has"""
        prefix = await self.bot.getPrefix(ctx.guild.id)
        try:
            credit = await self.bot.db.fetchrow("SELECT credits from premium WHERE userid = $1;", ctx.author.id)
            credit = credit['credits']
            await self.bot.sendSuccess(ctx, f"{ctx.author.mention} has {credit} credit(s).\n\n Use `{prefix}redeem` to redeem your premium credit(s).", ctx.message, ctx.guild)
        except:
            await self.bot.sendError(ctx, f"{ctx.author.mention} has no credit(s).\n\n Use `{prefix}upgrade` to learn how to upgrade.", ctx.message, ctx.guild)
    
    @commands.check(premium_admins)
    @commands.command(hidden=True)
    async def giftpremium(self, ctx, target: discord.Member, amount = 1):
        initQuestion = await ctx.send("Are you sure you would like to perform the following? If yes, react with a Thumbs Up. Otherwise, reacting with a Thumbs Down")
        embed = discord.Embed(
            title=f"Premium Gift \U0000270d", colour=discord.Colour(0xFFA500))
        embed.set_footer(text=f"Ticketer | {cfg.authorname}")
        #embed.set_thumbnail(url = self.bot.user.avatar_url)
        embed.add_field(name="User:", value=f"{target.mention}")
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
            return await self.bot.sendError(ctx, "Command Cancelled", [ctx.message, initQuestion, message], ctx.guild)
        try:
            await self.bot.db.execute("INSERT INTO premium (userid, credits) VALUES ($1, $2);", target.id, amount) 
        except:
            await self.bot.db.execute("UPDATE premium SET credits = credits + $1 WHERE userid = $2;", amount, target.id)

        newcredits = await self.bot.db.fetchrow("SELECT credits FROM premium WHERE userid = $1;", target.id)
        newcredits = newcredits['credits']
        await self.bot.sendSuccess(ctx, f"{target.mention} has received {amount} credits and now has {newcredits} credits.", [ctx.message, initQuestion, message], ctx.guild)
    
    @credits.error
    @votes.error
    async def credits_handler(self, ctx, error):
        import traceback
        traceback.print_exception(type(error), error, error.__traceback__)
        if isinstance(error, commands.CommandOnCooldown):
            seconds = error.retry_after
            seconds = round(seconds, 2)
            hours, remainder = divmod(int(seconds), 3600)
            minutes, seconds = divmod(remainder, 60)
            await self.bot.sendError(ctx, f"You are on cooldown! Please try again in **{seconds} seconds**", ctx.message, ctx.guild)

def setup(bot):
    bot.add_cog(Credits(bot))
