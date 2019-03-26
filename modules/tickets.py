import discord
import asyncio
from discord.ext import commands
import traceback
import sys
import datetime
import config as cfg
import uuid
import typing
import aiohttp
import aiofiles
import os

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def create_transcript(self, channel, guild):
        try:
            lines = []
            initMessage = True
            async for message in channel.history(reverse=True):
                if initMessage:
                    initMessage = False
                    continue
                if len(message.embeds) > 0:
                    lines.append("**EMBED**<br /><br />")
                else:
                    lines.append(str(message.author) + ": " + message.content.replace(channel.mention, f"{channel}") + "<br /><br />")
            
            path = f"home/dtavana/Coding/Python/Ticketer/tickets/{guild.id}_{channel}.html"
            async with aiofiles.open(path, mode="w+") as transcript:
                await transcript.writelines(lines)
                
            return discord.File(path, filename=f"transcript_{channel}.html"), f"{guild.id}_{channel}.html", path
        except Exception as e:
            await channel.send(e)
            return None, None, None
    
    async def ticketeradmin(ctx):
        bot = ctx.bot
        role = await bot.get_adminrole(ctx.guild.id)
        role = ctx.guild.get_role(role)
        return role in ctx.author.roles
    
    async def closeonlyadmin(self, ctx):
        bot = ctx.bot
        role = await bot.get_adminrole(ctx.guild.id)
        role = ctx.guild.get_role(role)
        adminclose = await ctx.bot.get_adminclose(ctx.guild.id)
        return role in ctx.author.roles or not adminclose
    
    async def checkAdmin(self, ctx):
        bot = ctx.bot
        role = await bot.get_adminrole(ctx.guild.id)
        role = ctx.guild.get_role(role)
        return role in ctx.author.roles
    
    @commands.command()
    async def new(self, ctx, *, subject: typing.Union[discord.Member, str, None] = None):
        """Creates a new ticket. **NOTE:** Ticketer Admins may use this command in the format `new @USER` to create a ticket for said user"""
        enforce_subject = await self.bot.get_enforcesubject(ctx.guild.id)
        prefix = await self.bot.getPrefix(ctx.guild.id)
        if enforce_subject and subject is None:
            return await self.bot.sendError(ctx, f"The server admins have made it required to use a subject. Please use `{prefix}new SUBJECT` or if you are an admin, `{prefix}new @USER SUBJECT` to create a ticket.", ctx.message, ctx.guild)
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
            await self.bot.sendError(ctx, f"The server admins have not ran the `{prefix}initializesetup` command yet!", ctx.message, ctx.guild)
            return
        ticketchanint = await self.bot.get_ticketchan(ctx.guild.id)
        ticketchan = self.bot.get_channel(ticketchanint)
        specificchannels = await self.bot.get_specificchannels(ctx.guild.id)
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
        ticketprefix = await self.bot.get_ticketprefix(ctx.guild.id)
        welcomemessage = await self.bot.get_welcomemessage(ctx.guild.id)
        role = await self.bot.get_adminrole(ctx.guild.id)
        role = ctx.guild.get_role(role)

        channel_roles = []
        if specificchannels:
            for specificchannel in specificchannels:
                if specificchannel['channelid'] == ctx.channel.id:
                    channel_roles.append(specificchannel['roleid'])
        if specificchannels and not channel_roles:
            return await self.bot.sendError(ctx, f"{ctx.channel.mention} is not a ticket channel.", ctx.message, ctx.guild)


        if isinstance(subject, discord.Member):
            if not specificchannels:
                overwrites = {
                    ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False, read_messages=False),
                    ctx.author: discord.PermissionOverwrite(send_messages=True, read_messages=True, attach_files=True, embed_links=True),
                    role: discord.PermissionOverwrite(send_messages=True, read_messages=True, attach_files=True, embed_links=True),
                    ctx.bot.user: discord.PermissionOverwrite(send_messages=True, read_messages=True, attach_files=True, embed_links=True),
                    subject: discord.PermissionOverwrite(send_messages=True, read_messages=True, attach_files=True, embed_links=True)
                }
            else:
                overwrites = {
                    ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False, read_messages=False),
                    ctx.author: discord.PermissionOverwrite(send_messages=True, read_messages=True, attach_files=True, embed_links=True),
                    ctx.bot.user: discord.PermissionOverwrite(send_messages=True, read_messages=True, attach_files=True, embed_links=True),
                    subject: discord.PermissionOverwrite(send_messages=True, read_messages=True, attach_files=True, embed_links=True)
                }
                for roleid in channel_roles:
                    overwrites[ctx.guild.get_role(roleid)] = discord.PermissionOverwrite(send_messages=True, read_messages=True, attach_files=True, embed_links=True)
        else:
            if not specificchannels:
                overwrites = {
                    ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False, read_messages=False),
                    ctx.author: discord.PermissionOverwrite(send_messages=True, read_messages=True, attach_files=True, embed_links=True),
                    role: discord.PermissionOverwrite(send_messages=True, read_messages=True, attach_files=True, embed_links=True),
                    ctx.bot.user: discord.PermissionOverwrite(send_messages=True, read_messages=True, attach_files=True, embed_links=True)
                }
            else:
                overwrites = {
                    ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False, read_messages=False),
                    ctx.author: discord.PermissionOverwrite(send_messages=True, read_messages=True, attach_files=True, embed_links=True),
                    ctx.bot.user: discord.PermissionOverwrite(send_messages=True, read_messages=True, attach_files=True, embed_links=True)
                }
                for roleid in channel_roles:
                    overwrites[ctx.guild.get_role(roleid)] = discord.PermissionOverwrite(send_messages=True, read_messages=True, attach_files=True, embed_links=True)

        if isinstance(subject, discord.Member):
            target = subject
            subject = None
        else:
            target = ctx.author
        
        isBlacklisted = await self.bot.get_blacklisted(target.id, ctx.guild.id)
        if isBlacklisted:
            return await self.bot.sendError(ctx, f"{target.mention} is currently blacklisted from creating tickets.", ctx.message, ctx.guild)

        newticket = await ctx.guild.create_text_channel(f"{ticketprefix}-{currentticket}", category=ticketcategory, overwrites=overwrites)
        
        welcomemessage = welcomemessage.replace(":user:", target.mention)
        welcomemessage = welcomemessage.replace(":server:", str(ctx.guild))

        await self.bot.db.execute("INSERT INTO tickets (userid, ticketid, serverid) VALUES ($1, $2, $3);", target.id, newticket.id, ctx.guild.id)
        await self.bot.db.execute("UPDATE servers SET currentticket = currentticket + 1 WHERE serverid = $1;", ctx.guild.id)
        await self.bot.newTicket(newticket, subject, welcomemessage, target)
        await self.bot.sendNewTicket(ctx, f"{target.mention} your ticket has been opened, click here: {newticket.mention}", ctx.message, ctx.guild)
        await self.bot.sendLog(ctx.guild.id, f"{target} created a new ticket: {newticket.mention}", discord.Colour(0x32CD32))
        
    @commands.command()
    @commands.check(ticketeradmin)
    async def add(self, ctx, user: discord.Member, channel: discord.TextChannel):
        """Adds a user to a ticket. **NOTE:** Can only be run by Ticketer Admins"""
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
        """Removes a user from a ticket. **NOTE:** Can only be run by Ticketer Admins"""
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
    async def close(self, ctx, *, reason=None):
        """Closes a ticket"""
        try:
            close_data = await self.closeonlyadmin(ctx)
        except:
            close_data = True
        if close_data:
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
                channel = ctx.channel
                isPremium = await self.bot.get_premium(ctx.guild.id)
                sendTranscripts = await self.bot.get_sendtranscripts(ctx.guild.id)
                transcriptChan = await self.bot.get_transcriptchan(ctx.guild.id)
                if isPremium and sendTranscripts:
                    theFile, filename, path = await self.create_transcript(ctx.channel, ctx.guild)
                    ticketowner = await self.bot.get_ticketowner(ctx.channel.id)
                    ticketowner = ctx.guild.get_member(ticketowner)
                    if theFile is None and filename is None and path is None:
                        await self.bot.sendLog(ctx.guild.id, f"{ctx.author} closed `{ctx.channel}`\n**Reason:** `{reason}`\n**Transcript:** Could not be generated", discord.Colour(0xf44b42))
                        if ticketowner is not None:
                            await self.bot.sendError(ticketowner, f"Transcript for `{ctx.channel}` could not be generated")
                    else:
                        if transcriptChan != -1:
                            transcriptChan = self.bot.get_channel(transcriptChan)
                            logchan = await self.bot.sendLog(ctx.guild.id, f"{ctx.author} closed `{ctx.channel}`\n**Reason:** `{reason}`\n**Transcript:** In transcript channel", discord.Colour(0xf44b42))
                            await self.bot.sendLog(transcriptChan, f"{ctx.author} closed `{ctx.channel}`\n**Reason:** `{reason}`\n**Transcript:** Is below", discord.Colour(0xf44b42))
                            await self.bot.sendTranscript(transcriptChan, theFile)
                        else:
                            logchan = await self.bot.sendLog(ctx.guild.id, f"{ctx.author} closed `{ctx.channel}`\n**Reason:** `{reason}`\n**Transcript:** Is below", discord.Colour(0xf44b42))
                            if logchan is not None:
                                await self.bot.sendTranscript(logchan, theFile)
                        if ticketowner is not None:
                            await self.bot.sendSuccess(ticketowner, f"Transcript for `{ctx.channel}` is below")
                            await self.bot.sendTranscript(ticketowner, theFile)
                        try:
                            os.remove(path)
                        except:
                            pass
                else:
                    await self.bot.sendLog(ctx.guild.id, f"{ctx.author} closed `{ctx.channel}`\n**Reason:** `{reason}`", discord.Colour(0xf44b42))
                await self.bot.db.execute("DELETE FROM tickets WHERE ticketid = $1;", ctx.channel.id)
                await ctx.channel.delete(reason="Closing ticket.")
            else:
                await self.bot.sendError(ctx, f"You must run this command in a ticket channel.", ctx.message, ctx.guild)
        else:
            await self.bot.sendError(ctx, "The server admins have disallowed non admins to close tickets.", ctx.message, ctx.guild)
            
    @commands.command()
    @commands.check(ticketeradmin)
    async def closeall(self, ctx):
        """Closes all tickets"""
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
        await self.bot.sendSuccess(ctx, "All tickets have been closed.", [ctx.message, initQuestion, message], ctx.guild)
    
    @commands.command()
    @commands.check(ticketeradmin)
    async def blacklist(self, ctx, user: discord.Member):
        """Blacklists a user from creating new tickets"""
        data = await self.bot.db.fetchrow("SELECT userid FROM blacklist WHERE serverid = $1 AND userid = $2;", ctx.guild.id, user.id)
        if data is None:
            await self.bot.db.execute("INSERT INTO blacklist (userid, serverid) VALUES ($1, $2);", user.id, ctx.guild.id)
            await self.bot.sendSuccess(ctx, f"{user.mention} has been blacklisted.")
        else:
            await self.bot.sendError(ctx, f"{user.mention} is already in the blacklist.", ctx.message, ctx.guild)
    
    @commands.command()
    @commands.check(ticketeradmin)
    async def unblacklist(self, ctx, user: discord.Member):
        """Removed a user from the blacklist"""
        data = await self.bot.db.fetchrow("SELECT userid FROM blacklist WHERE serverid = $1 AND userid = $2;", ctx.guild.id, user.id)
        if data is not None:
            await self.bot.db.execute("DELETE FROM blacklist WHERE userid = $1 AND serverid = $2;", user.id, ctx.guild.id)
            await self.bot.sendSuccess(ctx, f"{user.mention} has been removed from the blacklist.")
        else:
            await self.bot.sendError(ctx, f"{user.mention} was not found in the blacklist.", ctx.message, ctx.guild)
    
    
    
    
def setup(bot):
    bot.add_cog(Tickets(bot))
