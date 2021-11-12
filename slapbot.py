import random
import string
import time
import os

import discord
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('SLAP_DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord')
    for guild in bot.guilds:
        print(f'registered on {guild.name}')


class Slapper(commands.Converter):
    async def convert(self, ctx, argument):
        to_slap = random.choice(ctx.guild.members)
        # mentioned_in_reason = None
        # if '@' in argument:
        #     argument = argument.split(' ')
        #     for word in argument:
        #         if word[0] == '@':
        #             pass
        if ctx.author.nick:
            slapper = ctx.author.nick
        else:
            slapper = ctx.author.name
        # if to_slap.nick:
        #     to_slap = to_slap.nick
        # else:
        #     to_slap
        return '{0} slapped {1.mention} because *{2}*'.format(slapper, to_slap, argument)


@bot.command(rest_is_raw=False)
async def slap(ctx: commands.Context, *, reason: Slapper):
    # if ctx.channel.name != 'slap-chat':
    #     return
    await ctx.send(reason)

bot.run(TOKEN)
