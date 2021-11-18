import os
import random
import string
from core.core import bot, TIMEOUT, commands, discord
from core.validators import ContentValidator
import asyncio
import data.io as data

from models.game import Game, UNUSED
from models.player import Player

DEMO = Game('DEMO', data.games_cache)
data.games_cache.remove(DEMO)


@bot.event  # @client.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord')
    for guild in bot.guilds:
        print(f'registered on {guild.name}')


@bot.command(brief='Set up a board game to be played with your friends.',
             help='Each game setup organized through this bot can be saved for reuse.\nGame profile parameters:\n-' +
                  "\n-".join(filter(lambda a: not a.startswith("__"), dir(DEMO)))
             )
async def setup(ctx: commands.Context):
    outgoing = list()

    async def read(validator=None, timeout=None):
        rtn = await bot.wait_for('message', check=validator, timeout=timeout)
        return rtn.content

    async def add(var: str, bold=True, newline=True, italic=False, bullet=False, numeric=None):
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
        outgoing.append(rtn)

    async def send():
        await ctx.send(''.join(outgoing))
        outgoing.clear()

    """THIS IS THE 'MAIN LOOP' - triggered by typing !setup in Discord.
    Making sure messages are in appropriate channel, ignoring bot"""
    check = ContentValidator(ctx)
    if ctx.author == bot.user:
        return
    if ctx.guild.name == 'Cool Shanta Water' and ctx.channel.name != 'boardgames':
        await ctx.send('To avoid server clutter, we should probably do this in the appropriate channel...')
        return

    outgoing.append('Let\'s set up a game!')
    if len(data.games_cache) > 0:
        outgoing.append('Type *lib* to see the library of existing game profiles.')
    outgoing.append('Type *new* to create a new game profile.')
    await send()

    this_game = None
    try:
        new_or_lib = await bot.wait_for('message', check=check.new_or_show_lib, timeout=15)
        new_or_lib = new_or_lib.content.strip().lower()
        if new_or_lib == 'lib':
            game_list = ''
            for g in data.games_cache:
                game_list += f'\n**{g.game_id})** *{g.title}* -- supports {g.min_players}-{g.max_players} players'
            game_list += '\n\n**Enter Game ID (#) to load corresponding profile...**'
            await ctx.send(game_list)
            try:
                selected_id = await bot.wait_for('message', check=check.game_selection, timeout=15)
                selected_id = int(selected_id.content)
                this_game = [gm for gm in data.games_cache if gm.game_id == selected_id][0]
                await ctx.send(f'**Loaded profile for *{this_game.title}*.**')
            except asyncio.TimeoutError:
                await ctx.send(TIMEOUT)
                return
        elif new_or_lib == 'new':
            await ctx.send('**Woohoo! A new game!  What is its title?**')
            title_input = await bot.wait_for('message')
            this_game = Game(title_input.content, data.games_cache)

            await ctx.send(f'**Minimum player count for *{this_game.title}*?**')
            min_count = await bot.wait_for('message', check=check.reasonable_int)
            this_game.min_players = int(min_count.content)

            await ctx.send(f'**Maximum player count for *{this_game.title}*?**')
            max_count = await bot.wait_for('message', check=check.reasonable_int)
            this_game.max_players = int(max_count.content)

            await ctx.send(f'**Okay, we will configure more setup parameters for *{this_game.title}* '
                           f'as we go along.**\n\n')
    except asyncio.TimeoutError:
        await ctx.send(TIMEOUT)
        return

    members_list_prompt = f'**I have detected the following members of *{ctx.guild.name}*:**'
    member_dict = {}
    i = 1
    for m in ctx.guild.members:  # list all members in server and prompt user to select some as Players
        if m == bot.user:
            continue
        member_dict[i] = m
        members_list_prompt += f'\n**{i})** *{m.name}*'
        i += 1
    members_list_prompt += f'\n\n**Please enter the player numbers you want to include for this game separated by ' \
                           f'commas.\nIf you need to add a player not in *{ctx.guild.name}*, we\'ll do that next.**'
    await ctx.send(members_list_prompt)

    def check_player_ids(msg: discord.Message):
        submission = msg.content.replace(' ', '').split(',')
        bad_value = False
        for v in submission:
            try:
                if int(v) not in member_dict.keys():
                    bad_value = True
            except TypeError or ValueError:
                bad_value = True
        return msg.author == ctx.author and msg.channel == ctx.channel and not bad_value

    try:
        player_select_input = await bot.wait_for('message', check=check_player_ids, timeout=30)
        players = []
        selected_confirmation = '**Selected Players:**\n'
        for x in player_select_input.content.replace(' ', '').split(','):
            p = Player(member_dict[int(x)])
            players.append(p)  # creating instances of class Player for each selected member
            selected_confirmation += f'*{p.name}*\n'
    except asyncio.TimeoutError:
        await ctx.send(TIMEOUT)
        return
    await ctx.send(selected_confirmation)
    if not len(players) >= this_game.max_players:
        await ctx.send(f'\n\n**Would you like to add any other players?**  *y/n*')
        try:
            add_players_yn = await bot.wait_for('message', check=check.yn, timeout=15)
            if add_players_yn.content.lower() == 'y':
                await ctx.send('\n**How many more players would you like to add?**')
                extra_player_count = await bot.wait_for('message', check=check.reasonable_int)
                extra_player_count = int(extra_player_count.content)
                added_players_confirmation = ''
                for c in range(extra_player_count):
                    await ctx.send(f'**Enter name for extra player {c + 1}**')
                    new_name = await bot.wait_for('message')
                    p = Player(new_name.content)
                    players.append(p)
                for p in players:
                    added_players_confirmation += f'\n*{p.name}*'
                await ctx.send('**Updated Player List:**' + added_players_confirmation)
        except asyncio.TimeoutError:
            await ctx.send(TIMEOUT)
            return

    players_dict = {}
    for i in range(1, len(players)+1):
        players_dict[i] = players.pop()

    while len(list(players_dict.values())) > this_game.max_players:
        axed = False
        while not axed:
            await ctx.send('**Too many players.  Axe someone!** *input player number*\n')
            chopping_block = ''
            for p in players_dict.keys():
                chopping_block += f'**{p})** *{players_dict[p].name}*\n'
            await ctx.send(chopping_block)
            axed = await bot.wait_for('message', check=check.reasonable_int)
            axed = int(axed.content)
            try:
                players_dict.pop(axed)
                axed = True
            except KeyError:
                await ctx.send('\n**Invalid choice!**')

    player_list = '**Final Player List:**\n'
    for p in players_dict.values():
        player_list += f'*{p.name}*\n'
    await ctx.send(player_list)

    if this_game.game_roles is None:
        await ctx.send('**Do you want to setup roles?** *y/n*')
        try:
            yn_roles = await bot.wait_for('message', check=check.yn, timeout=15)
            if yn_roles.content.lower() == 'y':
                roles_list_confirmation = ''
                roles_dict = {}
                await ctx.send('**How many roles?**')
                number_roles = await bot.wait_for('message', check=check.reasonable_int)
                for n in range(1, int(number_roles.content) + 1):
                    await ctx.send(f'**Name for Role {n}?**')
                    role_name = await bot.wait_for('message')
                    roles_dict[n] = role_name.content
                    roles_list_confirmation += f'\n**{n})** *{roles_dict[n]}*'
                roles = list(roles_dict.values())
                this_game.game_roles = roles
                await ctx.send('\n\n**Ok I have these roles:**' + roles_list_confirmation +
                               '\n\n**Would you like to manually assign roles?** *y,n* \n'
                               '**If no, will be done randomly.**')
                yn_role_assign = await bot.wait_for('message', check=check.yn)
                role_assignment_confirmation = ''
                if yn_role_assign.content.lower() == 'y':
                    await ctx.send('**Okay. Referencing the above list, '
                                   'enter the role number you wish to assign to each player...\n**')
                    for p in players:
                        await ctx.send(f'**Role number for** *{p.name}*?')
                        choice = await bot.wait_for('message')
                        p.game_role = roles_dict[int(choice.content)]
                        role_assignment_confirmation += f'\n**{p.name}:** *{p.game_role}*'
                else:
                    random.shuffle(players)
                    random.shuffle(roles)
                    for p in players:
                        p.game_role = roles.pop()
                        role_assignment_confirmation += f'\n**{p.name}:** *{p.game_role}*'
                await ctx.send('**Okay here is the breakdown:**\n' + role_assignment_confirmation)
            else:
                this_game.game_roles = UNUSED
                await ctx.send(f'**Okay profile for *{this_game.title}* does not include any roles.**')
        except asyncio.TimeoutError:
            await ctx.send(TIMEOUT)

    if this_game.teams is None:
        await ctx.send('**Is this a team game? *0* for \"No\", or Enter the *#* of Teams.**')
        try:
            number_of_teams = await bot.wait_for('message', check=check.reasonable_int, timeout=15)
            number_of_teams = int(number_of_teams.content)
            if number_of_teams > 0:
                await ctx.send(f'**Ok. I have {number_of_teams} teams.  Do we want to evenly distribute players across '
                               f'teams**? *y/n*')
                yn = await bot.wait_for('message', check=check.yn)
                if yn.content.lower() == 'y':
                    teams = {}
                    team_player_count = len(players) // number_of_teams
                    random.shuffle(players)
                    for t in range(number_of_teams):
                        teams[t+1] = []
                        for i in range(team_player_count):
                            teams[t+1].append(players.pop())
                    team_assignment_confirmation = ''
                    for team in teams:
                        team_assignment_confirmation += f'\n\n**TEAM *{team}*:**'
                        for player in teams[team]:
                            team_assignment_confirmation += f'\n*{player}*'
                    await ctx.send('**Ok here\'s the breakdown:**' + team_assignment_confirmation)
                this_game.teams = number_of_teams
            else:
                await ctx.send(f'**Okay *{this_game.title}* will be saved as free for all.**')
                this_game.teams = UNUSED
        except asyncio.TimeoutError:
            await ctx.send(TIMEOUT)
            return
    data.save()


@bot.command(brief='Show me your kitties!', help='Cool Shanta Water requires this exchange in #meow-talk')
async def meow(ctx: commands.Context):
    if ctx.guild.name == 'Cool Shanta Water' and ctx.channel.name != 'meow-talk':
        await ctx.send(f'**Do you really think *{ctx.channel}* is the appropriate place to meow?**')
        return
    with open(os.path.join('static', 'crackbrie.jpg'), 'rb') as f:
        pic = discord.File(f)
        await ctx.send(file=pic)


@bot.command(brief='Relive Celery Man',
             help='Conversation Starters (punctuation/case insensitive):\n- Load up Celery Man\n- Kick up the '
                  '4D3D3D3\n- Give me a printout of Oyster smiling\n- Can I see a hat wobble?\n- Do we have any new '
                  'sequences? (this prompt can be followed up with replies to computer: \'alright\' and \'nude tayne\')'
             )
async def computer(ctx: commands.Context, *, arg: str):
    if ctx.channel.name != 'computer':
        await ctx.send('Incorrect channel!')
        return
    arg = arg.translate(str.maketrans('', '', string.punctuation)).lower()
    if arg == 'can i see a hat wobble':
        with open(os.path.join('static', 'hat_wobble.gif'), 'rb') as f:
            pic = discord.File(f)
            await ctx.send(file=pic)
    elif arg == 'kick up the 4d3d3d3':
        with open(os.path.join('static', '4d3d3d3.gif'), 'rb') as f:
            pic = discord.File(f)
            await ctx.send(file=pic)
    elif arg == 'give me a printout of oyster smiling':
        with open(os.path.join('static', 'oyster_smiling.jpeg'), 'rb') as f:
            pic = discord.File(f)
            await ctx.send(file=pic)
    elif arg == 'load up celery man please':
        with open(os.path.join('static', 'celery_man.gif'), 'rb') as f:
            pic = discord.File(f)
            await ctx.send(file=pic)

    elif arg == 'do we have any new sequences':
        def check_celery_alright(msg: discord.Message):
            alright_submit = msg.content.lower().strip()
            bad_value = True
            try:
                if alright_submit == 'alright':
                    bad_value = False
            except TypeError or ValueError:
                pass
            return msg.author == ctx.author and msg.channel == ctx.channel and not bad_value
        await ctx.send('**I have a BETA sequence\nI have been working on\nWould you like to see it?**')
        try:
            alright = await bot.wait_for('message', check=check_celery_alright)
            if alright:
                with open(os.path.join('static', 'tayne.gif'), 'rb') as f:
                    pic = discord.File(f)
                    await ctx.send(file=pic)

                def check_nude_tayne(msg: discord.Message):
                    submit = msg.content.lower().strip()
                    bad_value = True
                    try:
                        if submit == 'nude tayne':
                            bad_value = False
                    except TypeError or ValueError:
                        pass
                    return msg.author == ctx.author and msg.channel == ctx.channel and not bad_value
                try:
                    nude = await bot.wait_for('message', check=check_nude_tayne, timeout=15)
                    if nude:
                        await ctx.send('**WARNING! THIS IS NOT SUITABLE FOR WORK!**')
                        with open(os.path.join('static', 'warning.jpg'), 'rb') as f:
                            pic = discord.File(f)
                            await ctx.send(file=pic)
                except TimeoutError:
                    await ctx.send('**Timed Out (you could have seen more...)**')

        except asyncio.TimeoutError:
            await ctx.send(TIMEOUT)
    else:
        await ctx.send('**Sorry, Paul. That is not a valid command.  Try *!help*...**')

if __name__ == '__main__':
    bot.run(os.environ['BOT_TOKEN'])
