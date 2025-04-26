import os
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv
from steam_web_api import Steam
import commands as bot_commands 
from aiohttp_socks import ProxyConnector 


# Load environment variables from .env file
load_dotenv()

# Get the Discord token from environment variables
TOKEN = os.getenv('TOKEN')
STEAM = os.getenv('STEAM')
PROXY_URL = os.getenv('PROXY_URL')

# Set up intents
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True


async def start_bot():
    if not TOKEN:
        print("Error: No TOKEN found in .env file")
        return
    
    steam = Steam(STEAM)
    
    # Create proxy connector
    connector = ProxyConnector.from_url(PROXY_URL)
    
    # Create the bot with the proper proxy setup
    bot = commands.Bot(command_prefix='!', intents=intents, session=connector)
    
    # Replace the bot's HTTP client with one that uses our proxy
    bot.http.session = aiohttp.ClientSession(connector=connector)

    @bot.event
    async def on_ready():
        print(f'{bot.user.name} has connected to Discord!')
        print(f'Bot ID: {bot.user.id}')
        await bot_commands.setup(bot, steam)
        await bot.tree.sync()
        print('Commands loaded')
        print('------')

    @bot.event
    async def on_message(message):
        if message.author == bot.user:
            return
        await bot.process_commands(message)

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Command not found. Use !help to see available commands.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param.name}")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"Bad argument: {error}")
        else:
            await ctx.send(f"An error occurred: {error}")
            print(f"Unhandled error: {error}")

    try:
        await bot.start(TOKEN)
    finally:
        await bot.http.session.close()


def main():
    import asyncio
    try:
        asyncio.run(start_bot())
    except discord.errors.LoginFailure:
        print("Error: Invalid Discord TOKEN")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()