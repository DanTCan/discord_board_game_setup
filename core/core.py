import discord
import asyncio
from discord.ext import commands
import data.io as data

intents = discord.Intents.default()
intents.members = True
intents.presences = True
bot = commands.Bot(command_prefix='!', intents=intents)
TIMEOUT = '**Timed Out**'

# global_ctx = commands.Context
