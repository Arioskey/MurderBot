import discord
from discord import app_commands, Embed
from discord.ext import commands, tasks
from discord.utils import format_dt
from discord.ext.commands import Bot
import asyncio
import time
import random
from datetime import datetime

from requests import get
from io import BytesIO
from PIL import Image, ImageDraw, ImageOps
from games import Games


class Cards(Games):
    #def __init__(self, bot):
        #self.bot = bot
        #self.guild = self.bot.guilds[0]
        #self.allcards = []
        #self.customvalues = {}

    #TODO: Error handling for invalid inputs (IE Above 54/52 depending on jokers)
    @app_commands.command(description="carddd xMany")
    async def randomcards(self,interaction: discord.Interaction, cardnumber: int, includejokers: bool):
        self.loadAllCards()
        randomcards = self.loadRandomCard(cardnumber, includejokers)
        total = self.totalCards(randomcards)
        cardimage = self.mergeImages(randomcards)
        finalimage = self.developImage(cardimage)

        #Adds and sends embed
        embedVar = discord.Embed(title = "Random cards", color=0x00ff00)
        embedVar.add_field(name=f"Here are {cardnumber} random cards", value = f"They add to {total} (incase you wonder)", inline=False)
        embedVar.set_image(url= "attachment://image.png")
        await interaction.response.send_message(embed=embedVar, file = discord.File(fp=finalimage, filename="image.png"))