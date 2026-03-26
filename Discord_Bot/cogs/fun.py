# cogs/fun.py
import discord
from discord.ext import commands
import random
import asyncio

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.eight_ball_responses = [
            "It is certain.", "It is decidedly so.", "Without a doubt.",
            "Yes - definitely.", "You may rely on it.", "As I see it, yes.",
            "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.",
            "Reply hazy, try again.", "Ask again later.", "Better not tell you now.",
            "Cannot predict now.", "Concentrate and ask again.",
            "Don't count on it.", "My reply is no.", "My sources say no.",
            "Outlook not so good.", "Very doubtful."
        ]
    
    @commands.command(name='8ball', aliases=['eightball', 'ask'])
    async def eight_ball(self, ctx, *, question):
        """Ask the magic 8-ball a question"""
        response = random.choice(self.eight_ball_responses)
        
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            color=discord.Color.purple()
        )
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=f"**{response}**", inline=False)
        embed.set_footer(text=f"Asked by {ctx.author.display_name}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='roll', aliases=['dice'])
    async def roll(self, ctx, dice: str = "1d6"):
        """Roll dice in NdN format (e.g., 2d20)"""
        try:
            rolls, limit = map(int, dice.lower().split('d'))
        except:
            await ctx.send("❌ Format has to be in NdN (e.g., 2d20)")
            return
        
        if rolls > 100:
            await ctx.send("❌ You can't roll more than 100 dice at once!")
            return
        
        if limit > 1000:
            await ctx.send("❌ Dice can't have more than 1000 sides!")
            return
        
        results = [random.randint(1, limit) for _ in range(rolls)]
        total = sum(results)
        
        embed = discord.Embed(
            title="🎲 Dice Roll",
            description=f"Rolling {rolls}d{limit}",
            color=discord.Color.green()
        )
        embed.add_field(name="Results", value=f"`{results}`", inline=False)
        embed.add_field(name="Total", value=f"**{total}**", inline=False)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='coinflip', aliases=['flip', 'coin'])
    async def coinflip(self, ctx):
        """Flip a coin"""
        result = random.choice(['Heads', 'Tails'])
        
        embed = discord.Embed(
            title="🪙 Coin Flip",
            description=f"The coin landed on: **{result}**",
            color=discord.Color.gold() if result == 'Heads' else discord.Color.light_gray()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='rps')
    async def rps(self, ctx, choice: str = None):
        """Play Rock Paper Scissors with the bot"""
        choices = ['rock', 'paper', 'scissors']
        
        if not choice or choice.lower() not in choices:
            await ctx.send("❌ Please choose: `rock`, `paper`, or `scissors`")
            return
        
        bot_choice = random.choice(choices)
        user_choice = choice.lower()
        
        # Determine winner
        if user_choice == bot_choice:
            result = "It's a tie! 🤝"
            color = discord.Color.blue()
        elif (user_choice == 'rock' and bot_choice == 'scissors') or \
             (user_choice == 'paper' and bot_choice == 'rock') or \
             (user_choice == 'scissors' and bot_choice == 'paper'):
            result = f"You win! 🎉"
            color = discord.Color.green()
        else:
            result = f"I win! 🤖"
            color = discord.Color.red()
        
        embed = discord.Embed(
            title="📄 Rock Paper Scissors ✂️",
            description=result,
            color=color
        )
        embed.add_field(name="Your choice", value=user_choice.capitalize(), inline=True)
        embed.add_field(name="My choice", value=bot_choice.capitalize(), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Fun(bot))