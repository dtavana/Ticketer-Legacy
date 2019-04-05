# Base Modules for Bot
import discord
import asyncio
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
import traceback
import sys
import uuid

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
        try:
            hasPremium = await self.bot.db.fetchrow("SELECT key, enabled FROM newpremium WHERE serverid = $1 AND userid = $2;", ctx.guild.id, ctx.author.id)
            key = hasPremium['key']
            hasPremium = hasPremium['enabled']
        except:
            return await self.bot.sendError(ctx, f"This server currently does not have premium enabled. Please use the `{prefix}upgrade` command to get more information about premium.", ctx.message, ctx.guild)
        if hasPremium:
            await self.bot.db.execute("UPDATE newpremium SET enabled = False, serverid = 0 WHERE key = $1;", key)
            await self.bot.sendSuccess(ctx, f"Premium credit `{key}` is now available for use.", ctx.message, ctx.guild)
        else:
            await self.bot.sendError(ctx, f"This server currently does not have premium enabled or this command was run by a user that did not redeem premium. Please use the `{prefix}upgrade` command to get more information about premium.", ctx.message, ctx.guild)

    @commands.command()
    async def transfer(self, ctx, target: discord.Member):
        """Transfer a premium credit to a friend"""
        try:
            sufficient = await self.bot.db.fetchrow("SELECT key FROM newpremium WHERE userid = $1 AND enabled = False;", ctx.author.id)
            if sufficient is not None:
                prefix = await self.bot.getPrefix(ctx.guild.id)
                return await self.bot.sendError(ctx, f"{ctx.author.mention} does not have a credit to transfer.\n\nUse {prefix}credits to view your current credits!", ctx.message, ctx.guild)
        except:
            prefix = await self.bot.getPrefix(ctx.guild.id)
            return await self.bot.sendError(ctx, f"{ctx.author.mention} has no credits to transfer.\n\nUse {prefix}upgrade to buy a premium credit or vote for us on DBL!", ctx.message, ctx.guild)
        
        await self.bot.db.execute("UPDATE newpremium SET userid = $1 WHERE key = $2;", target.id, key)
        await self.bot.sendSuccess(ctx, f"{ctx.author.mention} has given {target.mention} their credit with id: `{key}`.", ctx.message, ctx.guild)
        

    
    @commands.command()
    @commands.guild_only()
    async def redeem(self, ctx):
        """Redeem a premium credit to the current server. Use the `upgrade` command for more info on getting premium"""
        sufficient = await self.bot.db.fetchrow("SELECT key FROM newpremium WHERE userid = $1 AND enabled = False;", ctx.author.id)
        hasPremium = await self.bot.db.fetchrow("SELECT key FROM newpremium WHERE serverid = $1;", ctx.guild.id)
        if sufficient is not None:
            if hasPremium is None:
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
                await self.bot.db.execute("UPDATE newpremium SET enabled = TRUE, serverid = $1;", ctx.guild.id)
                prefix = await self.bot.getPrefix(ctx.guild.id)
                await self.bot.sendSuccess(ctx, f"`{ctx.guild}` now has premium enabled! Take a look at `{prefix}help` under the settings category in order to utilize premium fully!\n\nThank you for using Ticketer.", [ctx.message, initQuestion, message], ctx.guild)
            else:
                await self.bot.sendError(ctx, f"`{ctx.guild}` already has premium enabled!", ctx.message, ctx.guild)
        else:
            prefix = await self.bot.getPrefix(ctx.guild.id)
            await self.bot.sendError(ctx, f"{ctx.author.mention} has no credits to redeem.\n\nUse {prefix}support for a link to our support server to pruchase premium!", ctx.message, ctx.guild)
    
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
            cur_credits = await self.bot.db.fetch("SELECT key, enabled, serverid from newpremium WHERE userid = $1;", ctx.author.id)
            embedStr = ""
            for credit in cur_credits:
                if credit['enabled']:
                    embedStr += f"Key: `{credit['key']}` | Enabled: `True` | ServerID: `{credit['serverid']}`\n"
                else:
                    embedStr += f"Key: `{credit['key']}` | Enabled: `False`\n"
            await self.bot.sendSuccess(ctx, embedStr, ctx.message, ctx.guild)
        except Exception as e:
            print(e)
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
        key = str(uuid.uuid4())
        key = key.replace('-', '')
        key = key[:10]
        await self.bot.db.execute("INSERT INTO newpremium (userid, key) VALUES ($1, $2);", target.id, key) 
        await self.bot.sendSuccess(ctx, f"{target.mention} has received a new credit with ID: `{key}`.", [ctx.message, initQuestion, message], ctx.guild)
    
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
