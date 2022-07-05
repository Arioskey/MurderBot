import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot
import asyncio


class Banned(commands.Cog):
    def __init__(self, bot, member, call, banTime, realTime):
        self.member = member
        self.call = call
        self.banTime = banTime
        self.realTime = realTime
        self.bot = bot
        self.guild = self.bot.guilds[0]


    
    def getBanTime(self):
        return self.banTime

    def getCall(self):
        return self.call

    def setRealTime(self, time):
        self.realTime = time
