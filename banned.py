import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot
import asyncio
import time


class Banned(commands.Cog):
    def __init__(self, bot, member, channel, banTime):
        self.member = member
        self.channel = channel
        self.banTime = banTime
        self.realTime = time.time()
        self.bot = bot
        self.guild = self.bot.guilds[0]
    
    def getBanTime(self):
        return self.banTime

    def getChannel(self):
        return self.channel

    def setRealTime(self, time):
        self.realTime = time
