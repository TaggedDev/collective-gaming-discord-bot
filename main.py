import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from steam_web_api import Steam
import commands as bot_commands  # Import the commands module

# Load environment variables from .env file
load_dotenv()

# Get the Discord token from environment variables
TOKEN = os.getenv('TOKEN')
STEAM = os.getenv('STEAM')

# Set up intents
intents = discord.Intents.default()
intents.message_content = True

# Create a bot instance with a command prefix and intents
bot = commands.Bot(command_prefix='!', intents=intents)
steam = Steam(STEAM)

@bot.event
async def on_ready():
    """Event triggered when the bot is ready and connected to Discord."""
    print(f'{bot.user.name} has connected to Discord!')
    print(f'Bot ID: {bot.user.id}')
    
    # Load commands from the commands.py file
    await bot_commands.setup(bot, steam)
    print('Commands loaded')
    print('------')

@bot.event
async def on_message(message):
    """Event triggered when a message is sent in a channel the bot can see."""
    # Don't respond to our own messages
    if message.author == bot.user:
        return
    
    # Process commands
    await bot.process_commands(message)

# Error handling
@bot.event
async def on_command_error(ctx, error):
    """Global error handler for command errors."""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found. Use !help to see available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument: {error.param.name}")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"Bad argument: {error}")
    else:
        await ctx.send(f"An error occurred: {error}")
        print(f"Unhandled error: {error}")

# Run the bot
def main():
    if not TOKEN:
        print("Error: No TOKEN found in .env file")
        return
        
    try:
        bot.run(TOKEN)
    except discord.errors.LoginFailure:
        print("Error: Invalid Discord TOKEN")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()