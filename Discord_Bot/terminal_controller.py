# terminal_controller.py
import asyncio
import discord
from discord.ext import commands
import os
import sys
from dotenv import load_dotenv

# Load token from .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

if not TOKEN:
    print("❌ No token found! Make sure .env file has DISCORD_TOKEN=your_token")
    sys.exit(1)

class TerminalBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        self.target_channel = None
        self.running = True
    
    async def setup_hook(self):
        print("✅ Terminal controller connected to Discord")
    
    async def on_ready(self):
        print(f"\n{'='*60}")
        print(f"✅ LOGGED IN AS: {self.user}")
        print(f"📡 IN SERVERS: {len(self.guilds)}")
        
        # Find a channel to use
        for guild in self.guilds:
            for channel in guild.text_channels:
                permissions = channel.permissions_for(guild.me)
                if permissions.send_messages:
                    self.target_channel = channel
                    print(f"📢 WILL SEND TO: #{channel.name} in {guild.name}")
                    break
            if self.target_channel:
                break
        
        if not self.target_channel:
            print("❌ No accessible channels found!")
            await self.close()
            return
        
        print('='*60)
        print("🎮 TERMINAL CONTROL ACTIVE")
        print('='*60)
        print("Type a message and press ENTER to send to Discord")
        print("Type '!command' to run a bot command (e.g., !ping)")
        print("Type 'exit' to quit")
        print('='*60 + '\n')
        
        # Send startup message
        await self.target_channel.send("🟢 Terminal controller is now online!")
        
        # Start terminal input loop
        await self.terminal_input_loop()
    
    async def terminal_input_loop(self):
        """Read from terminal and send to Discord"""
        while self.running:
            try:
                # This runs in the async thread but input() blocks
                # So we run it in a thread pool
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: input("> ")
                )
                
                if user_input.lower() == 'exit':
                    await self.target_channel.send("🔴 Terminal controller shutting down...")
                    self.running = False
                    await self.close()
                    break
                
                elif user_input.startswith('!'):
                    # It's a command - execute it
                    await self.execute_command(user_input)
                
                elif user_input.strip():
                    # Regular message - send to Discord
                    await self.target_channel.send(f"**[Terminal]**: {user_input}")
                    print(f"📤 Sent: {user_input}")
                    
            except EOFError:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    async def execute_command(self, command_text):
        """Execute a Discord command"""
        print(f"⚡ Executing command: {command_text}")
        
        # Find a channel to send the command from
        channel = self.target_channel
        if not channel:
            print("❌ No channel to execute command in")
            return
        
        # Create a fake message to process the command
        class FakeMessage:
            def __init__(self, content, author, channel):
                self.content = content
                self.author = author
                self.channel = channel
                self.guild = channel.guild
        
        fake_message = FakeMessage(command_text, self.user, channel)
        
        # Process the command
        await self.process_commands(fake_message)
    
    async def on_message(self, message):
        """Process commands"""
        if message.author.id == self.user.id:
            return
        await self.process_commands(message)
    
    async def on_command_error(self, ctx, error):
        """Handle command errors"""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f"❌ Command not found: {ctx.message.content}")
        else:
            await ctx.send(f"❌ Error: {error}")
            print(f"❌ Command error: {error}")

async def main():
    bot = TerminalBot()
    try:
        await bot.start(TOKEN)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
    finally:
        await bot.close()

if __name__ == "__main__":
    print("🎮 TERMINAL DISCORD CONTROLLER")
    print("Starting up...")
    asyncio.run(main())