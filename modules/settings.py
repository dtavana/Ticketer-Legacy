import discord
import asyncio
from discord.ext import commands
import traceback

#Misc. Modules
import datetime
import config as cfg


class Settings:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setup(self, ctx):
        guild = ctx.guild
        def validchannelcheck(message):
            try:
                messagestr = message.content[2:-1]
                channel = self.bot.get_channel(int(messagestr))
                return message.author == ctx.author and channel is not None
            except:
                return False
        
        def amountcheck(message):
            try:
                intval = int(message.content)
                return message.author == ctx.author and intval is not None
            except:
                return False

        def validrolecheck(message):
            try:
                messagestr = message.content[3:-1]
                role = guild.get_role(int(messagestr))
                return message.author == ctx.author and role is not None
            except:
                return False
        await ctx.send(f"Lets run through the setup for **{ctx.author.guild}**.")
        isPremium = await self.bot.get_premium(guild.id)
        embed = discord.Embed(
            title=f"Setup Info \U0000270d", colour=discord.Colour(0xFFA500))
        embed.set_footer(text=f"Ticketer | {cfg.authorname}")
        # ---GET CATEGORY FOR TICKETS
        try:
            await self.bot.get_channel(await self.bot.get_ticketcategory(ctx.guild.id)).delete(reason="Rerunning setup")
        except:
            pass
        categorychan = await ctx.guild.create_category("TicketerCategory")
        await ctx.send("I have created a category for tickets to be placed under, feel free to rename and move it but do not delete it. If you do, run this setup again.")
        if(isPremium):
            # ---GET CHANNEL FOR TICKETS
            await ctx.send("Please tag the channel you would like to set as the channel to create tickets.")
            ticketchan = await self.bot.wait_for('message', check=validchannelcheck, timeout=30)
            ticketchanint = int(ticketchan.content[2:-1])

            # ---GET TICKET PREFIX
            await ctx.send("Please enter what you would like as the ticket prefix. **NOTE**: Must be 10 characters or less!")
            ticketprefix = await self.bot.wait_for('message', check=lambda i: i.author == ctx.author and len(i.content) <= 10, timeout=30)

            # ---GET WELCOME MESSAGE FOR CHANNEL
            await ctx.send("Please enter what you would like the welcome message to be for new tickets. **NOTE**: Must be 100 characters or less!")
            welcomemessage = await self.bot.wait_for('message', check=lambda i: i.author == ctx.author and len(i.content) <= 100, timeout=30)

            # ---GET TICKET AMOUNT
            await ctx.send("Please enter the max amount of tickets a user may have at a time. Use -1 for unlimited. **NOTE**: Must be an actual integer.")
            ticketcount = await self.bot.wait_for('message', check=amountcheck, timeout=30)
            ticketcountint = int(ticketcount)

            # ---GET PREFIX
            await ctx.send("Please enter youre desired prefix **NOTE**: Must be less than 5 characters!")
            prefix = await self.bot.wait_for('message', check=lambda i: i.author == ctx.author and len(i.content) <= 5, timeout=30)

            # ---GET ROLE FOR ADMIN
            await ctx.send("Please tag the role you would like for admins to use as a Ticketer Administrator.")
            role = await self.bot.wait_for('message', check=validrolecheck, timeout=30)
            roleint = int(role.content[3:-1])

            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False)
            }
            categorychan = await ctx.guild.create_category("TicketerCategory", overwrites=overwrites)
            await ctx.send("I have created a category for tickets to be placed under, feel free to rename and move it but do not delete it. If you do, run this setup again.")

            await ctx.send("Are you sure you would like to perform the following? If yes, react with a Thumbs Up. Otherwise, reacting with a Thumbs Down")

            embed.add_field(name="Create Ticket Channel:",
                            value=f"{ticketchan.content}")
            embed.add_field(name="Ticket Prefix:",
                            value=f"`{ticketprefix.content}`")
            embed.add_field(name="Ticket Count:",
                            value=f"`{ticketcountint}`")
            embed.add_field(name="Welcome Message:",
                            value=f"`{welcomemessage.content}`")
            embed.add_field(name="Ticketer Admin Role:",
                            value=f"{role.content}")
            embed.add_field(name="Prefix:",
                            value=f"{prefix.content}")

            confirm = await ctx.send(embed=embed)
            await confirm.add_reaction("\U0001f44d")
            await confirm.add_reaction("\U0001f44e")

            def reactioncheck(reaction, user):
                validreactions = ["\U0001f44d", "\U0001f44e"]
                return user.id == ctx.author.id and reaction.emoji in validreactions
            reaction, user = await self.bot.wait_for('reaction_add', check=reactioncheck, timeout=30)
            # Check if thumbs up
            if reaction.emoji != "\U0001f44d":
                await ctx.send("Command Cancelled")
                return
            await self.bot.db.execute("UPDATE settings SET ticketchannel = $1, role = $2, welcomemessage = $3, ticketcategory = $4, prefix = $5, ticketprefix = $6, ticketcount = $7 WHERE serverid = $8;", ticketchanint, roleint, welcomemessage.content, categorychan.id, prefix.content, ticketprefix.content, ticketcountint, guild.id)
        else:
            await self.bot.db.execute("UPDATE settings SET ticketcategory = $1 WHERE serverid = $2;", categorychan.id, guild.id)
        await self.bot.sendSuccess(ctx, f"The setup has completed.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def clearsettings(self, ctx):
        await ctx.send("Are you sure you would like to perform the following? If yes, react with a Thumbs Up. Otherwise, reacting with a Thumbs Down")
        embed = discord.Embed(
            title=f"Settings Info \U0000270d", colour=discord.Colour(0xFFA500))
        embed.set_footer(text=f"Ticketer | {embed.timestamp}")
        embed.set_author(name=cfg.authorname)
        embed.add_field(name="Type:", value=f"`CLEAR SETTINGS`")
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
        ticketcategory = await self.bot.get_ticketcategory(ctx.guild.id)
        await self.bot.get_channel(ticketcategory).delete(reason="Clearing Ticketer settings.")
        await self.bot.db.execute(
            "DELETE FROM settings WHERE serverid = $1;", ctx.guild.id)
        await self.bot.db.execute(
            "INSERT INTO settings (serverid) VALUES ($1);", ctx.guild.id)
        await self.bot.sendSuccess(ctx, f"The settings were cleared.")


def setup(bot):
    bot.add_cog(Settings(bot))
