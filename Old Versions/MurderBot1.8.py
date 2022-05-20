#Imports
import asyncio
import discord
from argparse import ArgumentError
from discord.ext import commands, tasks
from discord.ext.commands import Bot
from nick import Nick
from random import randint
from words import allPhrases

# Variables
token = 'OTc1Mzc4MTAwNjMwMjE2NzA0.GMnQja.-sXdYIJdBQMY5KH5zkJFpYqG7WFqLe1O7y93SU'
target = 694382869367226368
options = allPhrases()

#Bot setup
bot = commands.Bot(command_prefix='.', intents=discord.Intents.all(), case_insensitive=True, strip_after_prefix=True)

#Check Admin Method
def checkAdmin():
    #Clears the admins list
    admins.clear()
    #Gets the valid admin roles
    adminRole = discord.utils.get(guild.roles, name="Murderer")
    adminRole2 = discord.utils.get(guild.roles, name="dn")
    #Checks which members in the server are admins
    for member in guild.members:
        #If they are admin make them an admin of the bot
        if adminRole in member.roles or adminRole2 in member.roles:
            newAdmin(member)

#Make Admin Method
def newAdmin(admin:discord.Member):
    #Adds admin to admins list
    admins.append(admin)


#On bot start up
@bot.event
async def on_ready():
    #Globalise all variables
    global admins, guild, lists, options, out_of_context, perm_nicknames, phrases, target, text_channels, voice_channels
    #Initliase variables and lists
    admins = []
    alt_nicknames = []
    phrases = options[0]
    out_of_context = options[1] 
    voice_channels = []
    text_channels = []
    perm_nicknames = []
    lists = [perm_nicknames, alt_nicknames]
    
    #Tell Console we have logged in
    print(f"We have logged in as {bot.user}")
    #Prepare bot
    await bot.wait_until_ready()
    
    #Get current server
    guild = bot.guilds[0]

    #Check all admins
    checkAdmin()
    #Initialise nick commands class
    bot.add_cog(Nick(bot, lists))
    
    #Check which channels are voice and text
    for channel in bot.get_all_channels():
        #Append voice channels to voice_channels
        if isinstance(channel, discord.channel.VoiceChannel):
            voice_channels.append(channel)
        #Append text channels to text_channels
        elif isinstance(channel, discord.channel.TextChannel):
            text_channels.append(channel)
    
    #Find out who had permanent nick names before bot shutdown
    with open('permanent.txt') as fd:
        lines = fd.readlines()
        for i, line in enumerate(lines):
            user = int(line.partition(":")[0])
            nickname = line.partition(":")[2]
            perm_nicknames.append(user)


    
###########################################################    

#On message method
@bot.event
async def on_message(message):
    #Checks if it is ROHIT and not a command
    if message.author == guild.get_member(target) and not message.content.startswith("."):
        random_opt = randint(0,1)
        random1 = randint(0, len(phrases)-1)
        random2 = randint(0, len(out_of_context)-1)
        randoms = [random1, random2]
        #Send a random message from rohit's past
        await message.channel.send(f"{options[random_opt][randoms[random_opt]]}")
    #If they valid then let them use commands (also has to be in bot commands)
    if message.author in admins and message.channel.id == 975385087677960263:
        await bot.process_commands(message)

#Error Handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Unknown Command!")
    if isinstance(error, commands.ChannelNotFound):
        await ctx.send("Channel not Found!")
    if isinstance(error, commands.MemberNotFound):
        await ctx.send("Member not Found!")
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Inccorrect arguments entered')


#Bot join VC (Move to another class)
@bot.command()
async def join(ctx, *, channel:str=None):
    
    #Check if the author is in a voice channel (NOT WORKING ATM)
    #if ctx.author in str(voice_channels[0].member):
        #await ctx.send("You are not in a voice channel!")
    #Check if the channel argument is empty
    if channel == None:
        channel = ctx.author.voice.channel
    #Check if their specified channel is valid
    else:
        #Check if the channel argument is valid
        for i, chan in enumerate(voice_channels):
            if channel.lower() == str(chan.name).lower():
                channel = chan
                break

        if isinstance(channel, discord.VoiceChannel):
            pass
        else: 
            #Tell user they did not put in a correct argument
            await ctx.send("You did not provide a valid voice channel")
    await channel.connect()

#Bot leave VC (Move to another class)
@bot.command()
async def leave(ctx):
    #Get current vc bot is in
    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    #Disconnect bot
    await vc.disconnect()

#Send method (Move to another class)
@bot.command()
async def send(ctx, channel:discord.TextChannel, *, message):
    await ctx.message.delete()
    #Send's message to given channel
    await channel.send(message)

#Ping pong
@bot.command()
async def ping(ctx, member:discord.Member=None, channel:discord.TextChannel=None):
    #Ping's author
    if member == None:
        member = ctx.message.author
    #Ping's user in current channel
    if channel == None:
        channel = ctx.channel
    #channel = discord.utils.get(bot.get_all_channels(), name="sounds")
    if member.status != discord.Status.offline:
        await channel.send(f"Hi <@{member.id}>!!")
    else:
        await channel.send(f"Where is <@{member.id}>?")


@bot.command()
async def move(ctx, member:discord.Member=None):
    #Check if no target
    if member == None:
        member = guild.get_member(target) #target
    await bot.wait_until_ready()
    #channel = discord.utils.get(bot.get_all_channels(), name="Noncess")
    name = member.name
    value = randint(0, 2)

    #Move everyone except targetted person
    for i in range(len(voice_channels)):
        if f"{name}" in str(voice_channels[i].members):
            for user in voice_channels[i].members:
                if user.name == name:
                    continue
                while value == i:
                    value = randint(0, 2)
                await user.move_to(voice_channels[value])


#Checks for admins            
@bot.command()
async def check_admins(ctx):
    await ctx.send("Checking admins...")
    checkAdmin()
    if len(admins) != 0:
        #List all admins
        await ctx.send("Found admins:")
        for i, person in enumerate(admins):
            await ctx.send(f"{person.name}")
        #Announce finished
        await ctx.send("Finished")
    else:
        #List is empty
        await ctx.send("No admins found!")
    
#Send a private dm to a person
@bot.command()
async def send_dm(ctx, user:discord.Member, *, message: str):
    #Hide your message
    await ctx.message.delete()
    #Creates a private dm
    channel = await user.create_dm()
    #Send's dm to user
    await channel.send(message)


#Run's the bot
bot.run(token)




