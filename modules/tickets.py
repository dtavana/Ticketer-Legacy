# Base Modules for Bot
import discord
import asyncio
from discord.ext import commands
import traceback
import sys

# Misc. Modules
import datetime
import config as cfg


class Tickets:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def new(self, ctx, subject=None):
        data = await self.bot.db.fetch("SELECT * FROM tickets WHERE userid = $1;", ctx.author.id)
        ticketcount = await self.bot.get_ticketcount(ctx.guild.id)
        if len(data) + 1 > ticketcount:
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
        await self.bot.db.execute("INSERT INTO tickets (userid, ticketid) VALUES ($1, $2);", ctx.author.id, newticket.id)
        await self.bot.sendSuccess(ctx, f"New ticket created: {newticket.mention}.\n\nClick on the ticket in this message to navigate to the ticket.")
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

    
def setup(bot):
    bot.add_cog(Tickets(bot))
