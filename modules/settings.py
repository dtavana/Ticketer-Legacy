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
    async def initializesetup(self, ctx):
        """Creates the Ticketer Admin role as well as the Ticketer Category. **Run this command if you have deleted either the role or category created on guild join**"""
        category = await self.bot.get_ticketcategory(ctx.guild.id)
        role = await self.bot.get_adminrole(ctx.guild.id)

        try:
            await self.bot.get_channel(category).delete(reason="Running setup")
        except:
            pass
        try:
            await ctx.guild.get_role(role).delete(reason="Running setup")
        except:
            pass
        role = await ctx.guild.create_role(name="Ticketer Admin")
        categorychan = await ctx.guild.create_category("TicketerCategory")
        await ctx.author.add_roles(role)
        await self.bot.db.execute("UPDATE settings SET ticketcategory = $1, role = $2 WHERE serverid = $3;", categorychan.id, role.id, ctx.guild.id)
        await self.bot.sendSuccess(ctx, f"I have created the role Ticketer Admin as well as the category TicketerCategory. Make sure you give any staff you would like to be able to use Ticketer Admin commands the new role. **DO NOT** delete either of these, doing so will require you to run this command again. Feel free to rename both of these.", ctx.message, ctx.guild)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setspecificchannels(self, ctx):
        """Sets specifc ticket creation channels to be bound to specific roles. **NOTE:** requires `setticketchannel` to be set to `-1`"""
        def validchannelcheck(message):
            try:
                messagestr = message.content[2:-1]
                channel = self.bot.get_channel(int(messagestr))
                return message.author == ctx.author and channel is not None
            except:
                return False
        
        def validrolecheck(message):
            try:
                if message.content == "-1":
                    return True
                messagestr = message.content[3:-1]
                role = message.guild.get_role(int(messagestr))
                return message.author == ctx.author and role is not None
            except:
                return False
        
        isPremium = await self.bot.get_premium(ctx.guild.id)
        ticketchan = None
        await asyncio.sleep(1)
        if(isPremium):
            ticketchan = await self.bot.get_ticketchan(ctx.guild.id)
            if ticketchan != -1:
                prefix = await self.bot.getPrefix(ctx.guild.id)
                return await self.bot.sendError(ctx, f"**{ctx.guild}** currently does not {prefix}setticketchannel equal to `-1`. Please do so before proceeding", ctx.message, ctx.guild)
            try:
                role_message = await ctx.send("Please tag the role you would like to set as the designated role to view the ticket channel you are creating. **NOTE:** Admins still need to have the Ticketer Admin role to manage tickets.")
                role = await self.bot.wait_for('message', check=validrolecheck, timeout=120)
                roleint = int(role.content[3:-1])
                channel_message = await ctx.send("Please tag the channel you would like to set as the channel to create tickets. **NOTE:** Enter **-1** to not restrict the channel.")
                ticketchan = await self.bot.wait_for('message', check=validchannelcheck, timeout=120)
                ticketchanint = int(ticketchan.content[2:-1])
                await self.bot.db.execute("INSERT INTO specificchannels (serverid, channelid, roleid) VALUES ($1, $2, $3);", ctx.guild.id, ticketchanint, roleint)
                await self.bot.sendSuccess(ctx, f"{ticketchan.content} is now bound to {role.content}", [ctx.message, role_message, channel_message], ctx.guild)
            except asyncio.TimeoutError:
                return await self.bot.sendError(ctx, f'Your current operation timed out. Please re-run the command', [ctx.message, role_message, channel_message, ticketchan], ctx.guild)
        else:
            prefix = await self.bot.getPrefix(ctx.guild.id)
            await self.bot.sendError(ctx, f"**{ctx.guild}** currently does not have premium enabled! For more info, please look at `{prefix}upgrade`", ctx.message, ctx.guild)
        

    
    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setticketchannel(self, ctx):
        """Sets the channel to restrict creation of tickets to. **NOTE:** use `-1` to allow creation of tickets in any channel OR to define channels that are bound to specific roles such that only those roles can see the created tickets"""
        def validchannelcheck(message):
            try:
                if message.content == "-1":
                    return True
                messagestr = message.content[2:-1]
                channel = self.bot.get_channel(int(messagestr))
                return message.author == ctx.author and channel is not None
            except:
                return False
        
        isPremium = await self.bot.get_premium(ctx.guild.id)
        ticketchan = None
        await asyncio.sleep(1)
        if(isPremium):
            try:
                # ---GET CHANNEL FOR TICKETS
                message = await ctx.send("Please tag the channel you would like to set as the channel to create tickets. **NOTE:** Enter **-1** to not restrict the channel.")
                ticketchan = await self.bot.wait_for('message', check=validchannelcheck, timeout=120)
                if(ticketchan.content == "-1"):
                    ticketchanint = -1
                else:
                    ticketchanint = int(ticketchan.content[2:-1])
            except asyncio.TimeoutError:
                return await self.bot.sendError(ctx, f'Your current operation timed out. Please re-run the command', [ctx.message, message, ticketchan], ctx.guild)
            await self.bot.db.execute("UPDATE settings SET ticketchannel = $1 WHERE serverid = $2;", ticketchanint, ctx.guild.id)
            if ticketchanint == -1:
                await self.bot.sendSuccess(ctx, f"Create ticket channel is now unbounded", [ctx.message, message, ticketchan], ctx.guild)
            else:
                await self.bot.sendSuccess(ctx, f"Create ticket channel is now {ticketchan.content}", [ctx.message, message, ticketchan], ctx.guild)
        else:
            prefix = await self.bot.getPrefix(ctx.guild.id)
            await self.bot.sendError(ctx, f"**{ctx.guild}** currently does not have premium enabled! For more info, please look at `{prefix}upgrade`", ctx.message, ctx.guild)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setlogchannel(self, ctx):
        """Sets the channel to restrict creation of tickets to. **NOTE:** use -1 to disable logs. **NOTE:** transcripts require one to set a log channel"""
        def validchannelcheck(message):
            try:
                if message.content == "-1":
                    return True
                messagestr = message.content[2:-1]
                channel = self.bot.get_channel(int(messagestr))
                return message.author == ctx.author and channel is not None
            except:
                return False

        isPremium = await self.bot.get_premium(ctx.guild.id)
        logchan = None
        await asyncio.sleep(1)
        if(isPremium):
            try:
                message = await ctx.send("Please tag the channel you would like to set as the log channel for tickets. **NOTE:** Enter **-1** to not have a log channel.")
                logchan = await self.bot.wait_for('message', check=validchannelcheck, timeout=120)
                if(logchan.content == "-1"):
                    logchanint = -1
                else:
                    logchanint = int(logchan.content[2:-1])
            except asyncio.TimeoutError:
                return await self.bot.sendError(ctx, f'Your current operation timed out. Please re-run the command', [ctx.message, message, logchan], ctx.guild)
            await self.bot.db.execute("UPDATE settings SET logchannel = $1 WHERE serverid = $2;", logchanint, ctx.guild.id)
            if logchanint == -1:
                await self.bot.sendSuccess(ctx, f"Log channel is now unbounded", [ctx.message, message, logchan], ctx.guild)
            else:
                await self.bot.sendSuccess(ctx, f"Log channel is now {logchan.content}", [ctx.message, message, logchan], ctx.guild)
        else:
            prefix = await self.bot.getPrefix(ctx.guild.id)
            await self.bot.sendError(ctx, f"**{ctx.guild}** currently does not have premium enabled! For more info, please look at `{prefix}upgrade`", ctx.message, ctx.guild)

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setticketprefix(self, ctx):
        """Sets the prefix before a ticket. Example: `ticket-123` where `ticket` is the ticket prefix"""
        isPremium = await self.bot.get_premium(ctx.guild.id)
        ticketprefix = None
        await asyncio.sleep(1)
        if(isPremium):
            try:
                message = await ctx.send("Please enter what you would like as the ticket prefix. **NOTE**: Must be 10 characters or less!")
                ticketprefix = await self.bot.wait_for('message', check=lambda i: i.author == ctx.author and len(i.content) <= 10, timeout=120)
            except asyncio.TimeoutError:
                return await self.bot.sendError(ctx, f'Your current operation timed out. Please re-run the command', [ctx.message, message, ticketprefix], ctx.guild)

            await self.bot.db.execute("UPDATE settings SET ticketprefix = $1 WHERE serverid = $2;", ticketprefix.content, ctx.guild.id)
            await self.bot.sendSuccess(ctx, f"Ticket Prefix is now set to `{ticketprefix.content}`", [ctx.message, message, ticketprefix], ctx.guild)
        else:
            prefix = await self.bot.getPrefix(ctx.guild.id)
            await self.bot.sendError(ctx, f"**{ctx.guild}** currently does not have premium enabled! For more info, please look at `{prefix}upgrade`", ctx.message, ctx.guild)
            
    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setwelcomemessage(self, ctx):
        """Sets the welcome message that is displayed at the creation of a ticket in the ticket. **NOTE:** `:user:` and `:server:` can be used in the welcome message to be replaced with a mention of the user that created the ticket and the sevrer name"""
        isPremium = await self.bot.get_premium(ctx.guild.id)
        welcomemessage = None
        await asyncio.sleep(1)
        if(isPremium):
            try:
                message = await ctx.send("Please enter what you would like the welcome message to be for new tickets. **NOTE**: Must be 2000 characters or less! You may use `:user:` to mention the user in your message or `:server:` to insert your server name.")
                welcomemessage = await self.bot.wait_for('message', check=lambda i: i.author == ctx.author and len(i.content) <= 2000, timeout=120)
            except asyncio.TimeoutError:
                return await self.bot.sendError(ctx, f'Your current operation timed out. Please re-run the command', [ctx.message, message, welcomemessage], ctx.guild)

            await self.bot.db.execute("UPDATE settings SET welcomemessage = $1 WHERE serverid = $2;", welcomemessage.content, ctx.guild.id)
            await self.bot.sendSuccess(ctx, f"Welcome Message is now set to:\n\n{welcomemessage.content}", [ctx.message, message, welcomemessage], ctx.guild)
        else:
            prefix = await self.bot.getPrefix(ctx.guild.id)
            await self.bot.sendError(ctx, f"**{ctx.guild}** currently does not have premium enabled! For more info, please look at `{prefix}upgrade`", ctx.message, ctx.guild)
            
    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setmaxtickets(self, ctx):
        """Sets the max amount of tickets a user may have. **NOTE:** use -1 to undrestrict a max amount of tickets"""
        def amountcheck(message):
            try:
                intval = int(message.content)
                return message.author == ctx.author and intval is not None and intval >= -1
            except:
                return False

        isPremium = await self.bot.get_premium(ctx.guild.id)
        ticketcount = None
        await asyncio.sleep(1)
        if(isPremium):
            try:
                message = await ctx.send("Please enter the max amount of tickets a user may have at a time. Use -1 for unlimited. **NOTE**: Must be an actual integer.")
                ticketcount = await self.bot.wait_for('message', check=amountcheck, timeout=120)
                ticketcountint = int(ticketcount.content)
            except asyncio.TimeoutError:
                return await self.bot.sendError(ctx, f'Your current operation timed out. Please re-run the command', [ctx.message, message], ctx.guild)

            await self.bot.db.execute("UPDATE settings SET ticketcount = $1 WHERE serverid = $2;", ticketcountint, ctx.guild.id)
            if ticketcountint == -1: 
                await self.bot.sendSuccess(ctx, f"Ticket Count is now set to `Unlimited`", [ctx.message, message, ticketcount], ctx.guild)
            else:
                await self.bot.sendSuccess(ctx, f"Ticket Count is now set to `{ticketcountint}`", [ctx.message, message, ticketcount], ctx.guild)
        else:
            prefix = await self.bot.getPrefix(ctx.guild.id)
            await self.bot.sendError(ctx, f"**{ctx.guild}** currently does not have premium enabled! For more info, please look at `{prefix}upgrade`", ctx.message, ctx.guild)
            
    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setprefix(self, ctx):
        """Sets the command prefix for all commands. By default, this is set to `-`"""
        isPremium = await self.bot.get_premium(ctx.guild.id)
        prefix = None
        await asyncio.sleep(1)
        if(isPremium):
            try:
                message = await ctx.send("Please enter youre desired command prefix **NOTE**: Must be less than 5 characters!")
                prefix = await self.bot.wait_for('message', check=lambda i: i.author == ctx.author and len(i.content) <= 5, timeout=120)
            except asyncio.TimeoutError:
                return await self.bot.sendError(ctx, f'Your current operation timed out. Please re-run the command', [ctx.message, message, prefix], ctx.guild)

            await self.bot.db.execute("UPDATE settings SET prefix = $1 WHERE serverid = $2;", prefix.content, ctx.guild.id)
            await self.bot.sendSuccess(ctx, f"Command Prefix is now set to `{prefix.content}`", [ctx.message, message, prefix], ctx.guild)
        else:
            prefix = await self.bot.getPrefix(ctx.guild.id)
            await self.bot.sendError(ctx, f"**{ctx.guild}** currently does not have premium enabled! For more info, please look at `{prefix}upgrade`", ctx.message, ctx.guild)
            
    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setdmonjoin(self, ctx):
        """Sets a DM on join for users that explains how Ticketer works"""
        isPremium = await self.bot.get_premium(ctx.guild.id)
        dmonjoin = None
        await asyncio.sleep(1)
        if(isPremium):
            try:
                message = await ctx.send("Please enter **1** to turn this feature on or **2** to turn this feature off!")
                dmonjoin = await self.bot.wait_for('message', check=lambda i: i.author == ctx.author and i.content == '1' or i.content == '2', timeout=120)
            except asyncio.TimeoutError:
                return await self.bot.sendError(ctx, f'Your current operation timed out. Please re-run the command', [ctx.message, message, dmonjoin], ctx.guild)

            if dmonjoin.content == '1':
                dmonjoindata = True
            else:
                dmonjoindata = False
            await self.bot.db.execute("UPDATE settings SET dmonjoin = $1 WHERE serverid = $2;", dmonjoindata, ctx.guild.id)
            await self.bot.sendSuccess(ctx, f"DM On Join is now set to `{dmonjoindata}`", [ctx.message, message, dmonjoin], ctx.guild)
        else:
            prefix = await self.bot.getPrefix(ctx.guild.id)
            await self.bot.sendError(ctx, f"**{ctx.guild}** currently does not have premium enabled! For more info, please look at `{prefix}upgrade`", ctx.message, ctx.guild)
            
    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setcleannew(self, ctx):
        """Sets the option to clean `new` invocations. In short, this will delete the command invocation as well as the embed displaying that a new ticket has been created"""
        isPremium = await self.bot.get_premium(ctx.guild.id)
        cleannew = None
        await asyncio.sleep(1)
        if(isPremium):
            try:
                message = await ctx.send("Please enter **1** to turn this feature on or **2** to turn this feature off!")
                cleannew = await self.bot.wait_for('message', check=lambda i: i.author == ctx.author and i.content == '1' or i.content == '2', timeout=120)
            except asyncio.TimeoutError:
                return await self.bot.sendError(ctx, f'Your current operation timed out. Please re-run the command', [ctx.message, message, cleannew], ctx.guild)

            if cleannew.content == '1':
                cleannewdata = True
            else:
                cleannewdata = False
            await self.bot.db.execute("UPDATE settings SET cleannew = $1 WHERE serverid = $2;", cleannewdata, ctx.guild.id)
            await self.bot.sendSuccess(ctx, f"Clean New Ticket Invocations is now set to `{cleannewdata}`", [ctx.message, message, cleannew], ctx.guild)
        else:
            prefix = await self.bot.getPrefix(ctx.guild.id)
            await self.bot.sendError(ctx, f"**{ctx.guild}** currently does not have premium enabled! For more info, please look at `{prefix}upgrade`", ctx.message, ctx.guild)
            
    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setcleanall(self, ctx):
        """Sets the option to clean all invocations other than `new` invocations. In short, this will delete the command invocation as well as any embeds displayed afterwards"""
        isPremium = await self.bot.get_premium(ctx.guild.id)
        cleanall = None
        await asyncio.sleep(1)
        if(isPremium):
            try:
                message = await ctx.send("Please enter **1** to turn this feature on or **2** to turn this feature off!")
                cleanall = await self.bot.wait_for('message', check=lambda i: i.author == ctx.author and i.content == '1' or i.content == '2', timeout=120)
            except asyncio.TimeoutError:
                return await self.bot.sendError(ctx, f'Your current operation timed out. Please re-run the command', [ctx.message, message, cleanall], ctx.guild)

            if cleanall.content == '1':
                cleanalldata = True
            else:
                cleanalldata = False
            await self.bot.db.execute("UPDATE settings SET cleanall = $1 WHERE serverid = $2;", cleanalldata, ctx.guild.id)
            await self.bot.sendSuccess(ctx, f"Clean All Invocations is now set to `{cleanalldata}`", [ctx.message, message, cleanall], ctx.guild)
        else:
            prefix = await self.bot.getPrefix(ctx.guild.id)
            await self.bot.sendError(ctx, f"**{ctx.guild}** currently does not have premium enabled! For more info, please look at `{prefix}upgrade`", ctx.message, ctx.guild)
            
    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setenforcesubject(self, ctx):
        """Sets the need for a user to provide a subject when creating a ticket. **NOTE:** this does not apply to when a Ticketer Admin uses `new @USER`"""
        isPremium = await self.bot.get_premium(ctx.guild.id)
        enforcesubject = None
        await asyncio.sleep(1)
        if(isPremium):
            try:
                message = await ctx.send("Please enter **1** to turn this feature on or **2** to turn this feature off!")
                enforcesubject = await self.bot.wait_for('message', check=lambda i: i.author == ctx.author and i.content == '1' or i.content == '2', timeout=120)
            except asyncio.TimeoutError:
                return await self.bot.sendError(ctx, f'Your current operation timed out. Please re-run the command', [ctx.message, message, enforcesubject], ctx.guild)

            if enforcesubject.content == '1':
                enforcesubjectdata = True
            else:
                enforcesubjectdata = False
            await self.bot.db.execute("UPDATE settings SET enforcesubject = $1 WHERE serverid = $2;", enforcesubjectdata, ctx.guild.id)
            await self.bot.sendSuccess(ctx, f"Enforcing Subject is now set to `{enforcesubjectdata}`", [ctx.message, message, enforcesubject], ctx.guild)
        else:
            prefix = await self.bot.getPrefix(ctx.guild.id)
            await self.bot.sendError(ctx, f"**{ctx.guild}** currently does not have premium enabled! For more info, please look at `{prefix}upgrade`", ctx.message, ctx.guild)
            
    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def settranscripts(self, ctx):
        """Sets the sending of transcripts to a log channel as well as the user that created the ticket on closing of the ticket. **NOTE:** requires `setlogchannel` to be set to `True`"""
        isPremium = await self.bot.get_premium(ctx.guild.id)
        transcripts = None
        await asyncio.sleep(1)
        if(isPremium):
            try:
                message = await ctx.send("Please enter **1** to turn this feature on or **2** to turn this feature off!")
                transcripts = await self.bot.wait_for('message', check=lambda i: i.author == ctx.author and i.content == '1' or i.content == '2', timeout=120)
            except asyncio.TimeoutError:
                return await self.bot.sendError(ctx, f'Your current operation timed out. Please re-run the command', [ctx.message, message, transcripts], ctx.guild)

            if transcripts.content == '1':
                transcriptsdata = True
            else:
                transcriptsdata = False
            await self.bot.db.execute("UPDATE settings SET sendtranscripts = $1 WHERE serverid = $2;", transcriptsdata, ctx.guild.id)
            await self.bot.sendSuccess(ctx, f"Sending Transcripts is now set to `{transcriptsdata}`", [ctx.message, message, transcripts], ctx.guild)
        else:
            prefix = await self.bot.getPrefix(ctx.guild.id)
            await self.bot.sendError(ctx, f"**{ctx.guild}** currently does not have premium enabled! For more info, please look at `{prefix}upgrade`", ctx.message, ctx.guild)
            
    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setadminclose(self, ctx):
        """Sets the ability for non admins to close tickets. **NOTE:** `True` disallows non admins from closing tickets"""
        isPremium = await self.bot.get_premium(ctx.guild.id)
        adminclose = None
        await asyncio.sleep(1)
        if(isPremium):
            try:
                message = await ctx.send("Please enter **1** to turn this feature on or **2** to turn this feature off!")
                adminclose = await self.bot.wait_for('message', check=lambda i: i.author == ctx.author and i.content == '1' or i.content == '2', timeout=120)
            except asyncio.TimeoutError:
                return await self.bot.sendError(ctx, f'Your current operation timed out. Please re-run the command', [ctx.message, message, adminclose], ctx.guild)

            if adminclose.content == '1':
                adminclosedata = True
            else:
                adminclosedata = False
            await self.bot.db.execute("UPDATE settings SET adminclose = $1 WHERE serverid = $2;", adminclosedata, ctx.guild.id)
            await self.bot.sendSuccess(ctx, f"Admin Only Ticket Close is now set to `{adminclosedata}`", [ctx.message, message, adminclose], ctx.guild)
        else:
            prefix = await self.bot.getPrefix(ctx.guild.id)
            await self.bot.sendError(ctx, f"**{ctx.guild}** currently does not have premium enabled! For more info, please look at `{prefix}upgrade`", ctx.message, ctx.guild)
            
    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def clearsettings(self, ctx):
        """Clears all settings from the server. **NOTE:** run `initializesetup` after this command to ensure that the bot functions correctly"""
        initQuestion = await ctx.send("Are you sure you would like to perform the following? If yes, react with a Thumbs Up. Otherwise, reacting with a Thumbs Down")
        embed = discord.Embed(
            title=f"Settings Info \U0000270d", colour=discord.Colour(0xFFA500))
        embed.set_footer(text=f"Ticketer | {embed.timestamp}")
        #embed.set_thumbnail(url = self.bot.user.avatar_url)
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
            return await self.bot.sendError(ctx, "Command Cancelled", [ctx.message, initQuestion, message], ctx.guild)
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
        await self.bot.sendSuccess(ctx, f"The settings were cleared.", [ctx.message, initQuestion, message], ctx.guild)
        await self.bot.db.execute("UPDATE servers SET setup = False WHERE serverid = $1;", ctx.guild.id)

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def clearspecificchannels(self, ctx):
        """Clears all specific channel settings from the server."""
        initQuestion = await ctx.send("Are you sure you would like to perform the following? If yes, react with a Thumbs Up. Otherwise, reacting with a Thumbs Down")
        embed = discord.Embed(
            title=f"Settings Info \U0000270d", colour=discord.Colour(0xFFA500))
        embed.set_footer(text=f"Ticketer | {embed.timestamp}")
        #embed.set_thumbnail(url = self.bot.user.avatar_url)
        embed.set_author(name=cfg.authorname)
        embed.add_field(name="Type:", value=f"`CLEAR SPECIFIC CHANNELS`")
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
        await self.bot.db.execute(
            "DELETE FROM specificchannels WHERE serverid = $1;", ctx.guild.id)
        await self.bot.sendSuccess(ctx, f"The role bound channels were cleared.", [ctx.message, initQuestion, message], ctx.guild)

def setup(bot):
    bot.add_cog(Settings(bot))
