from argparse import ArgumentError
import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot
from random import seed
from random import randint
from typing import Optional
import os


import json
import asyncio
from words import allPhrases

token = 'OTc1Mzc4MTAwNjMwMjE2NzA0.GMnQja.-sXdYIJdBQMY5KH5zkJFpYqG7WFqLe1O7y93SU'
global voice_channels, text_channels, phrases, options, out_of_context, admins, perm_nicknames, perm_nicknames_tasks, target

voice_channels = []
text_channels = []
admins = []
perm_nicknames = []
perm_nicknames_tasks = []

target = 694382869367226368


options = allPhrases()
phrases = options[0]
out_of_context = options[1]
    
intents = discord.Intents.all()
client = commands.Bot(command_prefix='.', intents=intents)


def newAdmin(admin:discord.Member):
    admins.append(admin)

@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    await client.wait_until_ready()
    global target_channel, guild
    guild = client.guilds[0]
    checkAdmin()
    

    
    target_channel = client.get_channel(975385087677960263)


    for channel in client.get_all_channels():
        if str(type(channel)) == "<class 'discord.channel.VoiceChannel'>":
            voice_channels.append(channel)
        elif str(type(channel)) == "<class 'discord.channel.TextChannel'>":
            text_channels.append(channel)
    
    with open('MurderBot\permanent.txt') as fd:
        lines = fd.readlines()
        for i, line in enumerate(lines):
            user = line.partition(":")[0]
            nickname = line.partition(":")[2]
            user = int(user)
            member = guild.get_member(user)
            perm_nicknames.append(user)
            perm_nicknames_tasks.append([user, asyncio.create_task(nick(member, nickname))])

    
###########################################################    





@client.command()
async def join(ctx):
    if ctx.message.author not in admins:
        return

    channel = ctx.author.voice.channel
    await channel.connect()

@client.command()
async def leave(ctx):
    if ctx.message.author not in admins:
        return
    await ctx.voice_client.disconnect()

@client.event
async def on_message(message):
    random_opt = randint(0,1)
    random1 = randint(0, len(phrases)-1)
    random2 = randint(0, len(out_of_context)-1)
    randoms = [random1, random2]

    if message.author == guild.get_member(target) and not message.content.startswith("."):
        await message.channel.send(f"{options[random_opt][randoms[random_opt]]}")
    await client.process_commands(message)



@client.command()
async def send(ctx, channel:discord.TextChannel, *, message):

    if ctx.message.author not in admins:
        return
    await channel.send(message)





@client.command()
async def ping(ctx, member:discord.Member, channel:discord.TextChannel=None):
    if channel == None:
        channel = ctx.channel
    if ctx.message.author not in admins:
        return
    await client.wait_until_ready()
    #channel = discord.utils.get(client.get_all_channels(), name="sounds")
    if member.status != discord.Status.offline:
        await channel.send(f"Hi <@{member.id}>!!")
    else:
        await channel.send(f"Where is <@{member.id}>?")

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Unknown Command!")
    if isinstance(error, commands.ChannelNotFound):
        await ctx.send("Channel not Found!")
    if isinstance(error, commands.MemberNotFound):
        await ctx.send("Member not Found!")

    


@client.command()
async def move(ctx, member:discord.Member=None):
    if ctx.message.author not in admins:
        return
    if member == None:
        member = guild.get_member(target) #target
    await client.wait_until_ready()
    #channel = discord.utils.get(client.get_all_channels(), name="Noncess")
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

@client.command()
async def set_perm_nick(ctx, member:discord.Member, *, nickname:str):
    user = member.id
    if check_perm_nickname(user):
        await ctx.send(f"{member.name} already has a permanent nickname!")
        return


    with open('MurderBot\permanent.txt', "a") as fd:
        fd.write(f"{str(user)}:{nickname}\n")
    fd.close()
    perm_nicknames.append(user)
    perm_nicknames_tasks.append([user, asyncio.create_task(nick(member, nickname))])
    await ctx.send(f"Changed {member.name}'s nickname!")

def check_perm_nickname(user:int) -> bool:
    with open('MurderBot\permanent.txt', "r") as fd:
        lines = fd.readlines()
        for i, line in enumerate(lines):
            if str(user) in line and user in perm_nicknames:
                return True
    fd.close()
    return False

@client.command()
async def check_perm_nick(ctx, member:discord.Member) -> bool:
    user = member.id
    if check_perm_nickname(user):
        await ctx.send(f"{member.name} does HAVE a permanent nickname!")
        return True
    else:
        await ctx.send(f"{member.name} does NOT HAVE a permanent nickname!")
        return False

@client.command()
async def clear_perm_nick(ctx, member:discord.Member):
    user = member.id
    if check_perm_nickname(user):
        perm_nicknames_tasks[perm_nicknames.index(user)][1].cancel()
        perm_nicknames.remove(user)
        await ctx.send(f"Cleared {member.name}'s permanent nickname!")
    else:
        await ctx.send(f"{member.name} does not have a permanent nickname!")
        return
    with open('MurderBot\permanent.txt', "r") as fd:
        lines = fd.readlines()
        for i, line in enumerate(lines):
            if str(user) in line:
                del lines[i]
                break
        fd.close()
    with open('MurderBot\permanent.txt', "w") as fd:
        for line in lines:
            fd.write(line)
        fd.close()

async def nick(member:discord.Member, nickname:str):
    while True:
        if member != nickname:
            await member.edit(nick=nickname)
        continue
    

def checkAdmin():
    admins.clear()
    adminRole = discord.utils.get(guild.roles, name="Murderer")
    adminRole2 = discord.utils.get(guild.roles, name="dn")
    for member in guild.members:
        if adminRole in member.roles or adminRole2 in member.roles:
            newAdmin(member)
            
@client.command()
async def check_admins(ctx):
    if ctx.message.author != guild.get_member(238063640601821185):
        return
    await ctx.send("Checking admins...")
    checkAdmin()
    if len(admins) != 0:
        await ctx.send("Found admins:")
        for i, person in enumerate(admins):
            await ctx.send(f"{person.name}")
    else:
        await ctx.send("No admins found!")
    

@client.command()
async def send_dm(ctx, user:discord.Member, *, message: str):
    await ctx.message.delete()
    channel = await user.create_dm()
    await channel.send(message)



    



 
client.run(token)




