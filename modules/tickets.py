# Base Modules for Bot
import discord
import asyncio
from discord.ext import commands

# Misc. Modules
import datetime
import config as cfg


class Tickets:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def new(self, ctx, subject=None):
        ticketcategoryint = await self.bot.get_ticketcategory(ctx.guild.id)
        ticketcategory = self.bot.get_channel(ticketcategoryint)
        currentticket = await self.bot.get_currentticket(ctx.guild.id)
        ticketprefix = await self.bot.get_ticketprefix(ctx.guild.id)
        welcomemessage = await self.bot.get_welcomemessage(ctx.guild.id)
        ticketoverwrites = [(ctx.author, send_messages=True), (ctx.author. read_messages+True)]
        newticket = await ctx.guild.create_text_channel(f"{ticketprefix}-{currentticket}", category=ticketcategory, overwrites=ticketoverwrites)
        await self.bot.sendSuccess(ctx, f"New ticket created: {newticket.mention}.\n\nClick on the ticket in this message to navigate to the ticket.")
        await newticket.set_permissions(ctx.author, read_messages=True, send_messages=True)
        await self.bot.sendTicket(newticket, welcomemessage)
        
def setup(bot):
    bot.add_cog(Tickets(bot))
