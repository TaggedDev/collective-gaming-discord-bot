import asyncio
from datetime import datetime, timedelta
import discord
from discord.ext import commands
from steam_web_api import Steam
import time

steam = None

async def setup(bot, steam_client: Steam):
    """Function to add all commands to the bot"""
    global steam
    steam = steam_client
    bot.add_command(ping)
    bot.add_command(hello)
    bot.add_command(countdown)
    bot.add_command(game_embed)


@commands.command(name='game')
async def game_embed(ctx, max_players: int, minutes_delay: int=0, *game_name):
    if not game_name:
        await ctx.send(f"Specify game name")
        return

    game_name = ' '.join(game_name)
    search_results = steam.apps.search_games(game_name)
    if (not search_results.get('apps', '')) and (len(search_results['apps']) == 0):
        await ctx.send(f"No results found for '{game_name}'.")
        return
    
    search_results = search_results['apps']
    game = search_results[0]
    game_id = game['id'][0]
    game_link = game['link']
    

    game_instance = steam.apps.get_app_details(game_id, country="RU", filters="basic,price_overview")
    if game_instance is None:
        await ctx.send(f"No results found for game with id '{game_id}'.")
        return
    
    
    game_instance = game_instance[str(game_id)]['data']
    image_link = game_instance['header_image']
    price = 'Бесплатно' if game_instance['is_free'] else game_instance['price_overview']['final_formatted']
    description = game_instance['short_description']

    future_time = datetime.now() + timedelta(minutes=minutes_delay)
    unix_timestamp = int(time.mktime(future_time.timetuple()))

    embed = discord.Embed(
        title=game_name,
        description=description,
        color=discord.Color.blue(),
        url=game_link
    )
    
    # Add author information
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
    
    # Add inline fields for max players and online play status
    embed.add_field(name="Сколько игроков?", value=max_players, inline=True)
    embed.add_field(name="Цена?", value=price, inline=True)
    embed.add_field(name="Когда?", value=f'<t:{unix_timestamp}:R>', inline=True)
    
    # Add game image
    embed.set_image(url=image_link)
    
    # Add footer with timestamp
    embed.set_footer(text=f"Call by {ctx.author.name}", icon_url=ctx.author.avatar.url)
    embed.timestamp = datetime.now()
    
    # Send the embed
    await ctx.send(embed=embed)

@commands.command(name='ping')
async def ping(ctx):
    """Responds with the bot's latency."""
    latency = round(ctx.bot.latency * 1000)
    await ctx.send(f'Pong! Latency: {latency}ms')

@commands.command(name='hello')
async def hello(ctx):
    """Greets the user who called the command."""
    await ctx.send(f'Hello, {ctx.author.mention}!')

@commands.command(name='countdown')
async def countdown(ctx, seconds: int = 5):
    """Starts a countdown from the specified number of seconds."""
    if seconds > 60:
        await ctx.send("Please use a value of 60 seconds or less.")
        return
        
    message = await ctx.send(f"Countdown: {seconds}")
    
    while seconds > 0:
        seconds -= 1
        await asyncio.sleep(1)
        await message.edit(content=f"Countdown: {seconds}")
    
    await message.edit(content="Countdown complete!")