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
    def __init__(self, bot):
        self.bot = bot
        self.guild = self.bot.guilds[0]

    #TODO: Error handling for invalid inputs (IE Above 54/52 depending on jokers)
    @app_commands.command(description="carddd xMany")
    async def randomcards(self,interaction: discord.Interaction, cardnumber: int, includejokers: bool):
        embedVar = discord.Embed(title = "As many random cards as you like", color=0x00ff00)
        embedVar.add_field(name=f"Here are {cardnumber} random cards", value = "I love many random cards", inline=False)
        randomcards = self.loadRandomCard(cardnumber, includejokers)
        cardimage = self.mergeImages(randomcards)
        finalimage = self.developImage(cardimage)
        embedVar.set_image(url= "attachment://image.png")
        await interaction.response.send_message(embed=embedVar, file = discord.File(fp=finalimage, filename="image.png"))