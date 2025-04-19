from discord import app_commands, Embed, Interaction, Color
from discord.ext import tasks
from datetime import datetime, timedelta
from discord.ext.commands import Bot
from steam_web_api import Steam
import time

reminder_tasks = {}

@app_commands.command(name="game", description="Показать информацию об игре из Steam")
@app_commands.describe(
    max_players="Сколько игроков будет участвовать?",
    minutes_delay="Через сколько минут игра начнется?",
    game_name="Название игры (на английском, будет поиск в Steam)"
)
async def game_embed(interaction: Interaction, max_players: int, minutes_delay: int, game_name: str):
    search_results = steam.apps.search_games(game_name)
    if not search_results.get('apps') or len(search_results['apps']) == 0:
        await interaction.response.send_message(f"Не найдено результатов для '{game_name}'.", ephemeral=True)
        return

    game = search_results['apps'][0]
    game_id = game['id'][0]
    game_link = game['link']

    game_instance = steam.apps.get_app_details(game_id, country="RU", filters="basic,price_overview")
    if game_instance is None:
        await interaction.response.send_message(f"Не удалось получить данные об игре с ID '{game_id}'.", ephemeral=True)
        return

    game_data = game_instance[str(game_id)]['data']
    image_link = game_data['header_image']
    price = 'Бесплатно' if game_data['is_free'] else game_data['price_overview']['final_formatted']
    description = game_data['short_description']

    future_time = datetime.now() + timedelta(minutes=minutes_delay)
    unix_timestamp = int(time.mktime(future_time.timetuple()))

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
    embed.set_image(url=image_link)
    embed.set_footer(text=f"Call by {interaction.user.name}", icon_url=interaction.user.avatar.url)
    embed.timestamp = datetime.now()

    await interaction.response.send_message(embed=embed)
    msg = await interaction.original_response()
    await msg.add_reaction("💝")  # добавляем реакцию

    reminder_tasks[msg.id] = {
        "users": set(),  # сюда будем добавлять пользователей
        "time": future_time
    }

    if not reminder_loop.is_running():
        reminder_loop.start()

# Функция setup, как и раньше, просто добавляет команду
async def setup(bot: Bot, _steam: Steam):
    global steam
    steam = _steam
    bot.tree.add_command(game_embed)

    @bot.event
    async def on_reaction_add(reaction, user):
        """Обработка нажатий на реакцию."""
        if user.bot:
            return
        if reaction.message.id in reminder_tasks:
            reminder_tasks[reaction.message.id]["users"].add(user)

    @bot.event
    async def on_reaction_remove(reaction, user):
        """Если пользователь убрал реакцию — удалим из списка."""
        if user.bot:
            return
        if reaction.message.id in reminder_tasks:
            reminder_tasks[reaction.message.id]["users"].discard(user)

@tasks.loop(seconds=30)
async def reminder_loop():
    now = datetime.now()
    expired = []
    for message_id, data in reminder_tasks.items():
        if now >= data["time"]:
            for user in data["users"]:
                try:
                    await user.send("🔔 Время играть! Ждём тебя 😉")
                except Exception as e:
                    print(f"Не удалось отправить сообщение {user}: {e}")
            expired.append(message_id)

    # Удалим выполненные задачи
    for message_id in expired:
        reminder_tasks.pop(message_id, None)