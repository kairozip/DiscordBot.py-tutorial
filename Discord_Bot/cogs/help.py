"""
help.py — The Neural Center of Your Bot's Command Interface

This cog provides a custom help system with a beautiful hardcoded embed
for the main !help command, plus detailed command and cog help.
"""

import discord
from discord.ext import commands
from typing import Optional

class HelpCog(commands.Cog):
    """
    📚 The Command Compendium
    
    This cog houses your bot's central help system with a custom
    hardcoded help embed for the main help command.
    """
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("🔧 HelpCog initialized — Custom help system active")
    
    @commands.command(name="help", aliases=["h", "commands", "cmds", "?"])
    async def help_command(self, ctx: commands.Context, *, target: Optional[str] = None):
        """
        Display help information for commands and cogs.
        
        **Usage:**
        `!help` - Shows all available commands grouped by category
        `!help [cog_name]` - Shows all commands in a specific cog
        `!help [command_name]` - Shows detailed help for a specific command
        
        **Examples:**
        `!help moderation` - View all moderation commands
        `!help kick` - Get detailed information about the kick command
        """
        
        # Case 1: No arguments — show the beautiful hardcoded help embed
        if target is None:
            await self._send_main_help_embed(ctx)
            return
        
        # Case 2: Try to find a cog first (case-insensitive)
        target_lower = target.lower()
        cog = None
        for cog_name, cog_instance in self.bot.cogs.items():
            if cog_name.lower() == target_lower:
                cog = cog_instance
                break
        
        if cog:
            await self._send_cog_help(ctx, cog)
            return
        
        # Case 3: Try to find a command
        command = self.bot.get_command(target_lower)
        if command:
            await self._send_command_help(ctx, command)
            return
        
        # Case 4: Nothing found
        embed = discord.Embed(
            title="❌ Command Not Found",
            description=f"No cog or command named `{target}` was found.\nUse `!help` to see all available commands.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    
    async def _send_main_help_embed(self, ctx: commands.Context):
        """Send the beautiful hardcoded help embed with all commands organized by category."""
        
        # Create the main embed with a sleek design
        embed = discord.Embed(
            title="🤖 BOT COMMANDS",
            description=f"**Command Prefix:** `{ctx.prefix}`\nUse `{ctx.prefix}help <command>` for detailed info on any command.",
            color=discord.Color.from_rgb(114, 137, 218)  # Discord Blurple
        )
        
        # Set the bot's avatar as thumbnail if available
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        
        # BASIC Commands Section
        embed.add_field(
            name="🔹 BASIC",
            value="```\n"
                  "!ping      - Check if bot is alive\n"
                  "!hello     - Get greeted\n"
                  "!info      - Bot stats\n"
                  "```",
            inline=False
        )
        
        # MODERATION Commands Section
        embed.add_field(
            name="🔹 MODERATION",
            value="```\n"
                  "!kick @user    - Kick member\n"
                  "!ban @user     - Ban member\n"
                  "!clear 10      - Delete messages\n"
                  "!mute @user 5  - Mute for 5 min\n"
                  "```",
            inline=False
        )
        
        # FUN Commands Section
        embed.add_field(
            name="🔹 FUN",
            value="```\n"
                  "!8ball question   - Magic 8-ball\n"
                  "!roll 2d20        - Roll dice\n"
                  "!coinflip         - Flip coin\n"
                  "!rps rock         - Rock Paper Scissors\n"
                  "```",
            inline=False
        )
        
        # UTILITY Commands Section
        embed.add_field(
            name="🔹 UTILITY",
            value="```\n"
                  "!userinfo @user   - User details\n"
                  "!serverinfo       - Server stats\n"
                  "!avatar @user     - Get avatar\n"
                  "```",
            inline=False
        )
        
        # Add a footer with additional info
        embed.set_footer(
            text=f"Total Commands: 12 | Requested by {ctx.author.name}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None
        )
        
        await ctx.send(embed=embed)
    
    async def _send_cog_help(self, ctx: commands.Context, cog: commands.Cog):
        """Send detailed help for a specific cog/module."""
        
        cog_name = cog.__class__.__name__
        
        # Get all visible commands in this cog
        commands_list = [cmd for cmd in cog.get_commands() 
                        if not cmd.hidden and cmd.name not in ["help", "h", "commands"]]
        commands_list.sort(key=lambda cmd: cmd.name)
        
        # Create the embed
        embed = discord.Embed(
            title=f"📂 Module: {cog_name}",
            description=cog.__doc__ or "No module description available.",
            color=discord.Color.blue()
        )
        
        # Add each command as a field
        for cmd in commands_list:
            # Build command signature
            signature = f"{ctx.prefix}{cmd.name} {cmd.signature}" if cmd.signature else f"{ctx.prefix}{cmd.name}"
            
            # Get command description
            description = cmd.short_doc or "No description"
            
            # Add aliases if they exist
            aliases_text = ""
            if cmd.aliases:
                aliases_text = f"\n*Aliases: {', '.join(f'`{alias}`' for alias in cmd.aliases)}*"
            
            embed.add_field(
                name=f"⚡ {cmd.name}",
                value=f"`{signature}`\n{description}{aliases_text}",
                inline=False
            )
        
        if not commands_list:
            embed.add_field(
                name="ℹ️ No Commands",
                value="This module contains no visible commands.",
                inline=False
            )
        
        embed.set_footer(text=f"Use {ctx.prefix}help <command> for even more details")
        
        await ctx.send(embed=embed)
    
    async def _send_command_help(self, ctx: commands.Context, command: commands.Command):
        """Send ultra-detailed help for a specific command."""
        
        # Create the embed
        embed = discord.Embed(
            title=f"⚙️ Command: {command.name}",
            color=discord.Color.green()
        )
        
        # Full description (help text)
        help_text = command.help or "No detailed help available for this command."
        embed.description = help_text
        
        # Usage section
        if command.usage:
            usage = f"{ctx.prefix}{command.name} {command.usage}"
        elif command.signature:
            usage = f"{ctx.prefix}{command.name} {command.signature}"
        else:
            usage = f"{ctx.prefix}{command.name}"
        
        embed.add_field(
            name="📝 Usage",
            value=f"`{usage}`",
            inline=False
        )
        
        # Aliases section
        if command.aliases:
            embed.add_field(
                name="🔄 Aliases",
                value=", ".join(f"`{alias}`" for alias in command.aliases),
                inline=False
            )
        
        # Cooldown section
        if command._buckets and command._buckets._cooldown:
            cd = command._buckets._cooldown
            embed.add_field(
                name="⏱️ Cooldown",
                value=f"{cd.rate} use(s) every {cd.per} seconds",
                inline=False
            )
        
        # Permissions section
        if command.checks:
            # Extract permission requirements if they exist
            permissions = []
            for check in command.checks:
                check_str = str(check)
                if "has_permissions" in check_str:
                    import re
                    perms = re.findall(r"(\w+)=True", check_str)
                    permissions.extend(perms)
            
            if permissions:
                embed.add_field(
                    name="🔒 Required Permissions",
                    value=", ".join(f"`{perm}`" for perm in permissions),
                    inline=False
                )
        
        # Cog attribution
        if command.cog:
            embed.set_footer(text=f"📁 Part of: {command.cog.__class__.__name__}")
        else:
            embed.set_footer(text="📁 Uncategorized command")
        
        await ctx.send(embed=embed)


# The mandatory setup function that Discord.py looks for when loading cogs
async def setup(bot: commands.Bot):
    """This function is called when the cog is loaded."""
    await bot.add_cog(HelpCog(bot))
    print("✅ HelpCog successfully loaded — Custom help embed active!")