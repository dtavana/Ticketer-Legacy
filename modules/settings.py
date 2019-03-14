import discord
import asyncio
from discord.ext import commands
import traceback
import sys

#Misc. Modules
import datetime
import config as cfg


class Settings(commands.Cog):
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
        
        await ctx.send(f"Lets run through the setup for **{ctx.author.guild}**.")
        
        ticketcategory = await self.bot.get_ticketcategory(ctx.guild.id)
        role = await self.bot.get_adminrole(ctx.guild.id)
        try:
            await ctx.guild.get_role(role).delete(reason="Clearing Ticketer settings.")
        except:
            pass
        try:
            await self.bot.get_channel(ticketcategory).delete(reason="Clearing Ticketer settings.")
        except:
            pass
        await self.bot.db.execute(
            "DELETE FROM settings WHERE serverid = $1;", ctx.guild.id)
        await self.bot.db.execute(
            "INSERT INTO settings (serverid) VALUES ($1);", ctx.guild.id)
        
        isPremium = await self.bot.get_premium(guild.id)
        embed = discord.Embed(
            title=f"Setup Info \U0000270d", colour=discord.Colour(0xFFA500))
        embed.set_footer(text=f"Ticketer | {cfg.authorname}")
        embed.set_thumbnail(url = self.bot.user.avatar_url)
        role = await ctx.guild.create_role(name="Support Team")
        '''
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False),
            role: discord.PermissionOverwrite(send_messages=True),
            role: discord.PermissionOverwrite(read_messages=True)
        }
        categorychan = await ctx.guild.create_category("TicketerCategory", overwrites=overwrites)
        '''

        categorychan = await ctx.guild.create_category("TicketerCategory")

        await ctx.send("I have created a category for tickets to be placed under, feel free to rename and move it but do not delete it. If you do, run this setup again.")
        
        if(isPremium):
            try:
                # ---GET CHANNEL FOR TICKETS
                await ctx.send("Please tag the channel you would like to set as the channel to create tickets.")
                ticketchan = await self.bot.wait_for('message', check=validchannelcheck, timeout=30)
                ticketchanint = int(ticketchan.content[2:-1])

                # ---GET CHANNEL FOR LOGS
                await ctx.send("Please tag the channel you would like to set as the log channel for tickets.")
                logchan = await self.bot.wait_for('message', check=validchannelcheck, timeout=30)
                logchanint = int(logchan.content[2:-1])

                # ---GET TICKET PREFIX
                await ctx.send("Please enter what you would like as the ticket prefix. **NOTE**: Must be 10 characters or less!")
                ticketprefix = await self.bot.wait_for('message', check=lambda i: i.author == ctx.author and len(i.content) <= 10, timeout=30)

                # ---GET WELCOME MESSAGE FOR CHANNEL
                await ctx.send("Please enter what you would like the welcome message to be for new tickets. **NOTE**: Must be 100 characters or less!")
                welcomemessage = await self.bot.wait_for('message', check=lambda i: i.author == ctx.author and len(i.content) <= 100, timeout=30)

                # ---GET TICKET AMOUNT
                await ctx.send("Please enter the max amount of tickets a user may have at a time. Use -1 for unlimited. **NOTE**: Must be an actual integer.")
                ticketcount = await self.bot.wait_for('message', check=amountcheck, timeout=30)
                ticketcountint = int(ticketcount.content)

                # ---GET PREFIX
                await ctx.send("Please enter youre desired command prefix **NOTE**: Must be less than 5 characters!")
                prefix = await self.bot.wait_for('message', check=lambda i: i.author == ctx.author and len(i.content) <= 5, timeout=30)

                # ---GET ROLE FOR ADMIN
                await ctx.send("Please enter the name for the role to be used for a Ticketer Administrator.")
                rolename = await self.bot.wait_for('message', check=lambda i: i.author == ctx.author, timeout=30)
                await role.edit(name=rolename.content)
            except asyncio.TimeoutError:
                await self.bot.sendError(ctx, f'Your current operation timed out. Please re-run the command')
                try:
                    await role.delete(reason="Setup timed out.")
                except:
                    pass
                try:
                    await categorychan.delete(reason="Setup timed out.")
                except:
                    pass
                return

            await ctx.send("Are you sure you would like to perform the following? If yes, react with a Thumbs Up. Otherwise, reacting with a Thumbs Down")

            embed.add_field(name="Create Ticket Channel:",
                            value=f"{ticketchan.content}")
            embed.add_field(name="Ticket Log Channel:",
                            value=f"{logchan.content}")
            embed.add_field(name="Ticket Prefix:",
                            value=f"`{ticketprefix.content}`")
            embed.add_field(name="Ticket Count:",
                            value=f"`{ticketcountint}`")
            embed.add_field(name="Welcome Message:",
                            value=f"`{welcomemessage.content}`")
            embed.add_field(name="Ticketer Admin Role:",
                            value=f"{role.mention}")
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
            await self.bot.db.execute("UPDATE settings SET ticketchannel = $1, role = $2, welcomemessage = $3, ticketcategory = $4, prefix = $5, ticketprefix = $6, ticketcount = $7, logchannel = $8 WHERE serverid = $9;", ticketchanint, role.id, welcomemessage.content, categorychan.id, prefix.content, ticketprefix.content, ticketcountint, logchanint, guild.id)
        else:
            await ctx.send("I have created a role for Ticketer Admin called Support Team. You may **NOT** change the name of this role. If you delete it, please rerun setup.")
            await self.bot.db.execute("UPDATE settings SET ticketcategory = $1, role = $2 WHERE serverid = $3;", categorychan.id, role.id, guild.id)
        await self.bot.db.execute("UPDATE servers SET setup = True WHERE serverid = $1;", ctx.guild.id)
        await self.bot.sendSuccess(ctx, f"The setup has completed.")
        await ctx.author.add_roles(role, reason="Role for Ticketer Administrators added")

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def clearsettings(self, ctx):
        await ctx.send("Are you sure you would like to perform the following? If yes, react with a Thumbs Up. Otherwise, reacting with a Thumbs Down")
        embed = discord.Embed(
            title=f"Settings Info \U0000270d", colour=discord.Colour(0xFFA500))
        embed.set_footer(text=f"Ticketer | {embed.timestamp}")
        embed.set_thumbnail(url = self.bot.user.avatar_url)
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
        role = await self.bot.get_adminrole(ctx.guild.id)
        try:
            await ctx.guild.get_role(role).delete(reason="Clearing Ticketer settings.")
        except:
            pass
        try:
            await self.bot.get_channel(ticketcategory).delete(reason="Clearing Ticketer settings.")
        except:
            pass
        await self.bot.db.execute(
            "DELETE FROM settings WHERE serverid = $1;", ctx.guild.id)
        await self.bot.db.execute(
            "INSERT INTO settings (serverid) VALUES ($1);", ctx.guild.id)
        await self.bot.sendSuccess(ctx, f"The settings were cleared.")
        await self.bot.db.execute("UPDATE servers SET setup = False WHERE serverid = $1;", ctx.guild.id)

def setup(bot):
    bot.add_cog(Settings(bot))
