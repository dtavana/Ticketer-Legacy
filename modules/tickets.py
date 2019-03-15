# Base Modules for Bot
import discord
import asyncio
from discord.ext import commands
import traceback
import sys

# Misc. Modules
import datetime
import config as cfg
import uuid
import typing

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def ticketeradmin(ctx):
        bot = ctx.bot
        role = await bot.get_adminrole(ctx.guild.id)
        role = ctx.guild.get_role(role)
        return role in ctx.author.roles
    
    async def checkAdmin(self, ctx):
        bot = ctx.bot
        role = await bot.get_adminrole(ctx.guild.id)
        role = ctx.guild.get_role(role)
        return role in ctx.author.roles
    
    @commands.command()
    async def new(self, ctx, *, subject: typing.Union[discord.Member, str, None] = None):
        if isinstance(subject, discord.Member):
            isAdmin =  await self.checkAdmin(ctx)
            if not isAdmin:
                prefix = await self.bot.getPrefix(ctx.guild.id)
                message = await self.bot.sendError(ctx, f"{ctx.author.mention}, only Ticketer Admins can open tickets for others, use `{prefix}new SUBJECT`", ctx.message, ctx.guild)
                return
        isSetup = await self.bot.get_setup(ctx.guild.id)
        isPremium = await self.bot.get_premium(ctx.guild.id)
        if not isSetup:
            prefix = await self.bot.getPrefix(ctx.guild.id)
            await self.bot.sendError(ctx, f"The server admins have not ran the `{prefix}setup` command yet!", ctx.message, ctx.guild)
            return
        ticketchan = await self.bot.get_ticketchan(ctx.guild.id)
        ticketchan = self.bot.get_channel(ticketchan)
        if ticketchan is not None and ctx.channel is not ticketchan and isPremium:
            await self.bot.sendError(ctx, f"Please run this command in {ticketchan.mention}", ctx.message, ctx.guild)
            return
        data = await self.bot.db.fetch("SELECT * FROM tickets WHERE userid = $1 AND serverid = $2;", ctx.author.id, ctx.guild.id)
        ticketcount = await self.bot.get_ticketcount(ctx.guild.id)
        if len(data) + 1 > ticketcount and ticketcount != -1:
            await self.bot.sendError(ctx, f"{ctx.author.mention} has the max amount of tickets one can have.", ctx.message, ctx.guild)
            return
        ticketcategoryint = await self.bot.get_ticketcategory(ctx.guild.id)
        ticketcategory = self.bot.get_channel(ticketcategoryint)
        currentticket = await self.bot.get_currentticket(ctx.guild.id)
        '''
        channelToken = str(uuid.uuid4())
        channelToken = channelToken[:channelToken.find('-')]
        channelToken = channelToken[::2]
        '''
        ticketprefix = await self.bot.get_ticketprefix(ctx.guild.id)
        welcomemessage = await self.bot.get_welcomemessage(ctx.guild.id)
        role = await self.bot.get_adminrole(ctx.guild.id)
        role = ctx.guild.get_role(role)


        if isinstance(subject, discord.Member):
            overwrites = {
                self.bot.user: discord.PermissionOverwrite(send_messages=False, read_messages=False),
                ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False, read_messages=False),
                ctx.author: discord.PermissionOverwrite(send_messages=True, read_messages=True),
                role: discord.PermissionOverwrite(send_messages=True, read_messages=True),
                subject: discord.PermissionOverwrite(send_messages=True, read_messages=True)
            }
        else:
            overwrites = {
                self.bot.user: discord.PermissionOverwrite(send_messages=False, read_messages=False),
                ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False, read_messages=False),
                ctx.author: discord.PermissionOverwrite(send_messages=True, read_messages=True),
                role: discord.PermissionOverwrite(send_messages=True, read_messages=True),
            }

        newticket = await ctx.guild.create_text_channel(f"{ticketprefix}-{currentticket}", category=ticketcategory, overwrites=overwrites)
        #newticket = await ctx.guild.create_text_channel(f"{ticketprefix}-{channelToken}", category=ticketcategory, overwrites=overwrites)
        if isinstance(subject, discord.Member):
            target = subject
            subject = None 
        else:
            target = ctx.author
        await self.bot.db.execute("INSERT INTO tickets (userid, ticketid, serverid) VALUES ($1, $2, $3);", ctx.author.id, newticket.id, ctx.guild.id)
        await self.bot.sendNewTicket(ctx, f"{target.mention} your ticket has been opened, click here: {newticket.mention}", ctx.message, ctx.guild)
        await self.bot.sendLog(ctx.guild.id, f"{target} created a new ticket: {newticket.mention}", discord.Colour(0x32CD32))
        await self.bot.newTicket(newticket, subject, welcomemessage, target)
        await self.bot.increment_ticket(ctx.guild.id)
    
    @commands.command()
    @commands.check(ticketeradmin)
    async def add(self, ctx, user: discord.Member, channel: discord.TextChannel):
        data = await self.bot.db.fetchrow("SELECT ticketid FROM tickets WHERE ticketid = $1;", channel.id)
        if data is not None:
            await channel.set_permissions(user, read_messages=True, send_messages=True)
            await self.bot.sendSuccess(ctx, f"{user.mention} has been added to {channel.mention}.")
            await self.bot.sendSuccess(channel, f"{user.mention} has been added to this ticket.")
        else:
            await self.bot.sendError(ctx, f"{channel.mention} was not recognized as a ticket channel.", ctx.message, ctx.guild)
    
    @commands.command()
    @commands.check(ticketeradmin)
    async def remove(self, ctx, user: discord.Member, channel: typing.Optional[discord.TextChannel]):
        if channel is None:
            chanel = ctx.channel
        data = await self.bot.db.fetchrow("SELECT ticketid FROM tickets WHERE ticketid = $1;", channel.id)
        if data is not None:
            await channel.set_permissions(user, read_messages=False, send_messages=False)
            await self.bot.sendSuccess(ctx, f"{user.mention} has been removed from {channel.mention}.")
            await self.bot.sendSuccess(channel, f"{user.mention} has been removed from this ticket.")
        else:
            await self.bot.sendError(ctx, f"{channel.mention} was not recognized as a ticket channel.", ctx.message, ctx.guild)

    @commands.command()
    #@commands.check(ticketeradmin)
    async def close(self, ctx, *, reason=None):
        data = await self.bot.db.fetchrow("SELECT ticketid FROM tickets WHERE ticketid = $1;", ctx.channel.id)
        if data is not None:
            if(reason is None):
                message = await ctx.send(f"Are you sure you would like to close {ctx.channel.mention}? If yes, react with a Thumbs Up. Otherwise, react with a Thumbs Down")
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
            await self.bot.sendLog(ctx.guild.id, f"{ctx.author.mention} closed `{ctx.channel}`\n\n**Reason:** `{reason}`", discord.Colour(0xf44b42))
            await self.bot.db.execute("DELETE FROM tickets WHERE ticketid = $1;", ctx.channel.id)
            await ctx.channel.delete(reason="Closing ticket.")
        else:
            await self.bot.sendError(ctx, f"You must run this command in a ticket channel.", ctx.message, ctx.guild)

    @commands.command()
    @commands.check(ticketeradmin)
    async def closeall(self, ctx):
        initQuestion = await ctx.send("Are you sure you would like to perform the following? If yes, react with a Thumbs Up. Otherwise, reacting with a Thumbs Down")
        embed = discord.Embed(
            title=f"Ticketer Management \U0000270d", colour=discord.Colour(0xFFA500))
        embed.set_footer(text=f"Ticketer | {cfg.authorname}")
        embed.add_field(name="Command:", value=f"**CLOSE ALL TICKETS**")
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
        
        tickets = await self.bot.db.fetch("SELECT ticketid FROM tickets WHERE serverid = $1;", ctx.guild.id)
        for ticket in tickets:
            for key, value in ticket.items():
                try:
                    await self.bot.get_channel(value).delete(reason="Closing all tickets.")
                except:
                    pass
        await self.bot.db.execute("DELETE FROM tickets WHERE serverid = $1;", ctx.guild.id)
        await self.bot.sendLog(ctx.guild.id, f"{ctx.author.mention} closed all tickets.", discord.Colour(0xf44b42))
    
    @commands.command()
    @commands.check(ticketeradmin)
    async def blacklist(self, ctx, user: discord.Member):
        data = await self.bot.db.fetchrow("SELECT userid FROM blacklist WHERE serverid = $2 AND userid = $3;", user.id, ctx.guild.id, user.id)
        if data is None:
            await self.bot.db.execute("INSERT INTO blacklist (userid, serverid) VALUES ($1, $2);", user.id, ctx.guild.id)
            await self.bot.sendSuccess(ctx, f"{user.mention} has been blacklisted.")
        else:
            await self.bot.sendError(ctx, f"{user.mention} is already in the blacklist.", ctx.message, ctx.guild)
    
    @commands.command()
    @commands.check(ticketeradmin)
    async def unblacklist(self, ctx, user: discord.Member):
        data = await self.bot.db.fetchrow("SELECT userid FROM blacklist WHERE serverid = $2 AND userid = $3;", user.id, ctx.guild.id, user.id)
        if data is not None:
            await self.bot.db.execute("DELETE FROM blacklist WHERE userid = $1 AND serverid = $2;", user.id, ctx.guild.id)
            await self.bot.sendSuccess(ctx, f"{user.mention} has been removed from the blacklist.")
        else:
            await self.bot.sendError(ctx, f"{user.mention} was not found in the blacklist.", ctx.message, ctx.guild)
    
    
    
    
def setup(bot):
    bot.add_cog(Tickets(bot))
