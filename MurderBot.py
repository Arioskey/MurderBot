version = "2.0"
#Imports

import asyncio

import discord
import os
import datetime
import time
import traceback

from discord import FFmpegPCMAudio, app_commands
from argparse import ArgumentError
from discord.ext import commands, tasks
from discord.ext.commands import Bot
from discord.ui import Button, View
from nick import Nick
from voice import Voice
from software import Software
from random import randint
from words import allPhrases
from banned import Banned
from canvas import CanvasCog
from connect4 import Connect4
from cards import Cards
from canvasapi.exceptions import InvalidAccessToken, ResourceDoesNotExist, Forbidden
from typing import Optional, Union
from datetime import datetime
from requests import get
from io import BytesIO
from PIL import Image, ImageDraw, ImageOps

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
bot = commands.Bot(command_prefix='.', test_guilds= [852379093776465940], intents=discord.Intents.all(), case_insensitive=True, strip_after_prefix=True, status=discord.Status.invisible)



#On bot start up
@bot.event
async def on_ready():
    #Globalise all variables
    global guild, lists, options, out_of_context, perm_nicknames, phrases, target, jumpscareBool
    #Initliase variables and lists
    alt_nicknames = []
    phrases = options[0]
    out_of_context = options[1] 
    perm_nicknames = []
    lists = [perm_nicknames, alt_nicknames]
    

 

    #Tell Console we have logged in
    print(f"We have logged in as {bot.user}")
    #Prepare bot 

    await bot.add_cog(CanvasCog(bot))

    await bot.add_cog(Nick(bot, lists))
    await bot.add_cog(Voice(bot))
    await bot.add_cog(Software(bot))
    await bot.add_cog(Cards(bot))
    await bot.add_cog(Connect4(bot))
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

    #Initialise nick commands class

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
    if message.content.startswith("."):
        await bot.process_commands(message)
    if message.content.startswith('!hello'):
        embedVar = discord.Embed(title="Title", description="Desc", color=0x00ff00)
        embedVar.add_field(name="Field1", value="hi", inline=True)
        embedVar.add_field(name="Field2", value="hi2", inline=False)
        await message.channel.send(embed=embedVar)

#Error Handling
@bot.tree.error
async def on_command_error(interaction:discord.Interaction, error):
    if isinstance(error, discord.app_commands.CommandInvokeError):
        error = error.original
    if isinstance(error, InvalidAccessToken):
        await interaction.response.send_message("Invalid Token")
    if isinstance(error, commands.CommandNotFound):
        await interaction.response.send_message("Unknown Command!")
    if isinstance(error, commands.ChannelNotFound):
        await interaction.response.send_message("Channel not Found!")
    if isinstance(error, commands.MemberNotFound):
        await interaction.response.send_message("Member not Found!")
    if isinstance(error, commands.MissingRequiredArgument):
        await interaction.response.send_message('Incorrect arguments entered')
    if isinstance(error, commands.BadArgument):
        await interaction.response.send_message('Incorrect arguments entered')
    if isinstance(error, discord.errors.NotFound):
        await interaction.channel.send("MurderBot was having a moment, try again!")
    if isinstance(error, discord.app_commands.errors.TransformerError):
        await interaction.response.send_message("Incorrect arguments entered")
        await interaction.channel.send(f"{error}")
    print('Ignoring exception in command {}:'.format(interaction.command))
    traceback.print_exception(type(error), error, error.__traceback__)        




#Send method (Move to another class)
@bot.tree.command(name = "send", description="Send a message via the bot to a channel")
async def send(interaction: discord.Interaction, channel:discord.TextChannel, *, message:str):
    #Send's message to given channel
    await channel.send(message)
    return await interaction.response.send_message("Sent message!")


#Ping pong
@bot.tree.command(name = "ping", description="Pong")
async def ping(interaction: discord.Interaction, member:discord.Member=None, channel:discord.TextChannel=None):
    #Ping's author
    if member == None:
        member = interaction.user
    #Ping's user in current channel
    if channel == None:
        channel = interaction.channel
    #channel = discord.utils.get(bot.get_all_channels(), name="sounds")
    if member.status != discord.Status.offline:
        await channel.send(f"Hi <@{member.id}>!!")
    else:
        await channel.send(f"Where is <@{member.id}>?")
    await interaction.response.send_message("Pinged!")


@bot.tree.command(description="Moves everyone away from target")
async def move_all_away(interaction: discord.Interaction, member:discord.Member=None):
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
            return await interaction.response.send_message("Moved all away", ephemeral=True)

global coasterUsers
coasterUsers = []
global timedOutMembers
timedOutMembers = {}


@tasks.loop()
async def jumpscare():
    while True:
        await asyncio.sleep(2)
        #print(discord.utils.get(bot.voice_clients, guild = guild))
        #print(jumpscareBool)
        number=randint(30,600)
        #print(number)
        await asyncio.sleep(number)
        if jumpscareBool == True and discord.utils.get(bot.voice_clients, guild = guild) != None:
                #print("boom time")
                selfPlay("boom")


def selfPlay(song):
    vc = discord.utils.get(bot.voice_clients, guild = guild)
    if vc.is_paused():
        vc.resume()
    else:
        vc.play(discord.FFmpegPCMAudio(f"Songs/{song}.mp3"))



@bot.tree.command(description = "Toggle the boom noise")
async def boom_toggle(interaction: discord.Interaction):
    global jumpscareBool
    jumpscareBool = not jumpscareBool
    await interaction.response.send_message(f"Jumpscare is now **{jumpscareBool}**")



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
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        print(current_time, f'{member} has left {before.channel}')
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
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        print(current_time,f'{member} has joined {after.channel}')
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



 
@bot.tree.command(description="Rollercoasts a user")
async def rollercoaster(interaction:discord.Interaction, member:discord.Member=None, movetimes:int = 1):
    #Check if no target
    if member == None:
        member = interaction.user
    #if member.id == 238063640601821185:
        #member = interaction.user
    if interaction.user.id == 694382869367226368:
        #if member.id == 288884848012296202:
        member = interaction.user
    initial_channel = member.voice.channel

    if member.voice is None:
        return await interaction.response.send_message("User is not in a channel")
    
    if movetimes < 1:
        return await interaction.response.send_message("Please move at least 1 time")


    coasterUsers.append(member.id)
    #name = member.display_name
    value = randint(0,2)
    await interaction.response.send_message(f"Enjoy the ride <@{member.id}>!!!")
    await interaction.channel.send(f"Coasting {movetimes} times",)
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

@bot.tree.command(description = "Keep someone out of a voice channel")
async def ban(interaction:discord.Interaction, member:discord.Member=None, bantime:int=10, channel:discord.VoiceChannel=None):
    if member.id in bannedMembers:
        return await interaction.response.send_message(f"{member} is already banned LOL")
    if member == None:
        member = guild.get_member(694382869367226368)
    if channel == None:
        channel = interaction.user.voice.channel
    if member.voice.channel == channel:
        await member.move_to(None, reason="Timed out")
    newBan = Banned(bot, member, channel, bantime)
    bannedMembers.append(member.id)
    bans.append(newBan)


    
#Send a private dm to a person
@bot.tree.command(description="Send's an annonymous dm to a user")
async def send_dm(interaction: discord.Interaction, user:discord.Member, *, message: str):
    #Hide your message
    #Creates a private dm
    channel = await user.create_dm()
    #Send's dm to user
    await channel.send(message)
    return await interaction.response.send_message("Sent message!", ephemeral=True)

def get_songs():
    songs = []
    sound_list = os.listdir("Songs")
    for i, x in enumerate(sound_list):
        x = x.replace(".mp3", "")
        songs.append(x)
    return songs


@bot.tree.command(description="Lists playable sounds")
async def songs(interaction:discord.Interaction):
    return await interaction.response.send_message(f"{get_songs()}", ephemeral=True)

@bot.tree.command(description="Plays audio from bot")
async def play(interaction:discord.Interaction, song:str = None):
    if song is not None:
        song = song.lower()
    if song not in get_songs() and song is not None:
        return await interaction.response.send_message(f"Not a valid song!\n Choose from\n {get_songs()}")
    vc = discord.utils.get(bot.voice_clients, guild = guild)
    if vc is None:
        print(dir(interaction.user.voice))
        current_vc = interaction.user.voice.channel
        await current_vc.connect()
    vc = discord.utils.get(bot.voice_clients, guild = guild)
    if vc.is_paused():
        vc.resume()
        return await interaction.response.send_message("Resuming")
    elif song is None:
        return await interaction.response.send_message(f"Not a valid song!\n Choose from\n {get_songs()}")
    else:
        vc.play(discord.FFmpegPCMAudio(f"Songs/{song}.mp3"))
    return await interaction.response.send_message(f"Playing {song}")

@bot.tree.command(description="Pauses the audio from bot")
async def pause(interaction:discord.Interaction):
    voice = discord.utils.get(bot.voice_clients, guild = guild)
    if voice is None:
        return await interaction.response.send_message("Murder Bot is not connected")
    if voice.is_playing():
        voice.pause()
        return await interaction.response.send_message("Paused audio")
    else:
        return await interaction.response.send_message("Currently no audio is playing")

@bot.tree.command(description="Stops the audio from bot")
async def stop(interaction:discord.Interaction):
    voice = discord.utils.get(bot.voice_clients, guild = guild)
    if voice is None:
        return await interaction.response.send_message("Murder Bot is not connected")
    voice.stop()

    return await interaction.response.send_message("Stopped audio")

snipe_message_author = {}
snipe_message_content = {}

@bot.event
async def on_message_delete(message):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print(current_time, f"A message was deleted in channel {message.channel}")
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


@bot.tree.command(description="Snipes the last deleted message")
async def snipe(interaction:discord.Interaction, channel:discord.TextChannel=None):
    if channel == None:
        channel = interaction.channel
    try: #This piece of code is run if the bot finds anything in the dictionary
        for index, value in enumerate(snipe_message_content[channel.id]):
            em = discord.Embed(title = f"Deleted message in #{channel.name}", description = value)
            em.set_footer(text = f"This message was sent by {snipe_message_author[channel.id][index].name}")
            return await interaction.response.send_message(embed = em)
    except KeyError: #This piece of code is run if the bot doesn't find anything in the dictionary
        await interaction.response.send_message(f"There are no recently deleted messages in #{channel.name}")

@bot.tree.command(description="Clears the snipe log")
async def snipe_clear(interaction:discord.Interaction):
    snipe_message_author.clear()
    snipe_message_content.clear()
    return await interaction.response.send_message("Cleared snipe log")

@bot.tree.command(description="Deletes a user's messages in a given channel (testing purposes ONLY)")
async def delete_messages(interaction:discord.Interaction, member:discord.Member, limit:int, channel:discord.TextChannel=None):
    if channel == None:
        channel = interaction.channel
    if interaction.user.id != 238063640601821185:
        return await interaction.response.send_message("You do not have access to this command")
    counter = 0
    msgs = []
    extra = 0
    if interaction.user.id == member.id:
        extra = 1
    #flatten no longer works
    for msg in await channel.history().flatten():
        if msg.author.id == member.id:
            msgs.append(msg)
            counter += 1
        if counter == limit+extra:
            break
    await channel.delete_messages(msgs)
    return await interaction.response.send_message("Deleted messages")

    
    #await message.delete()

#Changes status of the discord bot
@bot.tree.command(description="Changes status of the bot")
async def change_status(interaction:discord.Interaction, newstatus:discord.Status): 
    #Changes the status of the bot
    await bot.change_presence(status=newstatus)
    #Notifies user of status change 
    await interaction.response.send_message(f"Status successfully changed to {newstatus}")


#Pull's user's profile picture
@bot.tree.command(description="Pulls user's profile picture")
async def pfp(interaction:discord.Interaction, member:discord.User = None):
    #If no member is specified, it will pull the profile picture of the user who sent the command
    if member == None:
        member:discord.Member = interaction.user
    #Sends the profile picture of the member
    if member.avatar is None:
        return await interaction.response.send_message("This user does not have a profile picture", ephemeral=True)
    return await interaction.response.send_message(member.avatar, ephemeral=True)

@bot.tree.command(description="Create a custom emoji")
async def create_emoji(interaction:discord.Interaction, name:str, link:str=None, circular:bool=False):
    await interaction.response.defer(ephemeral=True, thinking=True)
    if link is None:
        response = get(interaction.user.avatar)
    else:
        response = get(link)

    image = Image.open(BytesIO(response.content))
    image = image.convert("RGBA")
    # Resize and compress the image
    max_size = (128, 128)  # Adjust the maximum size as needed
    image.thumbnail(max_size, Image.ANTIALIAS)

    if circular:
        # Create a circular mask
        mask = Image.new("L", image.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0) + image.size, fill=255)

        # Apply the mask and crop the image
        masked_image = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
        image = Image.composite(masked_image, Image.new("RGBA", mask.size), mask)

    image_buffer = BytesIO()
    image.save(image_buffer, format="PNG")  # Save the image to the buffer
    image_buffer.seek(0)
        
    await interaction.guild.create_custom_emoji(name=name, image=image_buffer.read())
    return await interaction.edit_original_response(content=f"Created emoji {name}")

@bot.tree.command(description="Delete a custom emoji")
async def delete_emoji(interaction:discord.Interaction, name:str):
    emojis = [emoji for emoji in guild.emojis if name.lower() in emoji.name.lower()]
    await interaction.response.defer(ephemeral=True, thinking=True)
    if not emojis:
        await interaction.edit_original_response(content=f"No emojis found containing the substring '{name}'.")
    else:
        deleted_emojis = []
        for emoji in emojis:
            await emoji.delete()
            deleted_emojis.append(emoji.name)
    return await interaction.edit_original_response(content=f"Deleted emojis containing the substring '{name}': {' '.join(deleted_emojis)}")

# @bot.tree.command(description="Checks dm's of a user")
# async def check_dms(interaction:discord.Interaction, member:discord.Member):
#     if interaction.user.id != 238063640601821185:
#         return await interaction.response.send_message("You do not have access to this command")
#     if member.dm_channel is None:
#         await member.create_dm()

#     dm = member.dm_channel.history()
#     print([i.content async for i in dm])
#     # do stuff with elem here
#     await interaction.response.send_message(f"DM's of {member.name}#{member.discriminator}:\n{[i.content async for i in dm]}", ephemeral=True)

@bot.command()
async def sync(ctx):
    await bot.tree.sync()

@bot.tree.command(description="Syncs the slash commands")
async def sync(interaction:discord.Interaction):
    await interaction.response.defer(ephemeral=False, thinking=True)
    await bot.tree.sync()
    return await interaction.edit_original_response(content="Synced slash commands")

#Run's the bot
bot.run(token)




