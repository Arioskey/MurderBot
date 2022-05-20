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
global voice_channels, text_channels, phrases, options, out_of_context, person_id
voice_channels = []
text_channels = []

person_id = 694382869367226368 #Rohit

options = allPhrases()
phrases = options[0]
out_of_context = options[1]
    
intents = discord.Intents.all()
client = commands.Bot(command_prefix='.', intents=intents)



@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    await client.wait_until_ready()
    #Start tasks
    pingRohit.start()
    update_status.start()
    global target_channel
    target_channel = client.get_channel(975385087677960263)

    
    for channel in client.get_all_channels():
        if str(type(channel)) == "<class 'discord.channel.VoiceChannel'>":
            voice_channels.append(channel)
        elif str(type(channel)) == "<class 'discord.channel.TextChannel'>":
            text_channels.append(channel)

@client.event
async def on_message(message):
    random_opt = randint(0,1)
    random1 = randint(0, len(phrases)-1)
    random2 = randint(0, len(out_of_context)-1)
    randoms = [random1, random2]
    if message.author == client.guilds[0].get_member(person_id):
        await message.channel.send(f"{options[random_opt][randoms[random_opt]]}")
    await client.process_commands(message)

@client.command()
async def send(ctx, *, message):
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
    member = client.guilds[0].get_member(238063640601821185)#aaron
    member2 = client.guilds[0].get_member(554096891500036138)#leon
    if ctx.message.author == member or ctx.message.author == member2:
        await channel.send(message)

@tasks.loop(seconds = 100)
async def pingRohit():
    await client.wait_until_ready()
    #channel = discord.utils.get(client.get_all_channels(), name="this-chat-was-not-caught-by-the-academic-integrity-bureau-of-the-university-of-auckland")
    channel = discord.utils.get(client.get_all_channels(), name="sounds")
    

@tasks.loop(seconds = 0)
async def update_status():
    await client.wait_until_ready()
    #channel = discord.utils.get(client.get_all_channels(), name="Noncess")
    member = client.guilds[0].get_member(person_id)
    value = randint(0, 2)
    #Move everyone except targetted person
    for i in range(len(voice_channels)):
        if f"{person_id}" in str(voice_channels[i].members):
            for member in voice_channels[i].members:
                if member.id == person_id:
                    continue
                while value == i:
                    value = randint(0, 2)
                await member.move_to(voice_channels[value])
                

    if member != "ohitaaa the cancelled":
        await member.edit(nick="ohitaaa the cancelled")


    



 
client.run(token)




