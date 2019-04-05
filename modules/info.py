import discord
import asyncio
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from .utils.paginator import HelpPaginator, CannotPaginate
import traceback
import sys
import datetime
import config as cfg
import psutil


class Information(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.premiumtask = bot.loop.create_task(self.premiumLoop())
        self.votestask = bot.loop.create_task(self.votesLoop())
        self.PREMIUM_LOG_CHANNEL = 558771497817210881
        self.VOTES_LOG_CHANNEL = 563201592971493386
    
    async def create_ticket_on_join(self, member, guild):
        isBlacklisted = await self.bot.get_blacklisted(member.id, guild.id)
        if isBlacklisted:
            return
        ticketcategoryint = await self.bot.get_ticketcategory(guild.id)
        ticketcategory = self.bot.get_channel(ticketcategoryint)
        currentticket = await self.bot.get_currentticket(guild.id)
        ticketprefix = await self.bot.get_ticketprefix(guild.id)
        welcomemessage = await self.bot.get_newmemberwelcomemessage(guild.id)
        role = await self.bot.get_adminrole(guild.id)
        role = guild.get_role(role)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(send_messages=False, read_messages=False),
            member: discord.PermissionOverwrite(send_messages=True, read_messages=True, attach_files=True, embed_links=True, read_message_history=True),
            self.bot.user: discord.PermissionOverwrite(send_messages=True, read_messages=True, attach_files=True, embed_links=True, read_message_history=True),
            role: discord.PermissionOverwrite(send_messages=True, read_messages=True, attach_files=True, embed_links=True, read_message_history=True)
        }

        newticket = await guild.create_text_channel(f"{member.display_name}-welcometicket", category=ticketcategory, overwrites=overwrites)
        
        subject = "New member joined the guild"
        
        welcomemessage = welcomemessage.replace(":user:", member.mention)
        welcomemessage = welcomemessage.replace(":server:", str(guild))
        await self.bot.db.execute("INSERT INTO tickets (userid, ticketid, serverid) VALUES ($1, $2, $3);", member.id, newticket.id, guild.id)
        await self.bot.newTicket(newticket, subject, welcomemessage, member)
        await self.bot.sendLog(guild.id, f"{member} had a ticket opened for them when they joined the server: {newticket.mention}", discord.Colour(0x32CD32))
    
    async def premiumLoop(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(10)
        while not self.bot.is_closed():
            peopletomessage = await self.bot.db.fetch("SELECT * FROM premiumqueue")
            for person in peopletomessage:
                guildid = person['guildid']
                userid = person['userid']
                added = person['added']
                user = self.bot.get_user(userid)
                
                logchan = self.bot.get_channel(self.PREMIUM_LOG_CHANNEL)
                await self.bot.db.execute("DELETE FROM premiumqueue WHERE userid = $1", userid)
                if user is None:
                    if added:
                        await self.bot.sendNewTicket(logchan, f"`{userid}` had a credit added to their account")
                    else:
                        await self.bot.sendNewTicket(logchan, f"`{userid}` had a credit removed from their account")
                    continue
                else:
                    if added:
                        await self.bot.sendNewTicket(logchan, f"{user.mention} had a credit added to their account")
                    else:
                        await self.bot.sendNewTicket(logchan, f"{user.mention} had a credit removed from their account")
                if added:
                    await self.bot.sendSuccess(user, f"You have had one premium credit added to your account! Use the `redeem` command to get started!")
                else:
                    await self.bot.sendSuccess(user, f"You have had one premium credit removed from your account! This is due to a chargeback, refund, or a subscription ending. If you would like to get premium again, use the `upgrade` command.")
            await asyncio.sleep(5)
    
    async def votesLoop(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(10)
        while not self.bot.is_closed():
            peopletomessage = await self.bot.db.fetch("SELECT * FROM votesqueue")
            for person in peopletomessage:
                cur_votes = person['cur_votes']
                userid = person['userid']
                receiveCredit = person['receivecredit']
                user = self.bot.get_user(userid)
                await self.bot.db.execute("DELETE FROM votesqueue WHERE userid = $1", userid)
                logchan = self.bot.get_channel(self.VOTES_LOG_CHANNEL)
                if user is None:
                    if receiveCredit:
                        await self.bot.sendNewTicket(logchan, f"`{userid}` just received a credit for voting!")
                    else:
                        await self.bot.sendNewTicket(logchan, f"`{userid}` just voted for Ticketer!")
                    continue
                else:
                    if receiveCredit:
                        await self.bot.sendNewTicket(logchan, f"{user.mention} just received a credit for voting!")
                    else:
                        await self.bot.sendNewTicket(logchan, f"{user.mention} just voted for Ticketer!")
                if receiveCredit:
                    await self.bot.sendSuccess(user, f"You have had one premium credit added to your account! Use the `redeem` command to get started! Thank you for voting for Ticketer!")
                else:
                    await self.bot.sendSuccess(user, f"Thank you for voting for Ticketer! You currently have **{cur_votes} votes** and need **{30 - cur_votes} votes** to receive a premium credit. Continue voting to receive 1 Premium Credit.")
            await asyncio.sleep(5)
    
    
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{len(self.bot.guilds)} Guilds | {len([usr for usr in self.bot.users if not usr.bot])} Users"))
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{len(self.bot.guilds)} Guilds | {len([usr for usr in self.bot.users if not usr.bot])} Users"))
        dmonjoin = await self.bot.get_dmonjoin(member.guild.id)
        isSetup = await self.bot.get_setup(member.guild.id)
        isPremium = await self.bot.get_premium(member.guild.id)
        isTicketOnJoin = await self.bot.get_ticketonjoin(member.guild.id)
        if isSetup and isPremium and isTicketOnJoin:
            await self.create_ticket_on_join(member, member.guild)
        if not dmonjoin:
            return
        ticketchan = await self.bot.get_ticketchan(member.guild.id)
        try:
            ticketchan = self.bot.get_channel(ticketchan)
        except:
            ticketchan = False
        prefix = await self.bot.getPrefix(member.guild.id)
        embed = discord.Embed(
            title=f"Ticketer", colour=discord.Colour(0x32CD32))
        embed.set_footer(text=f"Ticketer | {cfg.authorname}")
        #embed.set_thumbnail(url = self.bot.user.avatar_url)
        if not ticketchan:
            embed.add_field(name=f"Welcome to {member.guild}!", value=f"For support, type `{prefix}new SUBJECT` and replace subject with a brief topic. You may then post any info in the created channel.\n\n")
        else:
            embed.add_field(name=f"Welcome to {member.guild}!",value=f"For support, please navigate to {ticketchan.mention} and type `{prefix}new SUBJECT` and replace subject with a brief topic. You may then post any info in the created channel.\n\n")
        await member.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{len(self.bot.guilds)} Guilds | {len([usr for usr in self.bot.users if not usr.bot])} Users"))
        try:
            await self.bot.db.execute("INSERT INTO servers (serverid) VALUES ($1);", guild.id)
        except:
            pass
        try:
            await self.bot.db.execute("INSERT INTO settings (serverid) VALUES ($1);", guild.id)
        except:
            pass
        
        owner = guild.owner
        prefix = await self.bot.getPrefix(guild.id)
        
        embed = discord.Embed(
            title=f"Ticketer", colour=discord.Colour(0x32CD32))
        embed.set_footer(text=f"Ticketer | {cfg.authorname}")
        #embed.set_thumbnail(url = self.bot.user.avatar_url)
        embed.add_field(
            name=f"Thank you for inviting me to {guild}!", value=f"To get started, please run the `{prefix}initializesetup` command.\n\nMy prefix is `{prefix}`. You may upgrade these features by paying a monthly fee of **$2** which helps run Ticketer (`{prefix}upgrade`). For more information or any help, please join the official Discord Support Server. Thank you for using Ticketer.\n\n")
        try:
            await owner.send(embed=embed)
            await owner.send("https://discord.gg/5kNM5Sh")
        except:
            pass
        '''
        await asyncio.sleep(5)
        try:
            role = await guild.create_role(name="Ticketer Admin")
            categorychan = await guild.create_category("TicketerCategory")
            await self.bot.db.execute("UPDATE settings SET ticketcategory = $1, role = $2 WHERE serverid = $3;", categorychan.id, role.id, guild.id)
            await owner.add_roles(role, reason="Initial Ticketer Setup")
            await self.bot.db.execute("UPDATE servers SET setup = True WHERE serverid = $1;", guild.id)
        except:
            pass
        '''
    
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{len(self.bot.guilds)} Guilds | {len([usr for usr in self.bot.users if not usr.bot])} Users"))
        await self.bot.db.execute("DELETE FROM settings WHERE serverid = $1;", guild.id)
        await self.bot.db.execute("DELETE FROM blacklist WHERE serverid = $1;", guild.id)
        await self.bot.db.execute("DELETE FROM tickets WHERE serverid = $1;", guild.id)
        await self.bot.db.execute("DELETE FROM specificchannels WHERE serverid = $1;", guild.id)
        await self.bot.db.execute("UPDATE servers SET setup = False, currentticket = 1 WHERE serverid = $1;", guild.id)

    @commands.command()
    async def supportserver(self, ctx):
        """Displays an invite to the support server"""
        await ctx.send("Please join the official Ticketer support server for more detailed support.")
        await ctx.send("https://discord.gg/5kNM5Sh")
    
    @commands.command()
    async def info(self, ctx):
        """Displays general info about the bot"""
        prefix = await self.bot.getPrefix(ctx.guild.id)
        embed = discord.Embed(
            title=f"Ticketer", colour=discord.Colour(0x32CD32))
        embed.set_footer(text=f"Ticketer | {cfg.authorname}")
        #embed.set_thumbnail(url = self.bot.user.avatar_url)
        embed.add_field(
            name=f"Thank you for using Ticketer!", value=f"To get started, run the `{prefix}initializesetup` command. This will create a role called Ticketer Admin as well as the category TicketerCategory. Make sure you give any staff you would like to be able to use Ticketer Admin commands the new role. **DO NOT** delete either of these, doing so will require you to run `{prefix}initializesetup`. Feel free to rename both of these. My help command is `{prefix}help`. Use this to view all of my commands. Certain commands can only be accessed by a Ticketer Admin.\n\nMy prefix is `{prefix}`. You may upgrade these features by paying a monthly fee of **$2** which helps run Ticketer (`{prefix}upgrade`). For more information or any help, please join the official Discord Support Server. Thank you for using Ticketer.\n\n")
        await ctx.send(embed=embed)
        await ctx.send("https://discord.gg/5kNM5Sh")
    
    @commands.command()
    async def upgrade(self, ctx):
        """Information about upgrading to premium"""
        await self.bot.sendSuccess(ctx, f"[Click here to purchase premium](https://donatebot.io/checkout/542717934104084511)", ctx.message, ctx.guild)
    
    @commands.command()
    async def inviteme(self, ctx):
        """Displays an invite to invite me"""
        await self.bot.sendSuccess(ctx, f"To invite me, [click here](https://discordapp.com/oauth2/authorize?client_id=542709669211275296&scope=bot&permissions=805825745)")
          
    @commands.command()
    @commands.cooldown(1, 3.0, type=commands.BucketType.member)
    async def help(self, ctx, *, command: str = None):
        """Displays help for all commands"""
        try:
            if command is None:
                p = await HelpPaginator.from_bot(ctx)
            else:
                entity = self.bot.get_cog(command) or self.bot.get_command(command)
                if entity is None:
                    clean = command.replace('@', '@\u200b')
                    return await self.bot.sendError(ctx, f'Command or category `{clean}` not found.', ctx.message, ctx.guild)
                elif isinstance(entity, commands.Command):
                    p = await HelpPaginator.from_command(ctx, entity)
                else:
                    p = await HelpPaginator.from_cog(ctx, entity)

            await p.paginate()
        except Exception as e:
            await ctx.send(e)
    
    @commands.command(aliases=['statistics'])
    @commands.is_owner()
    async def stats(self, ctx):
        """Shows the bot's stats"""
        online = (len(set([m for m in self.bot.get_all_members(
        ) if m.status == discord.Status.online and not m.bot])))
        away = (len(set([m for m in self.bot.get_all_members()
                         if m.status == discord.Status.idle and not m.bot])))
        dnd = (len(set([m for m in self.bot.get_all_members()
                        if m.status == discord.Status.dnd and not m.bot])))
        offline = (len(set([m for m in self.bot.get_all_members(
        ) if m.status == discord.Status.offline and not m.bot])))

        p = psutil.Process()

        prefix = await self.bot.getPrefix(ctx.guild.id)

        memory_percent = psutil.virtual_memory()[2]

        e = discord.Embed(color=discord.Color.dark_blue())
        #e.set_thumbnail(url = self.bot.user.avatar_url)
        e.add_field(name="Bot Stats", value=f"**Coder:** {cfg.authorname}\n"
                                            f"**Commands:** {len(self.bot.commands)}\n"
                                            f"**Cogs:** {len(self.bot.cogs)}\n", inline=False)
        e.add_field(name="Discord Stats", value=f"**Prefix:** {prefix}\n"
                                                f"**Ping:** {ctx.bot.latency * 1000:,.0f}ms\n"
                                                f"**Guilds:** {len(self.bot.guilds)}\n"
                                                f"**Users:** {len(self.bot.users)}\n"
                                                f"**Version:** 1", inline=False)
        e.add_field(name="PC Stats", value=f"**Memory:** {int(p.memory_info()[0]/1024/1024)}mb ({memory_percent}%)\n"
                    f"**CPU:** {psutil.cpu_percent()}%", inline=False)
        await ctx.send(embed=e)
    
    @help.error
    async def info_handler(self, ctx, error):
        import traceback
        traceback.print_exception(type(error), error, error.__traceback__)
        if isinstance(error, commands.CommandOnCooldown):
            seconds = error.retry_after
            seconds = round(seconds, 2)
            hours, remainder = divmod(int(seconds), 3600)
            minutes, seconds = divmod(remainder, 60)
            await self.bot.sendError(ctx, f"You are on cooldown! Please try again in **{seconds} seconds**", ctx.message, ctx.guild)

def setup(bot):
    bot.add_cog(Information(bot))
