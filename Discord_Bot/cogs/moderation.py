# cogs/moderation.py
import discord
from discord.ext import commands
import asyncio

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='kick')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Kick a member from the server"""
        if member == ctx.author:
            await ctx.send("❌ You can't kick yourself!")
            return
        
        if member == self.bot.user:
            await ctx.send("❌ Nice try, but I'm not kicking myself!")
            return
        
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ You can't kick someone with higher or equal roles!")
            return
        
        try:
            await member.kick(reason=f"{ctx.author}: {reason}")
            
            embed = discord.Embed(
                title="👢 Member Kicked",
                color=discord.Color.orange(),
                timestamp=ctx.message.created_at
            )
            embed.add_field(name="Member", value=f"{member} ({member.id})", inline=False)
            embed.add_field(name="Moderator", value=f"{ctx.author}", inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            
            # FIXED: Safe avatar handling for users with no custom avatar
            avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
            embed.set_thumbnail(url=avatar_url)
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to kick that member!")
    
    @commands.command(name='ban')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Ban a member from the server"""
        if member == ctx.author:
            await ctx.send("❌ You can't ban yourself!")
            return
        
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ You can't ban someone with higher or equal roles!")
            return
        
        try:
            await member.ban(reason=f"{ctx.author}: {reason}", delete_message_days=0)
            
            embed = discord.Embed(
                title="🔨 Member Banned",
                color=discord.Color.red(),
                timestamp=ctx.message.created_at
            )
            embed.add_field(name="Member", value=f"{member} ({member.id})", inline=False)
            embed.add_field(name="Moderator", value=f"{ctx.author}", inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            
            # FIXED: Safe avatar handling for users with no custom avatar
            avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
            embed.set_thumbnail(url=avatar_url)
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to ban that member!")
    
    @commands.command(name='clear', aliases=['purge'])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        """Clear a specified number of messages"""
        if amount < 1:
            await ctx.send("❌ Please specify a positive number of messages to clear!")
            return
        
        if amount > 100:
            await ctx.send("❌ You can only clear up to 100 messages at once!")
            return
        
        try:
            deleted = await ctx.channel.purge(limit=amount + 1)  # +1 for the command message
            msg = await ctx.send(f"✅ Cleared {len(deleted)-1} messages!")
            await asyncio.sleep(3)
            await msg.delete()
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to delete messages!")
    
    @commands.command(name='mute')
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, duration: int, *, reason="No reason provided"):
        """Mute a member for a specified duration (in minutes)"""
        # Find or create a muted role
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        
        if not muted_role:
            # Create muted role if it doesn't exist
            muted_role = await ctx.guild.create_role(
                name="Muted",
                reason="Created for muting members"
            )
            
            # Deny send messages permission in all text channels
            for channel in ctx.guild.channels:
                if isinstance(channel, discord.TextChannel):
                    await channel.set_permissions(muted_role, send_messages=False)
                elif isinstance(channel, discord.VoiceChannel):
                    await channel.set_permissions(muted_role, speak=False)
        
        try:
            await member.add_roles(muted_role, reason=f"{ctx.author}: {reason}")
            
            embed = discord.Embed(
                title="🔇 Member Muted",
                color=discord.Color.dark_gray(),
                timestamp=ctx.message.created_at
            )
            embed.add_field(name="Member", value=f"{member} ({member.id})", inline=False)
            embed.add_field(name="Moderator", value=f"{ctx.author}", inline=False)
            embed.add_field(name="Duration", value=f"{duration} minute(s)", inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            
            await ctx.send(embed=embed)
            
            # Unmute after duration
            await asyncio.sleep(duration * 60)
            
            if muted_role in member.roles:
                await member.remove_roles(muted_role, reason="Mute duration expired")
                try:
                    await member.send(f"You have been unmuted in {ctx.guild.name}")
                except:
                    pass
                    
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to mute that member!")

async def setup(bot):
    await bot.add_cog(Moderation(bot))