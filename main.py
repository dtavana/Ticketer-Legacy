import discord
import asyncio
from discord.ext import commands
import traceback
import asyncpg

#Misc. Modules
import datetime
import config as cfg

extensions = [
    'modules.admin',
    'modules.info',
    'modules.settings',
    'modules.database',
    'modules.credits',
    'modules.tickets'
]


class Ticketer(commands.AutoShardedBot):
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

    async def get_currentticket(self, guildid):
        res = await self.db.fetchrow("SELECT currentticket FROM servers WHERE serverid = $1;", guildid)
        return res['currentticket']
    
    async def get_ticketprefix(self, guildid):
        res = await self.db.fetchrow("SELECT ticketprefix FROM settings WHERE serverid = $1;", guildid)
        return res['ticketprefix']
    
    async def get_ticketcategory(self, guildid):
        res = await self.db.fetchrow("SELECT ticketcategory FROM settings WHERE serverid = $1;", guildid)
        res = res['ticketcategory']
        return res
    
    async def get_ticketchan(self, guildid):
        res = await self.db.fetchrow("SELECT ticketchannel FROM settings WHERE serverid = $1;", guildid)
        res = res['ticketchannel']
        if res == 0:
            res = False
        return res

    async def get_premium(self, guildid):
        res = await self.db.fetchrow("SELECT premium FROM servers WHERE serverid = $1;", guildid)
        res = res['premium']
        return res
    
    async def sendSuccess(self, target, valString):
        embed = discord.Embed(
            title=f"Success \U00002705", colour=discord.Colour(0x32CD32))
        embed.set_footer(text=f"Ticketer | {cfg.authorname}")
        embed.add_field(
            name="Data:", value=valString)
        await target.send(embed=embed)
    
    async def sendError(self, target, valString):
        embed = discord.Embed(
            title=f"Error \U0000274c", colour=discord.Colour(0xf44b42))
        embed.set_footer(text=f"Ticketer | {cfg.authorname}")
        embed.add_field(
            name="Data:", value=valString)
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
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"Helping {len(self.users)} users"))

        credentials = {"user": cfg.ticketeruser, "password": cfg.ticketerpass,
                       "database": cfg.ticketerdb, "host": cfg.ticketerhost, "port": cfg.ticketerport}
        self.db = await asyncpg.create_pool(**credentials)

        # Example create table code, you'll probably change it to suit you
        await self.db.execute("CREATE TABLE IF NOT EXISTS servers(serverid bigint PRIMARY KEY, currentticket smallint DEFAULT 1, premium boolean DEFAULT FALSE);")
        await self.db.execute("CREATE TABLE IF NOT EXISTS settings(serverid bigint PRIMARY KEY, prefix varchar DEFAULT '-', ticketchannel bigint DEFAULT 0, ticketcategory bigint DEFAULT 0, ticketprefix varchar DEFAULT 'ticket', role bigint DEFAULT 0, welcomemessage varchar DEFAULT '');")
        await self.db.execute("CREATE TABLE IF NOT EXISTS premium(userid bigint PRIMARY KEY, credits smallint);")
  
        # Error logging
        async def on_command_error(ctx, error):
            embed = discord.Embed(
                title=f"**ERROR** \U0000274c", colour=discord.Colour(0xf44b42))
            embed.set_footer(text=f"Ticketer | {embed.timestamp}")
            embed.set_author(name=cfg.authorname)
            embed.add_field(
                name="There was the following exception!", value=f"```{error}```")
            await ctx.send(embed=embed)
            channel = self.get_channel(488893718125084687)
            await channel.send(embed=embed)

        async def on_error(ctx, error):
            embed = discord.Embed(
                title=f"**ERROR** \U0000274c", colour=discord.Colour(0xf44b42))
            embed.set_footer(text=f"Ticketer | {embed.timestamp}")
            embed.set_author(name=cfg.authorname)
            embed.add_field(
                name="There was the following exception!", value=f"```{error}```")
            await ctx.send(embed=embed)
            channel = self.get_channel(488893718125084687)
            await channel.send(embed=embed)


if __name__ == "__main__":
    Ticketer().run()
