from discord.ext import commands
from settings import bot as settings
from settings import utils
import discord
import os
import asyncio

bot: commands.Bot = commands.Bot(command_prefix=settings.PREFIX, intents=settings.INTENTS)

@bot.event
async def on_ready():
    for guild in bot.guilds:
        with open(f'queues/queue_{guild.id}.json', 'a+', encoding='utf-8') as f:
            f.seek(0)
            if not f.read().strip():
                f.write('{}')
    await utils.init_db()
    print('---')
    cogs = []
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            name = f'{filename[:-3]}'
            await bot.load_extension(f'cogs.{name}')
            cogs.append(name)
    print(f'Loaded cogs: {", ".join(cogs)}')
    print('---')
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')

bot.run(settings.TOKEN)
