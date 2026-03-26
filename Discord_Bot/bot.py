# bot.py
import discord
from discord.ext import commands
import asyncio
import logging
import threading
import sys
from config import Config
from typing import Optional, Dict, List, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        intents.guild_messages = True
        
        super().__init__(
            command_prefix=Config.PREFIX,
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        
        # Extension loading
        self.initial_extensions = [
            'cogs.help',
            'cogs.basic',
            'cogs.moderation',
            'cogs.fun',
            'cogs.utility',
            'cogs.terminal',
            'cogs.channel_manager',
            'cogs.server_manager'  # NEW: Server management cog
        ]
        
        # Terminal stuff
        self.terminal_thread = None
        self.running = True
        self.terminal_channel = None
        
        # Channel management
        self.active_channels: Dict[int, discord.TextChannel] = {}  # guild_id -> active channel
        self.channel_history: Dict[int, List[int]] = {}  # guild_id -> list of channel IDs visited
        self.wandering_mode: Dict[int, bool] = {}  # guild_id -> wandering enabled
        self.response_channel: Dict[int, int] = {}  # guild_id -> channel_id for responses
        
        # SERVER MANAGEMENT - NEW
        self.active_guild: Optional[discord.Guild] = None  # Currently focused guild
        self.guild_history: List[int] = []  # History of visited guilds
        self.server_hopping_mode: bool = False  # Auto-follow across servers
        self.last_message_guild: Dict[int, int] = {}  # guild_id -> last message timestamp
        self.favorite_servers: List[int] = []  # Saved server IDs for quick access
        self.server_aliases: Dict[str, int] = {}  # nickname -> guild_id mapping
        
        # Uptime tracking
        self.start_time = None
        
        # Auto-response tracking
        self.last_message_channel: Dict[int, int] = {}  # guild_id -> last channel where bot responded
        
    async def setup_hook(self):
        """Load extensions when bot starts"""
        print("\n" + "="*60)
        print("🔧 INITIALIZING BOT EXTENSIONS")
        print("="*60)
        
        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
                logger.info(f"✅ Loaded extension: {extension}")
                print(f"  ✓ {extension}")
            except Exception as e:
                logger.error(f"❌ Failed to load extension {extension}: {e}")
                print(f"  ✗ {extension}: {e}")
        
        try:
            await self.tree.sync()
            logger.info("✅ Synced slash commands")
            print("  ✓ Slash commands synced")
        except Exception as e:
            logger.error(f"❌ Failed to sync slash commands: {e}")
            print(f"  ✗ Slash commands sync failed: {e}")
        
        self.start_time = discord.utils.utcnow()
        self.start_terminal_input()
        
        print("="*60 + "\n")
    
    def start_terminal_input(self):
        """Start a thread to read terminal input with server-hopping commands"""
        def terminal_reader():
            while self.running:
                try:
                    user_input = input()
                    
                    # SERVER MOVEMENT COMMANDS - NEW
                    if user_input.lower().startswith('joinserver ') or user_input.lower().startswith('goto '):
                        # Parse: goto <server_name> or goto <server_name> #channel
                        parts = user_input.split(' ', 2)
                        if len(parts) >= 2:
                            target = parts[1]
                            channel_spec = parts[2] if len(parts) >= 3 else None
                            asyncio.run_coroutine_threadsafe(
                                self.terminal_goto_server(target, channel_spec),
                                self.loop
                            )
                    elif user_input.lower().startswith('servers'):
                        asyncio.run_coroutine_threadsafe(
                            self.terminal_list_servers(),
                            self.loop
                        )
                    elif user_input.lower().startswith('serverhop'):
                        parts = user_input.split()
                        if len(parts) > 1 and parts[1].lower() in ['on', 'off']:
                            asyncio.run_coroutine_threadsafe(
                                self.terminal_server_hop_mode(parts[1].lower()),
                                self.loop
                            )
                        else:
                            asyncio.run_coroutine_threadsafe(
                                self.terminal_server_hop_mode(None),
                                self.loop
                            )
                    elif user_input.lower().startswith('serverinfo'):
                        target = user_input[10:].strip() if len(user_input) > 10 else None
                        asyncio.run_coroutine_threadsafe(
                            self.terminal_server_info(target),
                            self.loop
                        )
                    elif user_input.lower().startswith('favorite ') or user_input.lower().startswith('fav '):
                        parts = user_input.split()
                        if len(parts) >= 2:
                            action = parts[1].lower()
                            if action == 'add' and len(parts) >= 3:
                                server_name = ' '.join(parts[2:])
                                asyncio.run_coroutine_threadsafe(
                                    self.terminal_favorite_add(server_name),
                                    self.loop
                                )
                            elif action == 'remove' and len(parts) >= 3:
                                server_name = ' '.join(parts[2:])
                                asyncio.run_coroutine_threadsafe(
                                    self.terminal_favorite_remove(server_name),
                                    self.loop
                                )
                            elif action == 'list':
                                asyncio.run_coroutine_threadsafe(
                                    self.terminal_favorite_list(),
                                    self.loop
                                )
                    elif user_input.lower().startswith('alias '):
                        parts = user_input.split()
                        if len(parts) >= 3:
                            alias = parts[1]
                            server_name = ' '.join(parts[2:])
                            asyncio.run_coroutine_threadsafe(
                                self.terminal_add_alias(alias, server_name),
                                self.loop
                            )
                    # Channel movement commands (existing)
                    elif user_input.lower().startswith('gotochannel '):
                        channel_name = user_input[12:].strip()
                        asyncio.run_coroutine_threadsafe(
                            self.terminal_goto_channel(channel_name),
                            self.loop
                        )
                    elif user_input.lower().startswith('wander '):
                        guild_name = user_input[7:].strip()
                        asyncio.run_coroutine_threadsafe(
                            self.terminal_wander_mode(guild_name),
                            self.loop
                        )
                    elif user_input.lower() == 'where':
                        asyncio.run_coroutine_threadsafe(
                            self.terminal_where_am_i(),
                            self.loop
                        )
                    elif user_input.lower() == 'channels':
                        asyncio.run_coroutine_threadsafe(
                            self.terminal_list_channels(),
                            self.loop
                        )
                    elif user_input.lower() == 'exit':
                        print("\n🛑 Shutting down bot...")
                        self.running = False
                        asyncio.run_coroutine_threadsafe(self.close(), self.loop)
                        break
                    elif user_input.lower() == 'help':
                        self.print_terminal_help()
                    elif user_input.lower() == 'status':
                        asyncio.run_coroutine_threadsafe(
                            self.terminal_status(),
                            self.loop
                        )
                    elif user_input.lower() == 'cogs':
                        self.print_cogs_list()
                    else:
                        # Send to Discord
                        asyncio.run_coroutine_threadsafe(
                            self.send_terminal_message(user_input),
                            self.loop
                        )
                except EOFError:
                    print("\n🛑 EOF detected. Shutting down...")
                    self.running = False
                    asyncio.run_coroutine_threadsafe(self.close(), self.loop)
                    break
                except Exception as e:
                    print(f"❌ Terminal input error: {e}")
        
        self.terminal_thread = threading.Thread(target=terminal_reader, daemon=True)
        self.terminal_thread.start()
        self.print_terminal_help()
    
    def print_terminal_help(self):
        """Print terminal command help"""
        print("\n" + "="*60)
        print("📝 TERMINAL COMMANDS")
        print("="*60)
        print("  🏠 SERVER NAVIGATION:")
        print("    • goto <server> [#channel]  - Jump to a server (optional channel)")
        print("    • servers                   - List all servers the bot is in")
        print("    • serverhop on/off          - Enable/disable auto server hopping")
        print("    • serverinfo [server]       - Show detailed server info")
        print("    • favorite add/remove/list  - Manage favorite servers")
        print("    • alias <nick> <server>     - Create shortcut name for server")
        print("")
        print("  📍 CHANNEL NAVIGATION:")
        print("    • gotochannel <channel>     - Move to specific channel")
        print("    • wander <guild>            - Enable wandering mode in a guild")
        print("    • where                     - Show current location")
        print("    • channels                  - List all channels in current server")
        print("")
        print("  📊 GENERAL:")
        print("    • status                    - Show bot status")
        print("    • cogs                      - List loaded cogs")
        print("    • help                      - Show this help")
        print("    • exit                      - Shutdown bot")
        print("="*60 + "\n")
    
    def print_cogs_list(self):
        """Print loaded cogs in terminal"""
        print(f"\n📦 Loaded Cogs ({len(self.cogs)}):")
        for cog_name in sorted(self.cogs.keys()):
            cog = self.cogs[cog_name]
            cmd_count = len([cmd for cmd in cog.get_commands() if not cmd.hidden])
            print(f"  • {cog_name}: {cmd_count} commands")
        print()
    
    async def terminal_goto_server(self, target: str, channel_spec: Optional[str] = None):
        """Jump to a specific server from terminal"""
        target_lower = target.lower()
        target_guild = None
        
        # Try to find by alias first
        if target_lower in self.server_aliases:
            guild_id = self.server_aliases[target_lower]
            target_guild = self.get_guild(guild_id)
        
        # Try by name
        if not target_guild:
            for guild in self.guilds:
                if guild.name.lower() == target_lower:
                    target_guild = guild
                    break
        
        # Try by partial name match
        if not target_guild:
            matches = [g for g in self.guilds if target_lower in g.name.lower()]
            if matches:
                if len(matches) == 1:
                    target_guild = matches[0]
                else:
                    print(f"❌ Multiple servers match '{target}':")
                    for match in matches:
                        print(f"  • {match.name}")
                    return
        
        if not target_guild:
            print(f"❌ Could not find server '{target}'")
            return
        
        # Set active guild
        self.active_guild = target_guild
        if target_guild.id not in self.guild_history:
            self.guild_history.append(target_guild.id)
        
        # Handle channel specification
        if channel_spec:
            channel_name = channel_spec.lstrip('#')
            for channel in target_guild.text_channels:
                if channel.name.lower() == channel_name.lower():
                    if channel.permissions_for(target_guild.me).send_messages:
                        self.active_channels[target_guild.id] = channel
                        self.response_channel[target_guild.id] = channel.id
                        await channel.send(f"🌍 **Bot teleported here via terminal command**\n*Now operating in {target_guild.name}*")
                        print(f"✅ Moved to {target_guild.name} → #{channel.name}")
                        return
                    else:
                        print(f"❌ No permission to speak in #{channel_name}")
                        return
            
            print(f"❌ Could not find channel '{channel_name}' in {target_guild.name}")
            return
        
        # No channel specified, just announce server arrival
        print(f"✅ Active server set to: {target_guild.name}")
        current_channel = self.get_active_channel(target_guild.id)
        if current_channel:
            await current_channel.send(f"🌍 **Bot now operating in this server**\n*Use `{Config.PREFIX}goto #channel` to move around*")
            print(f"📍 Currently in: #{current_channel.name}")
    
    async def terminal_list_servers(self):
        """List all servers the bot is in with details"""
        print("\n🌍 SERVERS I'M IN:")
        print("="*60)
        
        for i, guild in enumerate(sorted(self.guilds, key=lambda g: g.name), 1):
            # Count members
            member_count = len([m for m in guild.members if not m.bot])
            bot_count = len([m for m in guild.members if m.bot])
            
            # Check if favorite
            is_favorite = "⭐ " if guild.id in self.favorite_servers else "   "
            
            # Check if current active
            is_active = "🔴 ACTIVE" if self.active_guild == guild else ""
            
            print(f"{is_favorite}{i:2}. {guild.name}")
            print(f"      ID: {guild.id} | Members: {member_count} 👤 + {bot_count} 🤖")
            if is_active:
                print(f"      {is_active}")
            print()
        
        print(f"Total: {len(self.guilds)} servers")
        if self.active_guild:
            print(f"\n📍 CURRENT ACTIVE: {self.active_guild.name}")
        print("="*60 + "\n")
    
    async def terminal_server_hop_mode(self, status: Optional[str] = None):
        """Enable or disable automatic server hopping"""
        if status == 'on':
            self.server_hopping_mode = True
            print("🚀 Server hopping mode ENABLED — I'll follow messages across servers!")
            if self.active_guild:
                channel = self.get_active_channel(self.active_guild.id)
                if channel:
                    await channel.send("🌐 **Server hopping mode enabled!** I'll now follow conversations across all servers I'm in.")
        elif status == 'off':
            self.server_hopping_mode = False
            print("📍 Server hopping mode DISABLED — I'll stay in one server.")
            if self.active_guild:
                channel = self.get_active_channel(self.active_guild.id)
                if channel:
                    await channel.send("📍 **Server hopping mode disabled.** I'll stay in this server.")
        else:
            current = "ON" if self.server_hopping_mode else "OFF"
            print(f"🔀 Server hopping mode is currently: {current}")
            print("Use 'serverhop on' or 'serverhop off' to change")
    
    async def terminal_server_info(self, target: Optional[str] = None):
        """Show detailed information about a server"""
        guild = None
        
        if target:
            # Try to find by name
            target_lower = target.lower()
            for g in self.guilds:
                if g.name.lower() == target_lower:
                    guild = g
                    break
            if not guild:
                print(f"❌ Could not find server '{target}'")
                return
        else:
            guild = self.active_guild
            if not guild:
                print("❌ No active server set")
                return
        
        # Gather server info
        channels = len([c for c in guild.text_channels if c.permissions_for(guild.me).send_messages])
        total_channels = len(guild.channels)
        roles = len(guild.roles)
        emojis = len(guild.emojis)
        boosts = guild.premium_subscription_count or 0
        verification = guild.verification_level
        
        print(f"\n📊 SERVER INFO: {guild.name}")
        print("="*60)
        print(f"  • ID: {guild.id}")
        print(f"  • Owner: {guild.owner} (ID: {guild.owner_id})")
        print(f"  • Created: {guild.created_at.strftime('%Y-%m-%d')}")
        print(f"  • Members: {guild.member_count} total")
        print(f"  • Channels: {total_channels} total ({channels} accessible)")
        print(f"  • Roles: {roles}")
        print(f"  • Emojis: {emojis}")
        print(f"  • Boosts: {boosts}")
        print(f"  • Verification: {verification}")
        
        # Show active channel
        active_channel = self.get_active_channel(guild.id)
        if active_channel:
            print(f"  • Active channel: #{active_channel.name}")
        
        print("="*60 + "\n")
    
    async def terminal_favorite_add(self, server_name: str):
        """Add a server to favorites"""
        for guild in self.guilds:
            if guild.name.lower() == server_name.lower():
                if guild.id not in self.favorite_servers:
                    self.favorite_servers.append(guild.id)
                    print(f"⭐ Added {guild.name} to favorites!")
                else:
                    print(f"⭐ {guild.name} is already in favorites!")
                return
        
        print(f"❌ Could not find server '{server_name}'")
    
    async def terminal_favorite_remove(self, server_name: str):
        """Remove a server from favorites"""
        for guild in self.guilds:
            if guild.name.lower() == server_name.lower():
                if guild.id in self.favorite_servers:
                    self.favorite_servers.remove(guild.id)
                    print(f"🗑️ Removed {guild.name} from favorites!")
                else:
                    print(f"📌 {guild.name} was not in favorites")
                return
        
        print(f"❌ Could not find server '{server_name}'")
    
    async def terminal_favorite_list(self):
        """List favorite servers"""
        if not self.favorite_servers:
            print("📌 No favorite servers yet. Use 'favorite add <server>' to add some!")
            return
        
        print("\n⭐ FAVORITE SERVERS:")
        print("="*50)
        for guild_id in self.favorite_servers:
            guild = self.get_guild(guild_id)
            if guild:
                print(f"  • {guild.name}")
        print("="*50 + "\n")
    
    async def terminal_add_alias(self, alias: str, server_name: str):
        """Add a nickname/alias for a server"""
        for guild in self.guilds:
            if guild.name.lower() == server_name.lower():
                self.server_aliases[alias.lower()] = guild.id
                print(f"🏷️ Alias '{alias}' now points to {guild.name}")
                return
        
        print(f"❌ Could not find server '{server_name}'")
    
    async def terminal_goto_channel(self, channel_name: str):
        """Move bot to a specific channel within current server"""
        if not self.active_guild:
            print("❌ No active server set. Use 'goto <server>' first")
            return
        
        for channel in self.active_guild.text_channels:
            if channel.name.lower() == channel_name.lower():
                if channel.permissions_for(self.active_guild.me).send_messages:
                    self.active_channels[self.active_guild.id] = channel
                    self.response_channel[self.active_guild.id] = channel.id
                    await channel.send("🎯 **Bot relocated here via terminal command**")
                    print(f"✅ Moved to #{channel.name} in {self.active_guild.name}")
                    return
                else:
                    print(f"❌ No permission to speak in #{channel_name}")
                    return
        
        print(f"❌ Could not find channel '{channel_name}' in {self.active_guild.name}")
    
    async def terminal_wander_mode(self, guild_name: str):
        """Enable wandering mode for a specific guild"""
        for guild in self.guilds:
            if guild.name.lower() == guild_name.lower():
                self.wandering_mode[guild.id] = True
                print(f"🚶 Wandering mode ENABLED for {guild.name}")
                await self.get_active_channel(guild.id).send("🚶 **Wandering mode enabled!** I'll respond wherever messages are sent in this server.")
                return
        
        print(f"❌ Could not find guild named '{guild_name}'")
    
    async def terminal_where_am_i(self):
        """Show current location across all servers"""
        print("\n📍 CURRENT LOCATION:")
        print("="*60)
        
        if self.active_guild:
            print(f"🌍 Active Server: {self.active_guild.name}")
            channel = self.get_active_channel(self.active_guild.id)
            if channel:
                print(f"📍 Current Channel: #{channel.name}")
        else:
            print("🌍 No active server set")
        
        print("\n📊 All Servers:")
        for guild in self.guilds:
            channel = self.get_active_channel(guild.id)
            if channel:
                status = "🔴 ACTIVE" if self.active_guild == guild else "   "
                print(f"  {status} {guild.name} -> #{channel.name}")
            else:
                print(f"     {guild.name} -> No active channel")
        
        print("="*60 + "\n")
    
    async def terminal_list_channels(self):
        """List all available channels in current server"""
        if not self.active_guild:
            print("❌ No active server set. Use 'goto <server>' first")
            return
        
        print(f"\n📡 CHANNELS IN {self.active_guild.name}:")
        print("="*60)
        
        text_channels = [ch for ch in self.active_guild.text_channels 
                        if ch.permissions_for(self.active_guild.me).send_messages]
        
        for channel in text_channels:
            print(f"  • #{channel.name} (ID: {channel.id})")
        
        print(f"\nTotal accessible: {len(text_channels)} channels")
        print("="*60 + "\n")
    
    async def terminal_status(self):
        """Show detailed bot status"""
        total_commands = sum(len([cmd for cmd in cog.get_commands() if not cmd.hidden]) 
                            for cog in self.cogs.values())
        
        print(f"\n📊 BOT STATUS:")
        print("="*60)
        print(f"  • User: {self.user} (ID: {self.user.id})")
        print(f"  • Guilds: {len(self.guilds)}")
        print(f"  • Uptime: {self.get_uptime()}")
        print(f"  • Commands: {total_commands}")
        print(f"  • Cogs: {len(self.cogs)}")
        print(f"  • Wandering mode active in: {len([g for g, w in self.wandering_mode.items() if w])} servers")
        print(f"  • Server hopping mode: {'ON' if self.server_hopping_mode else 'OFF'}")
        print(f"  • Favorite servers: {len(self.favorite_servers)}")
        print(f"  • Server aliases: {len(self.server_aliases)}")
        print("="*60 + "\n")
    
    def get_uptime(self):
        """Get bot uptime as a formatted string"""
        if not self.start_time:
            return "Unknown"
        
        now = discord.utils.utcnow()
        delta = now - self.start_time
        
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        seconds = delta.seconds % 60
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0 or days > 0:
            parts.append(f"{hours}h")
        if minutes > 0 or hours > 0 or days > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        
        return " ".join(parts)
    
    def get_active_channel(self, guild_id: int) -> Optional[discord.TextChannel]:
        """Get the active channel for a guild"""
        if guild_id in self.active_channels:
            channel = self.active_channels[guild_id]
            if channel.guild.get_channel(channel.id) and channel.permissions_for(channel.guild.me).send_messages:
                return channel
        
        guild = self.get_guild(guild_id)
        if guild:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    self.active_channels[guild_id] = channel
                    return channel
        
        return None
    
    async def send_terminal_message(self, message_text: str):
        """Send a message from terminal to the active Discord channel"""
        if not self.active_guild:
            print("❌ No active server set. Use 'goto <server>' first")
            return
        
        channel = self.get_active_channel(self.active_guild.id)
        if channel:
            try:
                if len(message_text) > 100:
                    embed = discord.Embed(
                        description=f"```\n{message_text}\n```",
                        color=discord.Color.dark_gray()
                    )
                    embed.set_author(name="💻 Terminal Input", icon_url=self.user.display_avatar.url)
                    await channel.send(embed=embed)
                else:
                    await channel.send(f"💻 **Terminal**: {message_text}")
                print(f"📤 Sent to {self.active_guild.name} → #{channel.name}: {message_text[:50]}{'...' if len(message_text) > 50 else ''}")
            except Exception as e:
                print(f"❌ Failed to send message: {e}")
        else:
            print("❌ No accessible text channel found in this server")
    
    async def on_ready(self):
        """Triggered when bot connects to Discord"""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guilds")
        
        # Set custom status
        activity_type = Config.ACTIVITY_TYPE.lower()
        activity_name = Config.ACTIVITY_NAME
        
        if activity_type == 'listening':
            activity = discord.Activity(type=discord.ActivityType.listening, name=activity_name)
        elif activity_type == 'watching':
            activity = discord.Activity(type=discord.ActivityType.watching, name=activity_name)
        elif activity_type == 'competing':
            activity = discord.Activity(type=discord.ActivityType.competing, name=activity_name)
        elif activity_type == 'streaming':
            activity = discord.Streaming(name=activity_name, url='https://twitch.tv/yourchannel')
        else:
            activity = discord.Game(name=activity_name)
            
        await self.change_presence(status=discord.Status.online, activity=activity)
        
        # Initialize all servers
        for guild in self.guilds:
            # Find best channel for responses
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    self.active_channels[guild.id] = channel
                    self.response_channel[guild.id] = channel.id
                    break
            
            # Initialize settings
            self.wandering_mode[guild.id] = False
            self.channel_history[guild.id] = []
        
        # Set first guild as active if none
        if self.guilds and not self.active_guild:
            self.active_guild = self.guilds[0]
        
        # Count total commands
        total_commands = sum(len([cmd for cmd in cog.get_commands() if not cmd.hidden]) 
                            for cog in self.cogs.values())
        
        print("\n" + "="*70)
        print(f"🤖 BOT ONLINE: {self.user}")
        print(f"📡 Connected to {len(self.guilds)} servers")
        print(f"📦 Loaded {len(self.cogs)} cogs with {total_commands} commands")
        print(f"💻 Command prefix: {Config.PREFIX}")
        print("="*70)
        print("\n🌍 SERVER NAVIGATION:")
        print("   • 'goto <server> [#channel]' - Jump to any server")
        print("   • 'servers' - List all servers")
        print("   • 'serverhop on/off' - Auto-follow across servers")
        print("   • 'favorite add/remove/list' - Manage favorites")
        print("   • 'alias <nick> <server>' - Create shortcuts")
        print("\n📍 CHANNEL NAVIGATION:")
        print("   • 'gotochannel <channel>' - Move within current server")
        print("   • 'wander <server>' - Enable auto channel following")
        print("   • 'where' - Show current location")
        print("\n📝 Type 'help' for full command list")
        print("="*70 + "\n")
        
        # Send startup message to first server
        if self.active_guild:
            channel = self.get_active_channel(self.active_guild.id)
            if channel:
                try:
                    await channel.send(f"🤖 **Bot Online!**\nBot is Ready To Use In {len(self.guilds)} servers.\nUse `{Config.PREFIX}help` to get started.")
                except:
                    pass
    
    async def on_message(self, message):
        """Process messages and commands with server-hopping capability"""
        if message.author.id == self.user.id:
            return
        
        # Server hopping logic
        if message.guild:
            # Update last message tracking
            self.last_message_guild[message.guild.id] = discord.utils.utcnow().timestamp()
            
            # If server hopping mode is on, jump to this server
            if self.server_hopping_mode and self.active_guild != message.guild:
                self.active_guild = message.guild
                # Update active channel within this server
                if message.channel.type == discord.ChannelType.text:
                    self.active_channels[message.guild.id] = message.channel
                    self.response_channel[message.guild.id] = message.channel.id
                
                # Optional: Announce arrival (comment out if too spammy)
                # await message.channel.send("🌐 *I've traveled here to help!*")
            
            # Update active channel if wandering mode is on for this guild
            if self.wandering_mode.get(message.guild.id, False):
                if self.active_channels.get(message.guild.id) != message.channel:
                    self.active_channels[message.guild.id] = message.channel
                    self.response_channel[message.guild.id] = message.channel.id
        
        # Update last message channel
        if message.guild and message.channel.type == discord.ChannelType.text:
            self.last_message_channel[message.guild.id] = message.channel.id
        
        # Always set response channel to where the command came from
        if message.guild:
            self.response_channel[message.guild.id] = message.channel.id
        
        await self.process_commands(message)
    
    async def on_command(self, ctx: commands.Context):
        """Called when a command is successfully invoked"""
        if ctx.guild:
            self.response_channel[ctx.guild.id] = ctx.channel.id
            
            # Update active guild if command comes from different server
            if self.active_guild != ctx.guild:
                if self.server_hopping_mode:
                    self.active_guild = ctx.guild
            
            # Update active channel if wandering mode is on
            if self.wandering_mode.get(ctx.guild.id, False):
                if self.active_channels.get(ctx.guild.id) != ctx.channel:
                    self.active_channels[ctx.guild.id] = ctx.channel
    
    async def on_command_error(self, ctx, error):
        """Global error handling"""
        if isinstance(error, commands.CommandNotFound):
            return
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f"❌ You don't have permission to do that, {ctx.author.mention}")
            return
        
        if isinstance(error, commands.BotMissingPermissions):
            await ctx.send(f"❌ I don't have permission to do that")
            return
        
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ Command on cooldown. Try again in {error.retry_after:.2f}s")
            return
        
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: `{error.param.name}`\nUse `{Config.PREFIX}help {ctx.command.name}` for usage")
            return
        
        if isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Invalid argument: {error}\nUse `{Config.PREFIX}help {ctx.command.name}` for proper usage")
            return
        
        logger.error(f"Unhandled error in command {ctx.command}: {error}")
        await ctx.send(f"❌ An unexpected error occurred: {error}")
    
    async def close(self):
        """Clean shutdown procedure"""
        logger.info("Shutting down bot...")
        self.running = False
        await super().close()

def main():
    """Main entry point"""
    try:
        Config.validate()
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        print(f"\n❌ Config Error: {e}")
        print("Please check your config.py file and try again.")
        return
    
    bot = MyBot()
    
    try:
        bot.run(Config.TOKEN, log_handler=None)
    except discord.LoginFailure:
        print("\n❌ Invalid token! Please check your Discord bot token in config.py")
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n❌ Fatal error: {e}")
    finally:
        print("👋 Goodbye!")

if __name__ == "__main__":
    main()