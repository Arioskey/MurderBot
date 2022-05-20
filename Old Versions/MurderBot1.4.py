import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot
from random import seed
from random import randint

import requests
import json
import asyncio
from words import allPhrases

token = 'OTc1Mzc4MTAwNjMwMjE2NzA0.GMnQja.-sXdYIJdBQMY5KH5zkJFpYqG7WFqLe1O7y93SU'
global voice_channels, text_channels, phrases, options, out_of_context, person_id, admins

voice_channels = []
text_channels = []
admins = []

person_id = 694382869367226368 #Rohit

options = allPhrases()
phrases = options[0]
out_of_context = options[1]
    
intents = discord.Intents.all()
client = commands.Bot(command_prefix='.', intents=intents)


def newAdmin(admin:int):
    admins.append(guild.get_member(admin))

@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    await client.wait_until_ready()
    global target_channel, guild
    guild = client.guilds[0]
    checkAdmin()
    
    #Start tasks
    #pingRohit.start()
    #If want to be a task
    nick.start()
    
    target_channel = client.get_channel(975385087677960263)


    for channel in client.get_all_channels():
        if str(type(channel)) == "<class 'discord.channel.VoiceChannel'>":
            voice_channels.append(channel)
        elif str(type(channel)) == "<class 'discord.channel.TextChannel'>":
            text_channels.append(channel)

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
    if message.author == guild.get_member(person_id):
        await message.channel.send(f"{options[random_opt][randoms[random_opt]]}")
    await client.process_commands(message)

@client.command()
async def send(ctx, *, message):
    if ctx.message.author not in admins:
        return
    
    words = message.split()
    channel = words[0]

    if channel not in str(text_channels):
        channel = ctx.channel

    else:
        if all(char.isdigit() for char in channel):
            channel = discord.utils.get(client.get_all_channels(), id=int(channel))
        else:
            channel = discord.utils.get(client.get_all_channels(), name=channel)
        message = message.split(' ', 1)[1]


    await channel.send(message)

#@tasks.loop(seconds = 5)
@client.command()
async def ping(ctx):
    if ctx.message.author not in admins:
        return

    await client.wait_until_ready()
    channel = discord.utils.get(client.get_all_channels(), name="this-chat-was-not-caught-by-the-academic-integrity-bureau-of-the-university-of-auckland")
    #channel = discord.utils.get(client.get_all_channels(), name="sounds")
    member = guild.get_member(person_id)
    if member.status == discord.Status.online:
        await channel.send(f"Hi <@{person_id}>!!")
    else:
        await channel.send(f"Where is <@{person_id}>?")
    

#@tasks.loop(seconds = 0)
@client.command()
async def move(ctx, name=person_id):
    if ctx.message.author not in admins:
        return

    await client.wait_until_ready()
    #channel = discord.utils.get(client.get_all_channels(), name="Noncess")
    member = guild.get_member(name)
    value = randint(0, 2)
    #Move everyone except targetted person
    
    for i in range(len(voice_channels)):
        if f"{name}" in str(voice_channels[i].members):
            for member in voice_channels[i].members:
                if member.id == name:
                    continue
                while value == i:
                    value = randint(0, 2)
                await member.move_to(voice_channels[value])
                

@tasks.loop(seconds = 0)
async def nick():
    member = guild.get_member(person_id)
    member2 = guild.get_member(288884848012296202)
    if member != "ohitaaa the cancelled":
        await member.edit(nick="ohitaaa the cancelled")
    if member2 != "I SUCK HARD":
        await member2.edit(nick="I SUCK HARD")
    

def checkAdmin():
    admins.clear()
    adminRole = discord.utils.get(guild.roles, name="Murderer")
    adminRole2 = discord.utils.get(guild.roles, name="dn")
    for member in guild.members:
        if adminRole in member.roles or adminRole2 in member.roles:
            newAdmin(member.id)
            
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
    


    



 
client.run(token)




