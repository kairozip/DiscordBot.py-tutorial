# cogs/basic.py
import discord
from discord.ext import commands
from discord import app_commands
import time
import platform

class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
    
    @commands.command(name='ping', aliases=['pong'])
    async def ping(self, ctx):
        """Check bot latency"""
        start = time.perf_counter()
        message = await ctx.send("🏓 Pinging...")
        end = time.perf_counter()
        
        duration = (end - start) * 1000
        api_latency = round(self.bot.latency * 1000)
        
        await message.edit(
            content=f"🏓 **PONG!**\n"
                   f"📡 API Latency: `{api_latency}ms`\n"
                   f"⏱️ Response Time: `{duration:.2f}ms`"
        )
    
    @commands.command(name='hello', aliases=['hi', 'hey', 'sup'])
    async def hello(self, ctx):
        """Say hello to the bot"""
        greetings = [
            f"Hey there {ctx.author.mention}! 👋",
            f"Hello {ctx.author.display_name}! How's it going? 🌟",
            f"Sup {ctx.author.mention}? Ready to party? 🎉",
            f"Oh hey, it's {ctx.author.display_name}! What's crackin'? 🥨"
        ]
        await ctx.send(greetings[len(ctx.author.name) % len(greetings)])
    
    @commands.command(name='info', aliases=['botinfo', 'stats'])
    async def info(self, ctx):
        """Display bot information"""
        uptime_seconds = int(time.time() - self.start_time)
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        
        embed = discord.Embed(
            title=f"{self.bot.user.name} Bot Information",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📊 Statistics",
            value=f"Guilds: `{len(self.bot.guilds)}`\n"
                  f"Users: `{sum(g.member_count for g in self.bot.guilds)}`\n"
                  f"Commands: `{len(self.bot.commands)}`",
            inline=True
        )
        
        embed.add_field(
            name="⚙️ System",
            value=f"Python: `{platform.python_version()}`\n"
                  f"discord.py: `{discord.__version__}`\n"
                  f"Platform: `{platform.system()}`",
            inline=True
        )
        
        embed.add_field(
            name="⏰ Uptime",
            value=f"`{days}d {hours}h {minutes}m {seconds}s`",
            inline=False
        )
        
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        
        await ctx.send(embed=embed)
    
    @app_commands.command(name="slash_hello", description="Say hello using slash commands")
    async def slash_hello(self, interaction: discord.Interaction):
        """Slash command version of hello"""
        await interaction.response.send_message(f"Hello {interaction.user.mention}! This is a slash command! 👋")

async def setup(bot):
    await bot.add_cog(Basic(bot))