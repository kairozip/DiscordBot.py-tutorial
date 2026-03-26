"""
channel_manager.py — Control the bot's movement through channels

This cog provides commands to manually move the bot,
enable wandering mode, and check current location.
"""

import discord
from discord.ext import commands
from typing import Optional

class ChannelManagerCog(commands.Cog):
    """
    🚶 Channel Movement Control
    
    Commands to control where the bot responds and how it moves through channels.
    """
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name="goto", aliases=["move", "go"])
    @commands.has_permissions(manage_channels=True)
    async def goto_channel(self, ctx: commands.Context, *, channel: discord.TextChannel):
        """
        Move the bot to a specific channel.
        
        After this command, the bot will respond in the specified channel
        until moved again or until wandering mode is enabled.
        
        **Usage:** `!goto #channel-name`
        """
        # Check permissions in target channel
        if not channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.send(f"❌ I don't have permission to send messages in {channel.mention}")
            return
        
        # Update active channel
        self.bot.active_channels[ctx.guild.id] = channel
        self.bot.response_channel[ctx.guild.id] = channel.id
        
        # If wandering mode was on, turn it off (manual override)
        if self.bot.wandering_mode.get(ctx.guild.id, False):
            self.bot.wandering_mode[ctx.guild.id] = False
            await ctx.send(f"📍 Moved to {channel.mention} and **disabled wandering mode**")
        else:
            await ctx.send(f"📍 Moved to {channel.mention}")
    
    @commands.command(name="wander", aliases=["roam", "follow"])
    @commands.has_permissions(administrator=True)
    async def wander_mode(self, ctx: commands.Context, *, status: Optional[str] = None):
        """
        Enable or disable wandering mode.
        
        When wandering mode is ON, the bot automatically moves to wherever
        messages are sent and responds there.
        
        **Usage:**
        `!wander on` - Enable wandering mode
        `!wander off` - Disable wandering mode
        `!wander` - Toggle current mode
        """
        current = self.bot.wandering_mode.get(ctx.guild.id, False)
        
        if status is None:
            # Toggle
            new_status = not current
        elif status.lower() in ["on", "enable", "yes", "true", "1"]:
            new_status = True
        elif status.lower() in ["off", "disable", "no", "false", "0"]:
            new_status = False
        else:
            await ctx.send(f"❌ Invalid status. Use `on` or `off`.")
            return
        
        self.bot.wandering_mode[ctx.guild.id] = new_status
        
        if new_status:
            await ctx.send("🚶 **Wandering mode ENABLED**\n*I will follow conversations wherever they happen.*")
        else:
            await ctx.send("📍 **Wandering mode DISABLED**\n*I will stay in the current channel unless moved manually.*")
    
    @commands.command(name="where", aliases=["location", "here"])
    async def where_am_i(self, ctx: commands.Context):
        """
        Show where the bot is currently configured to respond.
        
        Displays the current active channel and wandering mode status.
        """
        channel = self.bot.get_active_channel(ctx.guild.id)
        wandering = self.bot.wandering_mode.get(ctx.guild.id, False)
        
        embed = discord.Embed(
            title="📍 Bot Location",
            color=discord.Color.blue()
        )
        
        if channel:
            embed.add_field(
                name="Active Channel",
                value=f"{channel.mention}",
                inline=False
            )
        else:
            embed.add_field(
                name="Active Channel",
                value="No active channel set",
                inline=False
            )
        
        embed.add_field(
            name="Wandering Mode",
            value="✅ **ON** - Following conversations" if wandering else "❌ **OFF** - Stationary",
            inline=False
        )
        
        embed.set_footer(text=f"Use {ctx.prefix}goto to move me | {ctx.prefix}wander to toggle")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="channels", aliases=["listchannels"])
    @commands.has_permissions(manage_channels=True)
    async def list_channels(self, ctx: commands.Context):
        """
        List all channels the bot can see and access.
        
        Shows which channels the bot has permission to speak in.
        """
        accessible_channels = []
        inaccessible_channels = []
        
        for channel in ctx.guild.text_channels:
            if channel.permissions_for(ctx.guild.me).send_messages:
                accessible_channels.append(channel)
            else:
                inaccessible_channels.append(channel)
        
        embed = discord.Embed(
            title=f"📡 Accessible Channels in {ctx.guild.name}",
            color=discord.Color.green()
        )
        
        if accessible_channels:
            channel_list = "\n".join([f"• {ch.mention}" for ch in accessible_channels[:20]])
            if len(accessible_channels) > 20:
                channel_list += f"\n*... and {len(accessible_channels) - 20} more*"
            embed.add_field(
                name=f"✅ Can Speak ({len(accessible_channels)})",
                value=channel_list,
                inline=False
            )
        
        if inaccessible_channels and len(inaccessible_channels) <= 20:
            channel_list = "\n".join([f"• #{ch.name}" for ch in inaccessible_channels[:10]])
            embed.add_field(
                name=f"❌ Cannot Speak ({len(inaccessible_channels)})",
                value=channel_list,
                inline=False
            )
        
        embed.set_footer(text=f"Current active channel: {self.bot.get_active_channel(ctx.guild.id).mention if self.bot.get_active_channel(ctx.guild.id) else 'None'}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="hop", aliases=["jump"])
    async def hop_to_last(self, ctx: commands.Context):
        """
        Hop to the last channel where a message was received.
        
        Useful for following conversations after wandering mode is off.
        """
        last_channel_id = self.bot.last_message_channel.get(ctx.guild.id)
        
        if not last_channel_id:
            await ctx.send("❌ No recent message activity tracked.")
            return
        
        last_channel = ctx.guild.get_channel(last_channel_id)
        
        if not last_channel:
            await ctx.send("❌ Last channel no longer exists.")
            return
        
        if not last_channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.send(f"❌ I don't have permission to speak in {last_channel.mention}")
            return
        
        self.bot.active_channels[ctx.guild.id] = last_channel
        self.bot.response_channel[ctx.guild.id] = last_channel.id
        
        await ctx.send(f"🦘 Hopped to {last_channel.mention}")


async def setup(bot: commands.Bot):
    """Load the channel manager cog"""
    await bot.add_cog(ChannelManagerCog(bot))
    print("✅ ChannelManagerCog loaded — Bot can now move through channels!")