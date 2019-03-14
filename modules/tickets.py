# Base Modules for Bot
import discord
import asyncio
from discord.ext import commands
import traceback
import sys

# Misc. Modules
import datetime
import config as cfg


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def ticketeradmin(ctx):
        bot = ctx.bot
        role = await bot.get_adminrole(ctx.guild.id)
        role = ctx.guild.get_role(role)
        return role in ctx.author.roles
    
    @commands.command()
    async def new(self, ctx, subject=None):
        data = await self.bot.db.fetch("SELECT * FROM tickets WHERE userid = $1;", ctx.author.id)
        ticketcount = await self.bot.get_ticketcount(ctx.guild.id)
        if len(data) + 1 > ticketcount and ticketcount != -1:
            await self.bot.sendError(ctx, f"{ctx.author.mention} has the max amount of tickets one can have.")
            return
        ticketcategoryint = await self.bot.get_ticketcategory(ctx.guild.id)
        ticketcategory = self.bot.get_channel(ticketcategoryint)
        currentticket = await self.bot.get_currentticket(ctx.guild.id)
        ticketprefix = await self.bot.get_ticketprefix(ctx.guild.id)
        welcomemessage = await self.bot.get_welcomemessage(ctx.guild.id)
        overwrites = {
            ctx.author: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(send_messages=False)
        }
        newticket = await ctx.guild.create_text_channel(f"{ticketprefix}-{currentticket}", category=ticketcategory, overwrites=overwrites)
        await self.bot.db.execute("INSERT INTO tickets (userid, ticketid, serverid) VALUES ($1, $2, $3);", ctx.author.id, newticket.id, ctx.guild.id)
        await self.bot.sendSuccess(ctx, f"New ticket created: {newticket.mention}.\n\nClick on the ticket in this message to navigate to the ticket.")
        await self.bot.sendLog(ctx.guild.id, f"{ctx.author.mention} created a new ticket: {newticket.mention}", discord.Colour(0x32CD32))
        await self.bot.newTicket(newticket, subject, welcomemessage)
        await self.bot.increment_ticket(ctx.guild.id)
    
    @commands.command()
    async def add(self, ctx, user: discord.Member):
        data = await self.bot.db.fetchrow("SELECT ticketid = $1 AS exists FROM tickets;", ctx.channel.id)
        if data['exists']:
            await ctx.channel.set_permissions(user, read_messages=True, send_messages=True)
            await self.bot.sendSuccess(ctx, f"{user.mention} has been added to this ticket.")
        else:
            await self.bot.sendError(ctx, f"You must run this command in a ticket channel.")

    @commands.command()
    @commands.check(ticketeradmin)
    async def close(self, ctx, reason=None):
        data = await self.bot.db.fetchrow("SELECT ticketid = $1 AS exists FROM tickets;", ctx.channel.id)
        if data['exists']:
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
            await self.bot.sendError(ctx, f"You must run this command in a ticket channel.")

    @commands.command()
    @commands.check(ticketeradmin)
    async def closeall(self, ctx):
        await ctx.send("Are you sure you would like to perform the following? If yes, react with a Thumbs Up. Otherwise, reacting with a Thumbs Down")
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
            await ctx.send("Command Cancelled")
            return
        
        data = await self.bot.db.fetch("SELECT ticketid FROM tickets WHERE serverid = $1;", ctx.guild.id)
        for ticket in data:
            for key, value in data.items():
                try:
                    await self.bot.get_channel(value).delete(reason="Closing all tickets.")
                except:
                    pass
        await self.bot.db.execute("DELETE FROM tickets WHERE serverid = $1;", ctx.guild.id)
    
    @commands.command()
    @commands.check(ticketeradmin)
    async def blacklist(self, ctx, user: discord.Member):
        await self.bot.db.execute("INSERT INTO blacklist (userid, serverid) VALUES ($1, $2);", user.id, ctx.guild.id)
        await self.bot.sendSuccess(ctx, f"{user.mention} has been blacklisted.")
    
    @commands.command()
    @commands.check(ticketeradmin)
    async def unblacklist(self, ctx, user: discord.Member):
        data = await self.bot.db.fetchrow("SELECT userid = $1 AS exists FROM blacklist WHERE serverid = $2;", user.id, ctx.guild.id)
        if data['exists']:
            await self.bot.db.execute("DELETE FROM blacklist WHERE userid = $1 AND serverid = $2;", user.id, ctx.guild.id)
            await self.bot.sendSuccess(ctx, f"{user.mention} has been removed from the blacklist.")
        else:
            await self.bot.sendError(ctx, f"{user.mention} was not found in the blacklist.")
    
    
    
    
def setup(bot):
    bot.add_cog(Tickets(bot))
