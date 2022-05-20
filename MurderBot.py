version = "1.9.5"
# come find me hehe
#Imports
from ast import alias
import asyncio
from tempfile import TemporaryFile
import discord
import os
import youtube_dl

from discord import FFmpegPCMAudio
from argparse import ArgumentError
from discord.ext import commands, tasks
from discord.ext.commands import Bot
from nick import Nick
from voice import Voice
from random import randint
from words import allPhrases

# Variables
token = 'OTc1Mzc4MTAwNjMwMjE2NzA0.GMnQja.-sXdYIJdBQMY5KH5zkJFpYqG7WFqLe1O7y93SU'
target = 694382869367226368
options = allPhrases()
global permanent_file, alt_file
permanent_file = "Memory/permanent.txt"
alt_file = "Memory/alt.txt"
players = {}

#Bot setup
bot = commands.Bot(command_prefix='.', intents=discord.Intents.all(), case_insensitive=True, strip_after_prefix=True, status=discord.Status.invisible)


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
        if adminRole2 in member.roles:
            newHigherAdmin(member)

#Make Admin Method
def newAdmin(admin:discord.Member):
    #Adds admin to admins list
    admins.append(admin)

#Make HigherAdmin Method
def newHigherAdmin(higherAdmin:discord.Member):
    #Adds admin to admins list
    higher_admins.append(higherAdmin)


#On bot start up
@bot.event
async def on_ready():
    #Globalise all variables
    global admins, guild, higher_admins, lists, options, out_of_context, perm_nicknames, phrases, target
    #Initliase variables and lists
    admins = []
    alt_nicknames = []
    phrases = options[0]
    out_of_context = options[1] 
    perm_nicknames = []
    lists = [perm_nicknames, alt_nicknames]
    higher_admins = []

    
    #Tell Console we have logged in
    print(f"We have logged in as {bot.user}")
    #Prepare bot
    await bot.wait_until_ready()
    
    #Get current server
    guild = bot.guilds[0]


    #Find out who had permanent nick names before bot shutdown
    with open(permanent_file) as fd:
        lines = fd.readlines()
        for i, line in enumerate(lines):
            user = int(line.partition(":")[0])
            #nickname = line.partition(":")[2]
            perm_nicknames.append(user)
        fd.close
    #Find out who had an alternating nick name before bot shutdown
    with open(alt_file) as fd:
        lines = fd.readlines()
        for i, line in enumerate(lines):
            user = int(line.partition(":")[0])
            parameters = line.partition(":")[2]
            parameters = parameters.split()
            time = parameters[2]
            current_nick = guild.get_member(user).nick
            if current_nick == parameters[0]:
                nick = parameters[1]
            elif current_nick == parameters[1]:
                nick = parameters[0]
            else:
                index = [(i, id.index(user)) for i, id in enumerate(alt_nicknames) if user in id][0][0]
                alt_nicknames.pop(index)
                continue
            alt_nicknames.append([user, nick, time])
        fd.close


    #Check all admins
    checkAdmin()
    #Initialise nick commands class
    bot.add_cog(Nick(bot, lists))
    bot.add_cog(Voice(bot, higher_admins))
    if len(alt_nicknames) != 0:
        nick_cog = bot.get_cog("Nick")
        await nick_cog.set_alt_nick_on_ready()
    
    

    
    

    
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
async def move_all_away(ctx, member:discord.Member=None):
    #Check if no target
    if member == None:
        member = guild.get_member(target) #target
    #channel = discord.utils.get(bot.get_all_channels(), name="Noncess")
    name = member.name
    value = randint(0, 2)

    #Move everyone except targetted person
    for i, channel in enumerate(guild.voice_channels):
        if member in channel.members:
            for user in channel.members:
                if user.name == name:
                    continue
                while value == i:
                    value = randint(0, 2)
                await user.move_to(guild.voice_channels[value])
            return


 
@bot.command(aliases = ["rc"])
async def rollercoaster(ctx, member:discord.Member=None, movetimes:int = 1):
    #Check if no target
    if member == None:
        member = ctx.author

    initial_channel = member.voice.channel

    if member.voice is None:
        return await ctx.send("User is not in a channel")
    
    if movetimes < 1:
        return await ctx.send("Please move at least 1 time")

    if movetimes > 15:
        return await ctx.send("You can only move up to 15 times!")

    #name = member.display_name
    value = randint(0,2)

    await ctx.send(f"Enjoy the ride <@{member.id}>!!!")
    #print(movetimes)
    for i in range(movetimes):
        prev = value
        while value == prev:
            value = randint(0, 2)
        await member.move_to(guild.voice_channels[value])
        await asyncio.sleep(0.15)
    await asyncio.sleep(1)
    if member.voice.channel != initial_channel:
        await member.move_to(initial_channel)




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

@bot.command(brief="Plays a song")
async def play(ctx, song:str):
    current_vc = ctx.author.voice.channel
    vc = discord.utils.get(bot.voice_clients, guild = ctx.guild)
    if vc is None:
        await current_vc.connect()
    vc = discord.utils.get(bot.voice_clients, guild = ctx.guild)
    if vc.is_paused():
        vc.resume()
    else:
        vc.play(discord.FFmpegPCMAudio(f"Songs/{song}.mp3"))

@bot.command()
async def pause(ctx):
    voice = discord.utils.get(bot.voice_clients, guild = ctx.guild)
    if voice is None:
        return
    if voice.is_playing():
        voice.pause()
    else:
        await ctx.send("Currently no audio is playing")

@bot.command()
async def stop(ctx):
    voice = discord.utils.get(bot.voice_clients, guild = ctx.guild)
    if voice is None:
        return
    voice.stop()

    await ctx.send("Stopped audio")

snipe_message_author = {}
snipe_message_content = {}

@bot.event
async def on_message_delete(message):
     snipe_message_author[message.channel.id] = message.author
     snipe_message_content[message.channel.id] = message.content
     await asyncio.sleep(60)
     del snipe_message_author[message.channel.id]
     del snipe_message_content[message.channel.id]


@bot.command()
async def snipe(ctx, channel:discord.TextChannel=None):
    if channel == None:
        channel = ctx.channel
    try: #This piece of code is run if the bot finds anything in the dictionary
        em = discord.Embed(name = f"Last deleted message in #{channel.name}", description = snipe_message_content[channel.id])
        em.set_footer(text = f"This message was sent by {snipe_message_author[channel.id]}")
        await ctx.send(embed = em)
    except KeyError: #This piece of code is run if the bot doesn't find anything in the dictionary
        await ctx.send(f"There are no recently deleted messages in #{channel.name}")


#Run's the bot
bot.run(token)




