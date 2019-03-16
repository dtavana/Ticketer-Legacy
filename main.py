 #!/usr/bin/python3
import discord
import asyncio
from discord.ext import commands
import traceback
import sys
import asyncpg

#Misc. Modules
import datetime
import config as cfg
import typing

extensions = [
    'modules.admin',
    'modules.info',
    'modules.settings',
    'modules.database',
    'modules.credits',
    'modules.tickets',
    'modules.errors'
]


class Ticketer(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=self.get_pref, case_insensitive=True)

    async def get_pref(self, bot, ctx):
        try:
            res = await self.db.fetchrow("SELECT prefix FROM settings WHERE serverid = $1;", ctx.guild.id)
            res = res['prefix']
            return res
        except:
            return['-']

    async def getPrefix(self, guildid):
        res = await self.db.fetchrow("SELECT prefix FROM settings WHERE serverid = $1;", guildid)
        return res['prefix']
    
    async def get_welcomemessage(self, guildid):
        res = await self.db.fetchrow("SELECT welcomemessage FROM settings WHERE serverid = $1;", guildid)
        res = res['welcomemessage']
        if res == "":
            return "Thank you for opening a new ticket! Administration will be with you shortly."
        return res

    async def get_currentticket(self, guildid):
        res = await self.db.fetchrow("SELECT currentticket FROM servers WHERE serverid = $1;", guildid)
        return res['currentticket']
    
    async def get_enforcesubject(self, guildid):
        res = await self.db.fetchrow("SELECT enforcesubject FROM settings WHERE serverid = $1;", guildid)
        return res['enforcesubject']
    
    async def get_dmonjoin(self, guildid):
        res = await self.db.fetchrow("SELECT dmonjoin FROM settings WHERE serverid = $1;", guildid)
        return res['dmonjoin']
    
    async def get_adminclose(self, guildid):
        res = await self.db.fetchrow("SELECT adminclose FROM settings WHERE serverid = $1;", guildid)
        return res['adminclose']
    
    async def get_sendtranscripts(self, guildid):
        res = await self.db.fetchrow("SELECT sendtranscripts FROM settings WHERE serverid = $1;", guildid)
        return res['sendtranscripts']

    async def get_cleannew(self, guildid):
        res = await self.db.fetchrow("SELECT cleannew FROM settings WHERE serverid = $1;", guildid)
        return res['cleannew']
    
    async def get_cleanall(self, guildid):
        res = await self.db.fetchrow("SELECT cleanall FROM settings WHERE serverid = $1;", guildid)
        return res['cleanall']
    
    async def get_ticketowner(self, ticketid):
        res = await self.db.fetchrow("SELECT userid FROM tickets WHERE ticketid = $1;", ticketid)
        return res['userid']
    
    async def increment_ticket(self, guildid):
        await self.db.execute("UPDATE servers SET currentticket = currentticket + 1 WHERE serverid = $1;", guildid)
    
    async def get_ticketprefix(self, guildid):
        res = await self.db.fetchrow("SELECT ticketprefix FROM settings WHERE serverid = $1;", guildid)
        return res['ticketprefix']
    
    async def get_ticketcategory(self, guildid):
        res = await self.db.fetchrow("SELECT ticketcategory FROM settings WHERE serverid = $1;", guildid)
        try:
            res = res['ticketcategory']
            return res
        except:
            return None
    
    async def get_adminrole(self, guildid):
        res = await self.db.fetchrow("SELECT role FROM settings WHERE serverid = $1;", guildid)
        try:
            res = res['role']
            return res
        except:
            return None
    
    async def get_ticketchan(self, guildid):
        res = await self.db.fetchrow("SELECT ticketchannel FROM settings WHERE serverid = $1;", guildid)
        res = res['ticketchannel']
        if res == 0:
            res = False
        return res
    
    async def get_logchan(self, guildid):
        res = await self.db.fetchrow("SELECT logchannel FROM settings WHERE serverid = $1;", guildid)
        res = res['logchannel']
        if res == 0:
            res = False
        return res
    
    async def get_setup(self, guildid):
        res = await self.db.fetchrow("SELECT setup FROM servers WHERE serverid = $1;", guildid)
        res = res['setup']
        return res
    
    async def get_ticketcount(self, guildid):
        res = await self.db.fetchrow("SELECT ticketcount FROM settings WHERE serverid = $1;", guildid)
        res = res['ticketcount']
        return res

    async def get_premium(self, guildid):
        res = await self.db.fetchrow("SELECT premium FROM servers WHERE serverid = $1;", guildid)
        res = res['premium']
        return res
    
    async def sendSuccess(self, target, valString, origMessages: typing.Union[list, discord.Message]=None, guild=None):
        embed = discord.Embed(
            title=f"**Success** \U00002705", description=valString, colour=discord.Colour(0x32CD32))
        embed.set_footer(text=f"Ticketer | {cfg.authorname}")
        success_message = await target.send(embed=embed)
        if origMessages is not None and guild is not None:
            toClean = None
            isPremium = await self.get_premium(guild.id)
            if isPremium:
                toClean = await self.get_cleanall(guild.id)
                if toClean:
                    if isinstance(origMessages, discord.Message):
                        origMessages = [origMessages]
                    await asyncio.sleep(10)
                    for message in origMessages:
                        try:
                            await message.delete()
                        except:
                            pass
                    try:
                        await success_message.delete()
                    except:
                        pass
        else:
            return success_message
    
    async def sendNewTicket(self, target, valString, origMessage=None, guild=None):
        embed = discord.Embed(
            description=valString, colour=discord.Colour(0x32CD32))
        embed.set_footer(text=f"Ticketer | {cfg.authorname}")
        message = await target.send(embed=embed)
        if origMessage is not None and guild is not None:
            toClean = None
            isPremium = await self.get_premium(guild.id)
            if isPremium:
                toClean = await self.get_cleannew(guild.id)
                if toClean:
                    await asyncio.sleep(10)
                    try:
                        await origMessage.delete()
                    except:
                        pass
                    try:
                        await message.delete()
                    except:
                        pass
        else:
            return message
    
    async def sendError(self, target, valString, origMessages: typing.Union[list, discord.Message]=None, guild=None, isNew=None):
        embed = discord.Embed(
            title=f"**Error** \U0000274c", description=valString, colour=discord.Colour(0xf44b42))
        embed.set_footer(text=f"Ticketer | {cfg.authorname}")
        error_message = await target.send(embed=embed)
        if origMessages is not None and guild is not None:
            toClean = None
            isPremium = await self.get_premium(guild.id)
            if isPremium:
                toClean = await self.get_cleanall(guild.id)
                if toClean:
                    if isinstance(origMessages, discord.Message):
                        origMessages = [origMessages]
                    await asyncio.sleep(10)
                    for message in origMessages:
                        try:
                            await message.delete()
                        except:
                            pass
                    try:
                        await error_message.delete()
                    except:
                        pass
        else:
            return error_message
    
    async def sendLog(self, guildid, valString, color):
        logchanid = await self.get_logchan(guildid)
        if logchanid == -1:
            return None
        target = self.get_channel(logchanid)
        if target is None:
            return
        embed = discord.Embed(
            title=f"**Log** \U0001f5d2", description=valString, colour=color)
        embed.set_footer(text=f"Ticketer | {cfg.authorname}")
        #embed.set_thumbnail(url = self.user.avatar_url)
        await target.send(embed=embed)
        return target
    
    async def sendTranscript(self, target, theFile):
        await target.send(file=theFile)
    
    async def newTicket(self, target, subject, welcomemessage, user):
        await target.send(user.mention)
        await asyncio.sleep(1)
        embed = discord.Embed(
            colour=discord.Colour(0x32CD32), description=welcomemessage)
        embed.set_footer(text=f"Ticketer | {cfg.authorname}")
        #embed.set_thumbnail(url = self.user.avatar_url)
        embed.add_field(
            name="Subject:", value=f"`{subject}`")
        await target.send(embed=embed)

    def run(self):
        # self.remove_command("help")
        for ext in extensions:
            try:
                self.load_extension(ext)
                print(f"Loaded extension {ext}")
            except Exception as e:
                print(f"Failed to load extensions {ext}")
                print(f"{type(e).__name__}: {e}")
        super().run(cfg.token)

    async def on_ready(self,):
        print("Bot loaded")
        print(f"Logged in as: {self.user}")
        print(f"Total Servers: {len(self.guilds)}")
        print(f"Total Cogs: {len(self.cogs)}")
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{len(self.guilds)} Guilds"))

        credentials = {"user": cfg.ticketeruser, "password": cfg.ticketerpass,
                       "database": cfg.ticketerdb, "host": cfg.ticketerhost, "port": cfg.ticketerport}
        self.db = await asyncpg.create_pool(**credentials)

        # Example create table code, you'll probably change it to suit you
        await self.db.execute("CREATE TABLE IF NOT EXISTS servers(serverid bigint PRIMARY KEY, currentticket smallint DEFAULT 1, premium boolean DEFAULT FALSE, setup boolean DEFAULT FALSE);")
        await self.db.execute("CREATE TABLE IF NOT EXISTS settings(serverid bigint PRIMARY KEY, prefix varchar DEFAULT '-', logchannel bigint DEFAULT -1, ticketchannel bigint DEFAULT -1, ticketcategory bigint DEFAULT 0, ticketprefix varchar DEFAULT 'ticket', role bigint DEFAULT 0, ticketcount smallint DEFAULT 3, welcomemessage varchar DEFAULT 'Welcome to our server. Support will be with you shortly', sendtranscripts boolean DEFAULT FALSE, cleannew boolean DEFAULT FALSE, cleanall boolean DEFAULT FALSE, adminclose boolean DEFAULT FALSE, dmonjoin boolean DEFAULT FALSE, enforcesubject boolean DEFAULT FALSE);")
        await self.db.execute("CREATE TABLE IF NOT EXISTS premium(userid bigint PRIMARY KEY, credits smallint);")
        await self.db.execute("CREATE TABLE IF NOT EXISTS tickets(userid bigint, ticketid bigint, serverid bigint);")
        await self.db.execute("CREATE TABLE IF NOT EXISTS blacklist(userid bigint, serverid bigint);")
        await self.db.execute("CREATE TABLE IF NOT EXISTS payments(userid bigint, paymentid varchar, payerid varchar, dateofpurchase date DEFAULT NOW());")

if __name__ == "__main__":
    Ticketer().run()
