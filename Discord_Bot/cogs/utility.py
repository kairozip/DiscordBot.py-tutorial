# cogs/utility.py
import discord
from discord.ext import commands
import datetime

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='userinfo', aliases=['ui', 'whois'])
    async def userinfo(self, ctx, member: discord.Member = None):
        """Get information about a user"""
        member = member or ctx.author
        
        embed = discord.Embed(
            title=f"User Information - {member.display_name}",
            color=member.color,
            timestamp=ctx.message.created_at
        )
        
        embed.set_thumbnail(url=member.avatar.url)
        embed.set_footer(text=f"ID: {member.id}")
        
        # User information
        embed.add_field(name="Username", value=f"{member}", inline=True)
        embed.add_field(name="Nickname", value=member.nick or "None", inline=True)
        embed.add_field(name="Bot?", value="Yes 🤖" if member.bot else "No 👤", inline=True)
        
        # Status information
        status_map = {
            discord.Status.online: "🟢 Online",
            discord.Status.idle: "🌙 Idle",
            discord.Status.dnd: "⛔ Do Not Disturb",
            discord.Status.offline: "⚫ Offline"
        }
        embed.add_field(name="Status", value=status_map.get(member.status, "Unknown"), inline=True)
        
        # Activity
        if member.activity:
            activity_type = member.activity.type.name.capitalize() if member.activity.type else "Playing"
            embed.add_field(name="Activity", value=f"{activity_type} {member.activity.name}", inline=True)
        else:
            embed.add_field(name="Activity", value="None", inline=True)
        
        # Time information
        embed.add_field(
            name="Joined Server",
            value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"),
            inline=False
        )
        embed.add_field(
            name="Joined Discord",
            value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            inline=False
        )
        
        # Roles
        roles = [role.mention for role in member.roles[1:]]  # Skip @everyone
        if roles:
            embed.add_field(
                name=f"Roles ({len(roles)})",
                value=" ".join(roles[:10]) + ("..." if len(roles) > 10 else ""),
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='serverinfo', aliases=['si', 'guildinfo'])
    async def serverinfo(self, ctx):
        """Get information about the server"""
        guild = ctx.guild
        
        embed = discord.Embed(
            title=guild.name,
            description=guild.description if guild.description else "No description",
            color=discord.Color.blue(),
            timestamp=ctx.message.created_at
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.set_footer(text=f"ID: {guild.id}")
        
        # General information
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="Created", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Region", value=str(guild.region).capitalize(), inline=True)
        
        # Member statistics
        total_members = guild.member_count
        bots = sum(1 for member in guild.members if member.bot)
        humans = total_members - bots
        
        embed.add_field(name="Total Members", value=total_members, inline=True)
        embed.add_field(name="Humans", value=humans, inline=True)
        embed.add_field(name="Bots", value=bots, inline=True)
        
        # Channel statistics
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        embed.add_field(name="Text Channels", value=text_channels, inline=True)
        embed.add_field(name="Voice Channels", value=voice_channels, inline=True)
        embed.add_field(name="Categories", value=categories, inline=True)
        
        # Other statistics
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Emojis", value=f"{len(guild.emojis)}/{guild.emoji_limit}", inline=True)
        embed.add_field(name="Boost Level", value=guild.premium_tier, inline=True)
        embed.add_field(name="Boosters", value=guild.premium_subscription_count, inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='avatar', aliases=['av', 'pfp'])
    async def avatar(self, ctx, member: discord.Member = None):
        """Get a user's avatar"""
        member = member or ctx.author
        
        embed = discord.Embed(
            title=f"{member.display_name}'s Avatar",
            color=member.color
        )
        embed.set_image(url=member.avatar.url)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))