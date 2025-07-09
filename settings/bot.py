import discord
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
INTENTS = discord.Intents.all()
PREFIX = 'qq!'