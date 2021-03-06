version = "1.9.5"
# come find me hehe
#Imports
from ast import alias
import asyncio
from re import T

import discord
import os
import datetime
import time

from discord import FFmpegPCMAudio
from argparse import ArgumentError
from discord.ext import commands, tasks
from discord.ext.commands import Bot
from nick import Nick
from voice import Voice
from software import Software
from random import randint
from words import allPhrases
from banned import Banned
from canvas import CanvasCog

# Variables
token = open(".git/token.txt","r").read()
target = 694382869367226368
options = allPhrases()
global permanent_file, alt_file
permanent_file = "Memory/permanent.txt"
alt_file = "Memory/alt.txt"
players = {}
jumpscareBool = True

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
        if member.id == 309198720606404609:
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
    global admins, guild, higher_admins, lists, options, out_of_context, perm_nicknames, phrases, target, jumpscareBool
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

    global jumpscareTask
    jumpscareTask = jumpscare.start()

    #Check all admins
    checkAdmin()
    #Initialise nick commands class
    bot.add_cog(Nick(bot, lists))
    bot.add_cog(Voice(bot, higher_admins))
    bot.add_cog(Software(bot))
    bot.add_cog(CanvasCog(bot))
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
    if message.author in higher_admins:# or message.author.id == 288884848012296202:
        await bot.process_commands(message)
    elif message.author in admins:# and message.channel.id == 975385087677960263:
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
        await ctx.send('Incorrect arguments entered')
    if isinstance(error, commands.BadArgument):
        await ctx.send('Incorrect arguments entered')
    print(error)



#Send method (Move to another class)
@bot.command(brief="Send a message via the bot to a channel")
async def send(ctx, channel:discord.TextChannel, *, message):
    await ctx.message.delete()
    #Send's message to given channel
    await channel.send(message)

#Ping pong
@bot.command(brief="Pong")
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


@bot.command(brief="Moves everyone away from target")
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

global coasterUsers
coasterUsers = []
global timedOutMembers
timedOutMembers = {}


@tasks.loop(hours = 1000)
async def jumpscare():
    while True:
        await asyncio.sleep(2)
        #print(discord.utils.get(bot.voice_clients, guild = guild))
        #print(jumpscareBool)
        number=randint(30,600)
        print(number)
        await asyncio.sleep(number)
        if jumpscareBool == True and discord.utils.get(bot.voice_clients, guild = guild) != None:
                print("boom time")
                selfPlay("boom")


def selfPlay(song):
   
    vc = discord.utils.get(bot.voice_clients, guild = guild)
    if vc.is_paused():
        vc.resume()
    else:
        vc.play(discord.FFmpegPCMAudio(f"Songs/{song}.mp3"))



@bot.command(brief = "Toggle the boom noise", aliases = ["bT"])
async def boomToggle(ctx):
    global jumpscareBool
    jumpscareBool = not jumpscareBool
    await ctx.send("Jumpscare is now {}".format(jumpscareBool))



@bot.event
async def on_voice_state_update(member, before, after):
    channel = discord.utils.get(bot.get_all_channels(), name="bot_commands")
    #On join
    if not before.channel and after.channel:
        #if member.id == 975378100630216704:
            #jumpscareTask = await jumpscare.start()
        pass


    #On disconnect
    if before.channel and not after.channel:

            

        print(f'{member} has left {before.channel}')
        if member.id in bannedMembers:
            memberPos = bannedMembers.index(member.id)
            ban = bans[memberPos]
            await asyncio.sleep(ban.banTime)
            try:
                bannedMembers.remove(member.id)
                bans.pop(memberPos)
            except ValueError:
                pass
            
        if member.id in coasterUsers:
            await channel.send(f'{member} left WHILE COASTING!')
            timedOutMembers[member.id] = time.time()
            coasterUsers.remove(member.id)
            await asyncio.sleep(10)
            timedOutMembers.pop(member.id)

    #Moved Channel
    if before.channel and after.channel:
        pass

    #On channel connect
    if after.channel:
        print(f'{member} has joined {after.channel}')
        if member.id in timedOutMembers:
            await member.move_to(None, reason="Timed out")
            await channel.send(f"{member} tried to rejoin VC but had too many injuries from falling off the coaster!")
            if member.id in coasterUsers:
                coasterUsers.remove(member.id)
            try:
                await channel.send(f"Please wait {10 - int(time.time() - timedOutMembers[member.id])} seconds")
            except KeyError:
                pass

        if member.id in bannedMembers:
            memberPos = bannedMembers.index(member.id)
            ban = bans[memberPos]
            if after.channel == ban.channel:
                await member.move_to(None, reason="Timed out")
                await channel.send(f"{member} tried to rejoin {ban.channel} but is banned")

                try:
                    await channel.send(f"Please wait {ban.banTime - int(time.time() - ban.realTime)} seconds")
                except KeyError:
                    pass



 
@bot.command(brief="Rollercoasts a user", aliases = ["rc"])
async def rollercoaster(ctx, member:discord.Member=None, movetimes:int = 1):
    #Check if no target
    if member == None:
        member = ctx.author

    if ctx.author.id == 694382869367226368:
        #if member.id == 288884848012296202:
        member = ctx.author
    initial_channel = member.voice.channel

    if member.voice is None:
        return await ctx.send("User is not in a channel")
    
    if movetimes < 1:
        return await ctx.send("Please move at least 1 time")

    if movetimes > 15 and ctx.author not in higher_admins:
        return await ctx.send("You can only move up to 15 times!")

    coasterUsers.append(member.id)
    #name = member.display_name
    value = randint(0,2)
    await ctx.send(f"Coasting {movetimes} times")
    await ctx.send(f"Enjoy the ride <@{member.id}>!!!")
    #print(movetimes)
    for i in range(movetimes):
        print(i+1)
        prev = value
        while value == prev:
            value = randint(0, 2)
        await member.move_to(guild.voice_channels[value])
        await asyncio.sleep(0.15)
    await asyncio.sleep(1)
    if member.voice.channel != initial_channel:
        await member.move_to(initial_channel)
    if member.id in coasterUsers:
        coasterUsers.remove(member.id)

global bannedMembers
bannedMembers = []
global bans
bans = []

@bot.command(brief = "Keep someone out of a voice channel")
async def ban(ctx, member:discord.Member=None, bantime:int=10, channel:discord.VoiceChannel=None):
    if member.id in bannedMembers:
        return await ctx.send(f"{member} is already banned LOL")
    if member == None:
        member = guild.get_member(694382869367226368)
    if channel == None:
        channel = ctx.author.voice.channel
    if member.voice.channel == channel:
        await member.move_to(None, reason="Timed out")
    newBan = Banned(bot, member, channel, bantime)
    bannedMembers.append(member.id)
    bans.append(newBan)






#Checks for admins            
@bot.command(brief="Checks the current admins")
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
@bot.command(brief="Send's an annonymous dm to a user")
async def send_dm(ctx, user:discord.Member, *, message: str):
    #Hide your message
    await ctx.message.delete()
    #Creates a private dm
    channel = await user.create_dm()
    #Send's dm to user
    await channel.send(message)

@bot.command(brief="Lists playable sounds")
async def list(ctx):
    sounds = []
    sound_list = os.listdir("Songs")
    for i, x in enumerate(sound_list):
        x = x.replace(".mp3", "")
        sounds.append(x)
    await ctx.send(sounds)

@bot.command(brief="Plays audio from bot")
async def play(ctx, song:str):
    vc = discord.utils.get(bot.voice_clients, guild = guild)
    if vc is None:
        current_vc = discord.utils.get(bot.get_all_members(), id=ctx.author.id).voice.channel
        await current_vc.connect()
    vc = discord.utils.get(bot.voice_clients, guild = guild)
    if vc.is_paused():
        vc.resume()
    else:
        vc.play(discord.FFmpegPCMAudio(f"Songs/{song}.mp3"))

@bot.command(brief="Pauses the audio from bot")
async def pause(ctx):
    voice = discord.utils.get(bot.voice_clients, guild = guild)
    if voice is None:
        return
    if voice.is_playing():
        voice.pause()
    else:
        await ctx.send("Currently no audio is playing")

@bot.command(brief="Stops the audio from bot")
async def stop(ctx):
    voice = discord.utils.get(bot.voice_clients, guild = guild)
    if voice is None:
        return
    voice.stop()

    await ctx.send("Stopped audio")

snipe_message_author = {}
snipe_message_content = {}

@bot.event
async def on_message_delete(message):
    if message.content.startswith("."):
        return
    print(f"A message was deleted in channel {message.channel}")
    print(f"{message.author} said:\n{message.content}")
    if message.author.id == 975378100630216704:
        #await message.channel.send(message.content)
        return
    if not message.channel.id in snipe_message_author or not message.channel.id in snipe_message_content:
        snipe_message_author[message.channel.id] = [message.author]
        snipe_message_content[message.channel.id] = [message.content]
    else:

        snipe_message_author[message.channel.id].append(message.author)
        snipe_message_content[message.channel.id].append(message.content)
        # await asyncio.sleep(60)
        # del snipe_message_author[message.channel.id]
        # del snipe_message_content[message.channel.id]


@bot.command(brief="Snipes the last deleted message")
async def snipe(ctx, channel:discord.TextChannel=None):
    if channel == None:
        channel = ctx.channel
    try: #This piece of code is run if the bot finds anything in the dictionary
        for index, value in enumerate(snipe_message_content[channel.id]):
            em = discord.Embed(name = f"Deleted message in #{channel.name}", description = value)
            em.set_footer(text = f"This message was sent by {snipe_message_author[channel.id][index].name}")
            await ctx.send(embed = em)
    except KeyError: #This piece of code is run if the bot doesn't find anything in the dictionary
        await ctx.send(f"There are no recently deleted messages in #{channel.name}")

@bot.command(brief="Clears the snipe log", aliases=["snipeclear","snipec", "sc"])
async def snipe_clear(ctx):
    if ctx.message.author not in higher_admins:
        return await ctx.send("You do not have permission to clear snipe log")
    snipe_message_author.clear()
    snipe_message_content.clear()
    return await ctx.send("Cleared snipe log")

@bot.command(brief="Deletes a user's messages in a given channel (testing purposes ONLY", aliases=["delete", "del"])
async def delete_messages(ctx, member:discord.Member, limit:int, channel:discord.TextChannel=None):
    if channel == None:
        channel = ctx.channel
    if ctx.message.author.id != 238063640601821185:
        return await ctx.send("You do not have access to this command")
    counter = 0
    msgs = []
    extra = 0
    if ctx.message.author.id == member.id:
        extra = 1
    for msg in await channel.history().flatten():
        if msg.author.id == member.id:
            msgs.append(msg)
            counter += 1
        if counter == limit+extra:
            break
    
    print(len(msgs))
    await channel.delete_messages(msgs)

    
    #await message.delete()

#Changes status of the discord bot
@bot.command(brief="Changes status of the bot", aliases = ["status", "cs"])
async def change_status(ctx, newstatus:discord.Status): 
    #Changes the status of the bot
    await bot.change_presence(status=newstatus)
    #Notifies user of status change 
    await ctx.send(f"Status successfully changed to {newstatus}")

#Run's the bot
try:
    bot.run(token)
except:
    import traceback
    traceback.print_exc()



