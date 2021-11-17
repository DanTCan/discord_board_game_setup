import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True
intents.presences = True
bot = commands.Bot(command_prefix='!', intents=intents)
TIMEOUT = '**Timed Out**'

global_ctx = commands.Context
print('TEST1', global_ctx, type(global_ctx))


def context_decorator(function):
    def wrapper(context):
        global global_ctx
        global_ctx = context
        function(context)
    return wrapper
