import discord
from discord.ext import commands
try:
    from PIL import Image
except ImportError:
    import Image
import pytesseract

intents = discord.Intents.default()
intents.members = True
intents.presences = True
bot = commands.Bot(command_prefix='!', intents=intents)
TIMEOUT = '**Timed Out**'


class Console:
    def __init__(self, console_bot: commands.Bot, ctx: commands.Context):
        self.ctx = ctx
        self.bot = console_bot
        self.outgoing_buffer = list()

    async def read(self, check=None, timeout=None):
        rtn = await self.bot.wait_for('message', check=check, timeout=timeout)
        return rtn.content

    def add(self, var: str, bold=True, newline=True, italic=False, bullet=False, numeric=None):
        rtn = f'**{var}**\n'
        if italic:
            rtn.replace('**', '***')
        if not bold:
            rtn.replace('**', '')
        if not newline:
            rtn.replace('\n', '')
        if bullet:
            rtn = '**•** ' + rtn
        if numeric:
            rtn = f'**{numeric})** ' + rtn
        self.outgoing_buffer.append(rtn)

    async def send(self):
        await self.ctx.send(''.join(self.outgoing_buffer))
        self.outgoing_buffer.clear()
