import os
import random
import string
import time

import discord
import asyncio
from discord.ext import commands
# from dotenv import load_dotenv

# load_dotenv()
# TOKEN = input('enter token')

intents = discord.Intents.default()
intents.members = True
intents.presences = True
bot = commands.Bot(command_prefix='!', intents=intents)


class Player(object):
    def __init__(self, member):
        if type(member) == discord.Member:
            self.name = member.name  # [:-5]
            # self.tag_number = member.name[-5:]
            self.status = member.status
        else:
            self.name = member
            # self.tag_number = None
            self.status = 'NonDiscordUser'

        self.game_role = None
        self.team = None
        self.turn = None


class Game(object):
    def __init__(self, game_name):
        self.title = game_name
        self.game_id = int()
        self.game_roles = None
        self.teams = None
        self.times_played = None
        self.min_players = int()
        self.max_players = int()


'''
Once I'm confident that we are capturing the most essential parameters of a game, we will start saving the game 
profiles to a json or .txt or something to be retrieved into game cache.... although the cache will have to be 
fetched routinely... Well we can just refresh it after each full interaction with setup
'''
games_cache = []
game_ids = [gm.game_id for gm in games_cache]


def new_id():
    try:
        new = max(game_ids) + 1
    except ValueError:
        new = 1
    game_ids.append(new)
    return new


@bot.event  # @client.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord')
    for guild in bot.guilds:
        print(f'registered on {guild.name}')


@bot.command()
async def setup(ctx: commands.Context):
    """THIS IS THE 'MAIN LOOP' - triggered by typing !setup in Discord.
    Making sure messages are in appropriate channel, ignoring bot"""
    if ctx.author == bot.user:
        return
    if ctx.guild.name == 'Cool Shanta Water' and ctx.channel.name != 'boardgames':
        await ctx.send('To avoid server clutter, we should probably do this in the appropriate channel...')
        return

    """validation methods (checks)"""
    def check_yn(msg: discord.Message):
        return msg.author == ctx.author and msg.channel == ctx.channel and msg.content.lower() in ['y', 'n']

    def check_reasonable_int(msg: discord.Message):
        bad_value = False
        try:
            if not 0 <= int(msg.content) <= 15:
                bad_value = True
        except TypeError or ValueError:
            bad_value = True
        return not bad_value

    def check_game_selection(msg: discord.Message):
        bad_value = False

        if msg.content.strip().lower() == 'new':
            return not bad_value
        try:
            if int(msg.content) not in game_ids:
                bad_value = True
        except TypeError or ValueError:
            bad_value = True
        return not bad_value

    hi = f'Let\'s set up a new game!  I have these previously configured games already saved.  If you would like ' \
         f'to play one of these again, enter the corresponding number.  Otherwise, type [new] to set up a new game...\n'
    await ctx.send(hi)

    for g in games_cache:
        await ctx.send(f'{g.game_id}) {g.title} -- supports {g.min_players}-{g.max_players} players')

    this_game = None
    game_select = await bot.wait_for('message', check=check_game_selection, timeout=30)
    game_select = game_select.content
    if game_select.strip().lower() == 'new':
        await ctx.send('Woohoo! A new game!  What is its title?')
        title_input = await bot.wait_for('message')
        title_input = title_input.content.strip().capitalize()
        this_game = Game(title_input)
        this_game.game_id = new_id()
        await ctx.send(f'Minimum player count for {this_game.title}?')
        minc = await bot.wait_for('message', check=check_reasonable_int)
        this_game.min_players = int(minc.content)
        await ctx.send(f'Maximum player count for {this_game.title}?')
        maxc = await bot.wait_for('message', check=check_reasonable_int)
        this_game.max_players = int(maxc.content)
        await ctx.send(f'Okay, we will configure more setup parameters for {this_game.title} as we go along.\n\n')
    else:
        for g in games_cache:
            if g.game_id == game_select:
                this_game = g

    members_list_prompt = f'I have detected the following members of {ctx.guild.name}:'
    member_dict = {}
    i = 1
    for m in ctx.guild.members:  # list all members in server and prompt user to select some as Players
        if m == bot.user:
            continue
        member_dict[i] = m
        members_list_prompt += f'\n{i}) {m.name} - {m.status}'
        i += 1
    members_list_prompt += f'\n\nPlease enter the player numbers you want to include for this game separated by ' \
                           f'commas.\nIf you need to add a player not in {ctx.guild.name}, we\'ll do that next.'
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
        selected_confirmation = 'Selected Players:\n'
        for x in player_select_input.content.replace(' ', '').split(','):
            p = Player(member_dict[int(x)])
            players.append(p)  # creating instances of class Player for each selected member
            selected_confirmation += f'{p.name}\n'
    except asyncio.TimeoutError:
        await ctx.send('Timed Out')
        return
    await ctx.send(selected_confirmation)
    if not len(players) >= this_game.max_players:
        await ctx.send(f'\n\nWould you like to add any other players?  [y/n]')
        try:
            add_players_yn = await bot.wait_for('message', check=check_yn, timeout=15)
            if add_players_yn.content.lower() == 'y':
                await ctx.send('\nHow many more players would you like to add?')
                extra_player_count = await bot.wait_for('message', check=check_reasonable_int)
                extra_player_count = int(extra_player_count.content)
                added_players_confirmation = ''
                for c in range(extra_player_count):
                    await ctx.send(f'Enter name for extra player {c + 1}')
                    new_name = await bot.wait_for('message')
                    p = Player(new_name.content)
                    players.append(p)
                for p in players:
                    added_players_confirmation += f'\n{p.name}'
                await ctx.send('Updated Player List:' + added_players_confirmation)
        except asyncio.TimeoutError:
            await ctx.send('Timed Out')
            return

    players_dict = {}
    for i in range(1, len(players)+1):
        players_dict[i] = players.pop()

    while len(list(players_dict.values())) > this_game.max_players:
        axed = False
        while not axed:
            await ctx.send('Too many players.  Axe someone! (input player number)\n')
            chopping_block = ''
            for p in players_dict.keys():
                chopping_block += f'{p}) {players_dict[p].name}\n'
            await ctx.send(chopping_block)
            axed = await bot.wait_for('message', check=check_reasonable_int)
            axed = int(axed.content)
            try:
                players_dict.pop(axed)
                axed = True
            except KeyError:
                await ctx.send('\nInvalid choice!')

    player_list = 'Final Player List:\n'
    for p in players_dict.values():
        player_list += f'{p.name}\n'
    await ctx.send(player_list)

    await ctx.send('Do we want to setup roles? [y/n]')
    try:
        yn_roles = await bot.wait_for('message', check=check_yn, timeout=15)
        if yn_roles.content.lower() == 'y':
            roles_list_confirmation = ''
            roles_dict = {}
            await ctx.send('How many roles?')
            number_roles = await bot.wait_for('message', check=check_reasonable_int)
            for n in range(1, int(number_roles.content) + 1):
                await ctx.send(f'Name for Role {n}?')
                role_name = await bot.wait_for('message')
                roles_dict[n] = role_name.content
                roles_list_confirmation += f'\n{n}) {roles_dict[n]}'
            roles = list(roles_dict.values())
            this_game.game_roles = roles
            await ctx.send('\n\nOk I have these roles:' + roles_list_confirmation +
                           '\n\nWould you like to manually assign roles? [y,n] If no, will be done randomly.')
            yn_role_assign = await bot.wait_for('message', check=check_yn)
            role_assignment_confirmation = ''
            if yn_role_assign.content.lower() == 'y':
                await ctx.send('Okay. Referencing the above list, '
                               'enter the role number you wish to assign to each player...\n')
                for p in players:
                    await ctx.send(f'Role number for {p.name}?')
                    choice = await bot.wait_for('message')
                    p.game_role = roles_dict[int(choice.content)]
                    role_assignment_confirmation += f'\n{p.name}: {p.game_role}'
            else:
                random.shuffle(players)
                random.shuffle(roles)
                for p in players:
                    p.game_role = roles.pop()
                    role_assignment_confirmation += f'\n{p.name}: {p.game_role}'
            await ctx.send('Okay here is the breakdown:\n' + role_assignment_confirmation)

    except asyncio.TimeoutError:
        await ctx.send('Timed Out')

    await ctx.send('Is this a team game? Enter [0] for \"No\", or Enter the # of Teams.')
    try:
        number_of_teams = await bot.wait_for('message', check=check_reasonable_int, timeout=15)
        number_of_teams = int(number_of_teams.content)
        if number_of_teams > 0:
            await ctx.send(f'Ok. I have {number_of_teams} teams.  Do we want to evenly distribute players across '
                           f'teams? [y/n]')
            yn = await bot.wait_for('message', check=check_yn)
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
                    team_assignment_confirmation += f'\n\nTEAM {team}:'
                    for player in teams[team]:
                        team_assignment_confirmation += f'\n{player}'
                await ctx.send('Ok here\'s the breakdown:' + team_assignment_confirmation)
        else:
            await ctx.send('FREE FOR ALL!')
    except asyncio.TimeoutError:
        await ctx.send('Timed Out')
        return


@bot.command()
async def meow(ctx: commands.Context):
    if ctx.guild.name == 'Cool Shanta Water' and ctx.channel.name != 'meow-talk':
        await ctx.send(f'Do you really think {ctx.channel} is the appropriate place to meow?')
        return
    with open(os.path.join('static', 'crackbrie.jpg'), 'rb') as f:
        pic = discord.File(f)
        await ctx.send(file=pic)


@bot.command()
async def computer(ctx: commands.Context, *, arg: str):
    if ctx.channel.name != 'computer':
        await ctx.send('Incorrect channel!')
        return
    arg = arg.translate(str.maketrans('', '', string.punctuation))
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
            try:
                if alright_submit == 'alright':
                    return True
                else:
                    return False
            except TypeError or ValueError:
                return False
        await ctx.send('I have a BETA sequence\nI have been working on\nWould you like to see it?')
        try:
            alright = await bot.wait_for('message', check=check_celery_alright)
            if alright:
                with open(os.path.join('static', 'tayne.gif'), 'rb') as f:
                    pic = discord.File(f)
                    await ctx.send(file=pic)

                def check_nude_tayne(msg: discord.Message):
                    submit = msg.content.lower().strip()
                    try:
                        if submit == 'nude tayne':
                            return True
                        else:
                            return False
                    except TypeError or ValueError:
                        return False
                try:
                    nude = await bot.wait_for('message', check=check_nude_tayne, timeout=15)
                    if nude:
                        await ctx.send('WARNING! THIS IS NOT SUITABLE FOR WORK!')
                        with open(os.path.join('static', 'warning.jpg'), 'rb') as f:
                            pic = discord.File(f)
                            await ctx.send(file=pic)
                except TimeoutError:
                    await ctx.send('Timed Out (you could have seen more...)')

        except asyncio.TimeoutError:
            await ctx.send('Timed Out')
    else:
        await ctx.send('Sorry, Paul. That is not a valid command')

if __name__ == '__main__':
    bot.run(os.environ['BOT_TOKEN'])
