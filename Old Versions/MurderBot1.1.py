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
global channels, phrases, options, out_of_context, person_id
channels = []

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
    for channel in client.get_all_channels():
        if str(type(channel)) == "<class 'discord.channel.VoiceChannel'>":
            channels.append(channel)

@client.event
async def on_message(message):
    random_opt = randint(0,1)
    random1 = randint(0, len(phrases)-1)
    random2 = randint(0, len(out_of_context)-1)
    randoms = [random1, random2]
    if message.author == client.guilds[0].get_member(person_id):
        await message.channel.send(f"{options[random_opt][randoms[random_opt]]}")
    
@tasks.loop(seconds = 0)
async def update_status():
    await client.wait_until_ready()
    #channel = discord.utils.get(client.get_all_channels(), name="Noncess")
    member = client.guilds[0].get_member(person_id)
    value = randint(0, 2)
    #Move everyone except targetted person
    for i in range(len(channels)):
        if f"{person_id}" in str(channels[i].members):
            for member in channels[i].members:
                if member.id == person_id:
                    continue
                while value == i:
                    value = randint(0, 2)
                await member.move_to(channels[value])
                

    if member != "ohitaaa the cancelled":
        await member.edit(nick="ohitaaa the cancelled")



 

update_status.start()
client.run(token)




