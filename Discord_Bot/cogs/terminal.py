# cogs/terminal.py
import discord
from discord.ext import commands
import asyncio
import subprocess
import os

class Terminal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='terminal', aliases=['term', 'cmd', 'shell'])
    @commands.is_owner()  # Only bot owner can use this
    async def terminal_cmd(self, ctx, *, command):
        """Execute a terminal command from Discord and get output"""
        await ctx.send(f"⚡ Executing: `{command}`")
        
        try:
            # Run the command and capture output
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Decode output
            output = stdout.decode('utf-8', errors='ignore') if stdout else ""
            error = stderr.decode('utf-8', errors='ignore') if stderr else ""
            
            # Prepare response
            response = ""
            if output:
                if len(output) > 1900:
                    output = output[:1900] + "...\n[Output truncated]"
                response += f"**Output:**\n```\n{output}\n```"
            if error:
                if len(error) > 1900:
                    error = error[:1900] + "...\n[Error truncated]"
                response += f"**Error:**\n```\n{error}\n```"
            if not output and not error:
                response = "✅ Command executed successfully (no output)"
            
            await ctx.send(response)
            
        except Exception as e:
            await ctx.send(f"❌ Error executing command: {e}")
    
    @commands.command(name='say', aliases=['echo'])
    @commands.is_owner()
    async def say(self, ctx, *, message):
        """Make the bot say something in the channel"""
        await ctx.send(message)
        try:
            await ctx.message.delete()  # Delete the command message
        except:
            pass  # If we can't delete, whatever
    
    @commands.command(name='dm')
    @commands.is_owner()
    async def dm_user(self, ctx, user: discord.User, *, message):
        """Send a DM to a user from the bot"""
        try:
            await user.send(f"**Message from bot owner:** {message}")
            await ctx.send(f"✅ DM sent to {user}")
        except Exception as e:
            await ctx.send(f"❌ Failed to send DM: {e}")
    
    @commands.command(name='status')
    @commands.is_owner()
    async def change_status(self, ctx, status_type, *, status_text):
        """Change bot status: playing, watching, listening, competing"""
        status_map = {
            'playing': discord.Game(name=status_text),
            'watching': discord.Activity(type=discord.ActivityType.watching, name=status_text),
            'listening': discord.Activity(type=discord.ActivityType.listening, name=status_text),
            'competing': discord.Activity(type=discord.ActivityType.competing, name=status_text)
        }
        
        if status_type.lower() in status_map:
            await self.bot.change_presence(activity=status_map[status_type.lower()])
            await ctx.send(f"✅ Status changed to {status_type}: {status_text}")
        else:
            await ctx.send("❌ Invalid status type. Use: playing, watching, listening, competing")
    
    @commands.command(name='servers', aliases=['guilds'])
    @commands.is_owner()
    async def list_servers(self, ctx):
        """List all servers the bot is in"""
        embed = discord.Embed(
            title="🌐 Bot Servers",
            description=f"I'm in {len(self.bot.guilds)} servers",
            color=discord.Color.blue()
        )
        
        for guild in self.bot.guilds:
            embed.add_field(
                name=guild.name,
                value=f"ID: `{guild.id}`\nMembers: {guild.member_count}\nOwner: {guild.owner}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='leave')
    @commands.is_owner()
    async def leave_server(self, ctx, guild_id: int = None):
        """Leave a server by ID (or current server if no ID)"""
        if guild_id:
            guild = self.bot.get_guild(guild_id)
            if guild:
                await guild.leave()
                await ctx.send(f"✅ Left server: {guild.name}")
            else:
                await ctx.send("❌ Server not found with that ID")
        else:
            # Leave current server
            guild_name = ctx.guild.name
            await ctx.guild.leave()
            await ctx.send(f"✅ Left current server: {guild_name}")
    
    @commands.command(name='restart')
    @commands.is_owner()
    async def restart_bot(self, ctx):
        """Restart the bot"""
        await ctx.send("🔄 Restarting bot...")
        # Small delay to ensure message sends
        await asyncio.sleep(1)
        await self.bot.close()

async def setup(bot):
    await bot.add_cog(Terminal(bot))