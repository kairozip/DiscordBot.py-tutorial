"""
server_manager.py — Control the bot's movement across servers

This cog provides commands to jump between servers, manage favorites,
and control server-hopping behavior from within Discord.
"""

import discord
from discord.ext import commands
from typing import Optional

class ServerManagerCog(commands.Cog):
    """
    🌍 Server Navigation Commands
    
    Control where the bot operates across different Discord servers.
    """
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name="listservers", aliases=["guilds", "serverlist"])
    async def list_servers(self, ctx: commands.Context):
        """
        List all servers the bot is in.
        
        Shows all servers the bot has access to, with member counts
        and indicators for favorites and current active server.
        """
        embed = discord.Embed(
            title=f"🌍 Servers I'm In ({len(self.bot.guilds)})",
            color=discord.Color.purple()
        )
        
        sorted_guilds = sorted(self.bot.guilds, key=lambda g: g.name)
        
        for guild in sorted_guilds:
            member_count = len([m for m in guild.members if not m.bot])
            bot_count = len([m for m in guild.members if m.bot])
            
            # Icons
            fav_icon = "⭐ " if guild.id in self.bot.favorite_servers else ""
            active_icon = "🔴 **ACTIVE** " if self.bot.active_guild == guild else ""
            
            embed.add_field(
                name=f"{fav_icon}{guild.name}",
                value=f"{active_icon}ID: `{guild.id}`\n👤 {member_count} members | 🤖 {bot_count} bots",
                inline=False
            )
        
        if self.bot.active_guild:
            embed.set_footer(text=f"📍 Currently active: {self.bot.active_guild.name}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="jump", aliases=["serverswitch", "switch"])
    @commands.is_owner()
    async def jump_to_server(self, ctx: commands.Context, *, target: str):
        """
        Jump to a different server (owner only).
        
        Moves the bot's active focus to another server.
        
        **Usage:**
        `!jump ServerName` - Focus on a server
        """
        target_lower = target.lower()
        target_guild = None
        
        # Check aliases first
        if target_lower in self.bot.server_aliases:
            guild_id = self.bot.server_aliases[target_lower]
            target_guild = self.bot.get_guild(guild_id)
        
        # Try by name
        if not target_guild:
            for guild in self.bot.guilds:
                if guild.name.lower() == target_lower:
                    target_guild = guild
                    break
        
        # Try partial match
        if not target_guild:
            matches = [g for g in self.bot.guilds if target_lower in g.name.lower()]
            if len(matches) == 1:
                target_guild = matches[0]
            elif len(matches) > 1:
                matches_list = "\n".join([f"• {g.name}" for g in matches[:10]])
                await ctx.send(f"❓ Multiple servers match '{target}':\n{matches_list}\n\nUse the exact name.")
                return
        
        if not target_guild:
            await ctx.send(f"❌ Could not find server '{target}'")
            return
        
        # Set active guild
        self.bot.active_guild = target_guild
        
        # Get a channel in the new server to announce arrival
        channel = self.bot.get_active_channel(target_guild.id)
        if channel:
            try:
                await channel.send(f"🌍 **Bot teleported here!**\nNow operating in {target_guild.name}")
            except:
                pass
        
        await ctx.send(f"✅ Active server set to: **{target_guild.name}**")
    
    @commands.command(name="jumpgoto", aliases=["jumpto", "gotoserver"])
    @commands.is_owner()
    async def jump_to_server_channel(self, ctx: commands.Context, target: str, channel: discord.TextChannel):
        """
        Jump to a different server and specific channel (owner only).
        
        **Usage:**
        `!jumpgoto ServerName #channel` - Jump to server and channel
        """
        target_lower = target.lower()
        target_guild = None
        
        # Check aliases first
        if target_lower in self.bot.server_aliases:
            guild_id = self.bot.server_aliases[target_lower]
            target_guild = self.bot.get_guild(guild_id)
        
        # Try by name
        if not target_guild:
            for guild in self.bot.guilds:
                if guild.name.lower() == target_lower:
                    target_guild = guild
                    break
        
        if not target_guild:
            await ctx.send(f"❌ Could not find server '{target}'")
            return
        
        # Verify channel is in the target server
        if channel.guild != target_guild:
            await ctx.send(f"❌ Channel {channel.mention} is not in {target_guild.name}")
            return
        
        # Check permissions
        if not channel.permissions_for(target_guild.me).send_messages:
            await ctx.send(f"❌ I don't have permission to speak in {channel.mention}")
            return
        
        # Set active guild and channel
        self.bot.active_guild = target_guild
        self.bot.active_channels[target_guild.id] = channel
        self.bot.response_channel[target_guild.id] = channel.id
        
        try:
            await channel.send(f"🌍 **Bot teleported here!**\nNow operating in {target_guild.name}")
        except:
            pass
        
        await ctx.send(f"✅ Moved to **{target_guild.name}** → {channel.mention}")
    
    @commands.command(name="autojump", aliases=["serverauto", "autoroam"])
    @commands.is_owner()
    async def auto_jump_mode(self, ctx: commands.Context, *, status: Optional[str] = None):
        """
        Enable or disable automatic server hopping (owner only).
        
        When enabled, the bot automatically follows messages across servers.
        
        **Usage:**
        `!autojump on` - Enable server hopping
        `!autojump off` - Disable server hopping
        """
        current = self.bot.server_hopping_mode
        
        if status is None:
            current_status = "ON" if current else "OFF"
            await ctx.send(f"🔀 Server hopping mode is currently: **{current_status}**\nUse `{ctx.prefix}autojump on/off` to change")
            return
        
        if status.lower() in ["on", "enable", "yes", "true", "1"]:
            self.bot.server_hopping_mode = True
            await ctx.send("🌐 **Server hopping mode ENABLED!**\nI will now follow conversations across all servers I'm in.")
        elif status.lower() in ["off", "disable", "no", "false", "0"]:
            self.bot.server_hopping_mode = False
            await ctx.send("📍 **Server hopping mode DISABLED.**\nI will stay in the current server.")
        else:
            await ctx.send(f"❌ Invalid status. Use `on` or `off`")
    
    @commands.command(name="serverdetail", aliases=["guilddetail", "serverstats"])
    async def server_detail(self, ctx: commands.Context, *, server_name: Optional[str] = None):
        """
        Display detailed information about a server.
        
        Shows member count, channel stats, boost level, and more.
        
        **Usage:**
        `!serverdetail` - Info about current server
        `!serverdetail ServerName` - Info about another server
        """
        guild = None
        
        if server_name:
            # Try to find the server
            for g in self.bot.guilds:
                if g.name.lower() == server_name.lower():
                    guild = g
                    break
            if not guild:
                await ctx.send(f"❌ Could not find server '{server_name}'")
                return
        else:
            guild = ctx.guild
        
        # Gather data
        total_members = guild.member_count
        humans = len([m for m in guild.members if not m.bot])
        bots = total_members - humans
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        roles = len(guild.roles)
        emojis = len(guild.emojis)
        stickers = len(guild.stickers)
        boosts = guild.premium_subscription_count or 0
        boost_level = guild.premium_tier
        verification = str(guild.verification_level).title()
        
        embed = discord.Embed(
            title=f"📊 Server Info: {guild.name}",
            color=discord.Color.blue()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(name="🆔 Server ID", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="👑 Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="📅 Created", value=guild.created_at.strftime("%b %d, %Y"), inline=True)
        
        embed.add_field(name="👥 Members", value=f"{humans} 👤 + {bots} 🤖 = **{total_members}**", inline=False)
        
        embed.add_field(name="📁 Channels", value=f"💬 {text_channels} | 🎤 {voice_channels} | 📂 {categories}", inline=True)
        embed.add_field(name="🎭 Roles", value=str(roles), inline=True)
        embed.add_field(name="😀 Emojis", value=f"{emojis} + {stickers} stickers", inline=True)
        
        embed.add_field(name="⚡ Boosts", value=f"Level {boost_level} ({boosts} boosts)", inline=False)
        embed.add_field(name="🔒 Verification", value=verification, inline=True)
        
        # Show active channel if this is the current active server
        if self.bot.active_guild == guild:
            active_channel = self.bot.get_active_channel(guild.id)
            if active_channel:
                embed.add_field(name="📍 Active Channel", value=active_channel.mention, inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="favserver", aliases=["fav", "favoriteserver"])
    @commands.is_owner()
    async def favorite_server(self, ctx: commands.Context, action: str, *, server_name: Optional[str] = None):
        """
        Manage favorite servers for quick access (owner only).
        
        **Usage:**
        `!favserver add ServerName` - Add to favorites
        `!favserver remove ServerName` - Remove from favorites
        `!favserver list` - List all favorites
        """
        
        if action.lower() == "list":
            if not self.bot.favorite_servers:
                await ctx.send("📌 No favorite servers yet. Use `!favserver add ServerName` to add some!")
                return
            
            favorites = []
            for guild_id in self.bot.favorite_servers:
                guild = self.bot.get_guild(guild_id)
                if guild:
                    favorites.append(guild.name)
            
            embed = discord.Embed(
                title="⭐ Favorite Servers",
                description="\n".join([f"• {name}" for name in favorites]),
                color=discord.Color.gold()
            )
            await ctx.send(embed=embed)
            return
        
        if not server_name:
            await ctx.send(f"❌ Please specify a server name.\nUsage: `{ctx.prefix}favserver {action} ServerName`")
            return
        
        # Find the server
        target_guild = None
        for guild in self.bot.guilds:
            if guild.name.lower() == server_name.lower():
                target_guild = guild
                break
        
        if not target_guild:
            await ctx.send(f"❌ Could not find server '{server_name}'")
            return
        
        if action.lower() == "add":
            if target_guild.id in self.bot.favorite_servers:
                await ctx.send(f"⭐ {target_guild.name} is already in favorites!")
            else:
                self.bot.favorite_servers.append(target_guild.id)
                await ctx.send(f"⭐ Added **{target_guild.name}** to favorites!")
        
        elif action.lower() == "remove":
            if target_guild.id in self.bot.favorite_servers:
                self.bot.favorite_servers.remove(target_guild.id)
                await ctx.send(f"🗑️ Removed **{target_guild.name}** from favorites!")
            else:
                await ctx.send(f"📌 {target_guild.name} is not in favorites.")
        
        else:
            await ctx.send(f"❌ Unknown action. Use `add`, `remove`, or `list`")
    
    @commands.command(name="serveralias", aliases=["sralias", "servernick"])
    @commands.is_owner()
    async def server_alias(self, ctx: commands.Context, alias: str, *, server_name: str):
        """
        Create a shortcut alias for a server (owner only).
        
        **Usage:**
        `!serveralias main MyAwesomeServer` - Now you can use `!jump main`
        """
        # Find the server
        target_guild = None
        for guild in self.bot.guilds:
            if guild.name.lower() == server_name.lower():
                target_guild = guild
                break
        
        if not target_guild:
            await ctx.send(f"❌ Could not find server '{server_name}'")
            return
        
        self.bot.server_aliases[alias.lower()] = target_guild.id
        await ctx.send(f"🏷️ Alias **'{alias}'** now points to **{target_guild.name}**")
    
    @commands.command(name="serverunalias", aliases=["srunalias", "removeserveralias"])
    @commands.is_owner()
    async def remove_server_alias(self, ctx: commands.Context, alias: str):
        """
        Remove a server alias (owner only).
        
        **Usage:** `!serverunalias main`
        """
        if alias.lower() in self.bot.server_aliases:
            del self.bot.server_aliases[alias.lower()]
            await ctx.send(f"🗑️ Removed alias **'{alias}'**")
        else:
            await ctx.send(f"❌ Alias '{alias}' not found")
    
    @commands.command(name="activeserver", aliases=["currentserver", "whereami"])
    async def active_server(self, ctx: commands.Context):
        """
        Show which server the bot is currently focused on.
        
        Displays the active server and channel information.
        """
        if not self.bot.active_guild:
            await ctx.send("❌ No active server set. Use `!jump ServerName` to set one.")
            return
        
        embed = discord.Embed(
            title="📍 Active Server Location",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="🌍 Server",
            value=f"**{self.bot.active_guild.name}** (ID: `{self.bot.active_guild.id}`)",
            inline=False
        )
        
        channel = self.bot.get_active_channel(self.bot.active_guild.id)
        if channel:
            embed.add_field(
                name="📍 Channel",
                value=f"{channel.mention}",
                inline=False
            )
        
        wandering = self.bot.wandering_mode.get(self.bot.active_guild.id, False)
        embed.add_field(
            name="🚶 Wandering Mode",
            value="✅ ON" if wandering else "❌ OFF",
            inline=True
        )
        
        embed.add_field(
            name="🌐 Server Hopping",
            value="✅ ON" if self.bot.server_hopping_mode else "❌ OFF",
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="testjump", aliases=["testserver"])
    async def test_server_jump(self, ctx: commands.Context):
        """
        Test if server jumping is working.
        
        Shows all available servers and their IDs for troubleshooting.
        """
        embed = discord.Embed(
            title="🔧 Server Jump Troubleshooting",
            description="Here are all the servers I can jump to:",
            color=discord.Color.orange()
        )
        
        for guild in sorted(self.bot.guilds, key=lambda g: g.name):
            # Check if this guild is set as active
            is_active = "🔴 **ACTIVE** " if self.bot.active_guild == guild else ""
            
            # Count accessible channels
            accessible = len([c for c in guild.text_channels if c.permissions_for(guild.me).send_messages])
            
            embed.add_field(
                name=f"{guild.name}",
                value=f"{is_active}ID: `{guild.id}`\nMembers: {guild.member_count}\nAccessible channels: {accessible}",
                inline=False
            )
        
        embed.set_footer(text="Use !jump SERVERNAME to jump to any server above")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    """Load the server manager cog"""
    await bot.add_cog(ServerManagerCog(bot))
    print("✅ ServerManagerCog loaded — Bot can now hop between servers!")