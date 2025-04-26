from discord import app_commands, Embed, Interaction, Color, Message, Reaction, User
from discord.ext import tasks
from discord.ext.commands import Bot
from datetime import datetime, timedelta
from steam_web_api import Steam
from typing import Dict, Set, Any
import time

reminder_tasks: Dict[int, Dict[str, Any]] = {}

@app_commands.command(name="schedule_game", description="Запланировать игру на конкретное время и дату")
@app_commands.describe(
    max_players="Сколько игроков будет участвовать?",
    game_input_name="Название игры (на английском, будет поиск в Steam)",
    year="Год",
    month="Месяц (1-12)",
    day="День (1-31)",
    hour="Час (0-23)",
    minute="Минута (0-59)"
)
async def schedule_game(
    interaction: Interaction,
    max_players: int,
    game_input_name: str,
    year: int,
    month: int, 
    day: int,
    hour: int,
    minute: int
) -> None:
    # Validate time inputs
    try:
        # Create datetime object from input parameters
        scheduled_time = datetime(year, month, day, hour, minute)
        
        # Get current time and calculate one week from now
        current_time = datetime.now()
        one_week_later = current_time + timedelta(days=7)
        
        # Check if the scheduled time is within the valid range (between now and one week later)
        if scheduled_time < current_time:
            await interaction.response.send_message("Нельзя запланировать игру в прошлом.", ephemeral=True)
            return
        elif scheduled_time > one_week_later:
            await interaction.response.send_message("Планировать игру можно только на неделю вперёд.", ephemeral=True)
            return
            
        # Calculate minutes_delay for the original function
        time_difference = scheduled_time - current_time
        minutes_delay = int(time_difference.total_seconds() / 60)
        
    except ValueError:
        await interaction.response.send_message("Введена некорректная дата или время.", ephemeral=True)
        return
    
    search_results = steam.apps.search_games(game_input_name)
    if not search_results.get('apps'):
        await interaction.response.send_message(f"Не найдено результатов для '{game_input_name}'.", ephemeral=True)
        return

    game = search_results['apps'][0]
    game_id = game['id'][0]
    game_link = game['link']
    game_name = game['name']

    game_instance = steam.apps.get_app_details(game_id, country="RU", filters="basic,price_overview")
    if game_instance is None:
        await interaction.response.send_message(f"Не удалось получить данные об игре с ID '{game_id}'.", ephemeral=True)
        await interaction.original_response()
        return

    game_data = game_instance[str(game_id)]['data']
    image_link = game_data['header_image']
    price = 'Бесплатно' if game_data['is_free'] else game_data['price_overview']['final_formatted']
    description = game_data['short_description']

    future_time = datetime.now() + timedelta(minutes=minutes_delay)
    unix_timestamp = int(time.mktime(future_time.timetuple()))

    embed = generate_embed(
        interaction,
        max_players, 
        game_name, 
        game_link, 
        image_link, 
        price, 
        description, 
        unix_timestamp
    )

    await interaction.response.send_message(embed=embed)
    msg = await interaction.original_response()
    await msg.add_reaction("💝")

    reminder_tasks[msg.id] = {
        "users": set(),
        "time": future_time,
        "message": msg,
        "max_players": max_players,
        "game_name": game_name,
        "game_link": game_link,
        "channel_id": interaction.channel_id,
    }

    if not reminder_loop.is_running():
        reminder_loop.start()
    


@app_commands.command(name="game", description="Показать информацию об игре из Steam")
@app_commands.describe(
    max_players="Сколько игроков будет участвовать?",
    minutes_delay="Через сколько минут игра начнется?",
    game_input_name="Название игры (на английском, будет поиск в Steam)"
)
async def game_embed(
    interaction: Interaction,
    max_players: int,
    minutes_delay: int,
    game_input_name: str
) -> None:
    search_results = steam.apps.search_games(game_input_name)
    if not search_results.get('apps'):
        await interaction.response.send_message(f"Не найдено результатов для '{game_input_name}'.", ephemeral=True)
        return

    game = search_results['apps'][0]
    game_id = game['id'][0]
    game_link = game['link']
    game_name = game['name']

    game_instance = steam.apps.get_app_details(game_id, country="RU", filters="basic,price_overview")
    if game_instance is None:
        await interaction.response.send_message(f"Не удалось получить данные об игре с ID '{game_id}'.", ephemeral=True)
        await interaction.original_response()
        return

    game_data = game_instance[str(game_id)]['data']
    image_link = game_data['header_image']
    price = 'Бесплатно' if game_data['is_free'] else game_data['price_overview']['final_formatted']
    description = game_data['short_description']

    future_time = datetime.now() + timedelta(minutes=minutes_delay)
    unix_timestamp = int(time.mktime(future_time.timetuple()))

    embed = generate_embed(
        interaction,
        max_players, 
        game_name, 
        game_link, 
        image_link, 
        price, 
        description, 
        unix_timestamp
    )

    await interaction.response.send_message(embed=embed)
    msg = await interaction.original_response()
    await msg.add_reaction("💝")

    reminder_tasks[msg.id] = {
        "users": set(),
        "time": future_time,
        "message": msg,
        "max_players": max_players,
        "game_name": game_name,
        "game_link": game_link,
        "channel_id": interaction.channel_id,
    }

    if not reminder_loop.is_running():
        reminder_loop.start()

def generate_embed(interaction, max_players, game_name, game_link, image_link, price, description, unix_timestamp):
    embed = Embed(
        title=game_name,
        description=description,
        color=Color.blue(),
        url=game_link
    )
    embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url)
    embed.add_field(name="Сколько игроков?", value=max_players, inline=True)
    embed.add_field(name="Цена?", value=price, inline=True)
    embed.add_field(name="Когда?", value=f'<t:{unix_timestamp}:R>', inline=True)
    embed.add_field(name="Игроки", value="Пока никто не присоединился", inline=False)
    embed.set_image(url=image_link)
    embed.set_footer(text=f"Call by {interaction.user.name}", icon_url=interaction.user.avatar.url)
    embed.timestamp = datetime.now()
    return embed

async def setup(bot: Bot, _steam: Steam) -> None:
    global steam
    steam = _steam
    bot.tree.add_command(game_embed)
    bot.tree.add_command(schedule_game)

    @bot.event
    async def on_reaction_add(reaction: Reaction, user: User) -> None:
        if user.bot or str(reaction.emoji) != "💝":
            return

        message_id = reaction.message.id
        if message_id not in reminder_tasks:
            return

        task = reminder_tasks[message_id]
        task["users"].add(user)

        embed = reaction.message.embeds[0]
        player_count = len(task["users"])
        for i, field in enumerate(embed.fields):
            if field.name == "Игроки":
                player_list = "\n".join([f"{idx + 1}. {u.mention}" for idx, u in enumerate(task["users"])])
                embed.set_field_at(
                    i,
                    name="Игроки",
                    value=player_list if player_count else "Пока никто не присоединился",
                    inline=False
                )

        await reaction.message.edit(embed=embed)

    @bot.event
    async def on_reaction_remove(reaction: Reaction, user: User) -> None:
        if user.bot or str(reaction.emoji) != "💝":
            return

        message_id = reaction.message.id
        if message_id not in reminder_tasks:
            return

        task = reminder_tasks[message_id]
        task["users"].discard(user)

        embed = reaction.message.embeds[0]
        player_count = len(task["users"])
        for i, field in enumerate(embed.fields):
            if field.name == "Игроки":
                player_list = "\n".join([f"{idx + 1}. {u.mention}" for idx, u in enumerate(task["users"])])
                embed.set_field_at(
                    i,
                    name="Игроки",
                    value=player_list if player_count else "Пока никто не присоединился",
                    inline=False
                )

        await reaction.message.edit(embed=embed)

@tasks.loop(seconds=30)
async def reminder_loop() -> None:
    now = datetime.now()
    expired: list[int] = []

    for message_id, data in reminder_tasks.items():
        if now >= data["time"]:
            channel_mention = f"<#{data['channel_id']}>"
            for user in data["users"]:
                try:
                    if data.get('game_link'):
                        game_inline = f"[{data['game_name']}]({data['game_link']})"
                    else:
                        game_inline = f"{data['game_name']}"

                    await user.send(f"🔔 Планируем играть в {game_inline}, заходи в {channel_mention}")
                except Exception as e:
                    print(f"Не удалось отправить сообщение {user}: {e}")
            expired.append(message_id)

    for message_id in expired:
        reminder_tasks.pop(message_id, None)
