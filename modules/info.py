import discord
import asyncio
from discord.ext import commands
import traceback

#Misc. Modules
import datetime
import config as cfg
import psutil


class Information:
    def __init__(self, bot):
        self.bot = bot
    
    async def on_member_join(self, member):
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"Helping {len(self.bot.users)} users"))
        ticketchan = await self.bot.get_ticketchan(member.guild.id)
        prefix = await self.bot.getPrefix(member.guild.id)
        embed = discord.Embed(
            title=f"Ticketer", colour=discord.Colour(0x32CD32))
        embed.set_footer(text=f"Ticketer | {cfg.authorname}")
        if not ticketchan:
            embed.add_field(name=f"Welcome to {member.guild}!", value=f"For support, type `{prefix}new SUBJECT` and replace subject with a brief topic. You may then post any info in the created channel.\n\n")
        else:
            embed.add_field(name=f"Welcome to {member.guild}!",value=f"For support, please navigate to {ticketchan} and type `{prefix}new SUBJECT` and replace subject with a brief topic. You may then post any info in the created channel.\n\n")
        await member.send(embed=embed)
    
    async def on_member_remove(self, member):
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"Helping {len(self.bot.users)} users"))

    async def on_guild_join(self, guild):
        await self.bot.db.execute("INSERT INTO servers (serverid) VALUES ($1);", guild.id)
        await self.bot.db.execute("INSERT INTO settings (serverid) VALUES ($1);", guild.id)
        owner = guild.owner
        prefix = await self.bot.getPrefix(guild.id)
        
        embed = discord.Embed(
            title=f"Ticketer", colour=discord.Colour(0x32CD32))
        embed.set_footer(text=f"Ticketer | {cfg.authorname}")
        embed.add_field(
            name=f"Thank you for inviting me to {guild}!", value=f"My prefix is `{prefix}`. To start, please run `{prefix}setup`. You may view all of my current features using `{prefix}features`. You may upgrade these features by paying a one-time fee of **$5** which helps run Ticketer (`{prefix}upgrade`). For more information or any help, please join the official Discord Support Server. Thank you for using Ticketer.\n\n")
        await owner.send(embed=embed)
        await owner.send("https://discord.gg/uzygVc2")
    
    async def on_guild_remove(self, guild):
        await self.bot.db.execute("DELETE FROM servers WHERE serverid = $1;", guild.id)
        await self.bot.db.execute("DELETE FROM settings WHERE serverid = $1;", guild.id)

    @commands.command()
    async def support(self, ctx):
        await ctx.send("Please join the official Ticketer support server for more detailed support.")
        await ctx.send("https://discord.gg/uzygVc2")
    
    @commands.command()
    async def upgrade(self, ctx):
        await ctx.send("For only **$5**, you can upgrade to have so many more features and support Ticketer at the same time! Please join the offical support server for more information.")
        await ctx.send("https://discord.gg/uzygVc2")
    
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

        pre = await self.bot.get_pref(self, self.bot, ctx)

        memory_percent = psutil.virtual_memory()[2]

        e = discord.Embed(color=discord.Color.dark_blue())
        e.add_field(name="Bot Stats", value=f"**Coder:** {cfg.authorname}\n"
                                            f"**Commands:** {len(self.bot.commands)}\n"
                                            f"**Cogs:** {len(self.bot.cogs)}\n", inline=False)
        e.add_field(name="Discord Stats", value=f"**Prefix:** {pre}\n"
                                                f"**Ping:** {ctx.bot.latency * 1000:,.0f}ms\n"
                                                f"**Guilds:** {len(self.bot.guilds)}\n"
                                                f"**Users:** {len(self.bot.users)}\n"
                                                f"**Version:** 1", inline=False)
        e.add_field(name="PC Stats", value=f"**Memory:** {int(p.memory_info()[0]/1024/1024)}mb ({memory_percent}%)\n"
                    f"**CPU:** {psutil.cpu_percent()}%", inline=False)
        await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(Information(bot))
