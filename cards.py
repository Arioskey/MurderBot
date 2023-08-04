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
        self.hands = {}
        super(Cards, self).__init__(bot)

    @app_commands.command(description="Play Blackjack")
    async def blackjack(self, interaction: discord.Interaction):
        embedVar = discord.Embed(title="Blackjack", color=0x00ff00)
        embedVar.add_field(name="Dealer's Hand", value="Total value: -", inline=False)
        embedVar.add_field(name="Your Hand", value="Total value: -", inline=False)
        randomcard = self.loadRandomCard()
        embedVar.set_image(url= "attachment://image.png")
        await interaction.response.send_message(embed=embedVar, file = randomcard)

    @app_commands.command(description="carddd xMany")
    async def randomcard(self,interaction: discord.Interaction, cardnumber: int, includejokers: bool):
        if cardnumber < 1:
            await interaction.response.send_message("You need to have at least 1 card")
            return
        if cardnumber > 54 and includejokers:
            await interaction.response.send_message("You can't have more than 54 cards")
            return
        if cardnumber > 52 and not includejokers:
            await interaction.response.send_message("You can't have more than 52 cards without jokers")
            return
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

    @app_commands.command(description="give cards to people")
    async def dealcards(self, interaction: discord.Interaction):

        class ToggleSelectedCard(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)


            @discord.ui.button(label="⬅️", style=discord.ButtonStyle.blurple)
            async def leftButton(item, interaction: discord.Interaction, button: discord.ui.Button):
                handimage = self.mergeImages(self.hands[interaction.user])
                select_image = self.moveSelector(handimage, -1, len(self.hands[interaction.user]))
                finalimage = self.developImage(select_image)
                await interaction.channel.send(embed=embedVar, file = discord.File(fp=finalimage, filename="image.png"), view=item)
                await interaction.response.edit_message(embed=embedVar, view=item)

            @discord.ui.button(label="➡️", style=discord.ButtonStyle.blurple)
            async def rightbutton(item, interaction: discord.Interaction, button: discord.ui.Button):
                handimage = self.mergeImages(self.hands[interaction.user])
                select_image = self.moveSelector(handimage, 1, len(self.hands[interaction.user]))
                finalimage = self.developImage(select_image)
                await interaction.channel.send(embed=embedVar, file = discord.File(fp=finalimage, filename="image.png"), view=item)
                await interaction.response.edit_message(embed=embedVar, view=item)
            
            @discord.ui.button(label="Select card", style=discord.ButtonStyle.green)
            async def selectbutton(item, interaction: discord.Interaction, button: discord.ui.Button):
                selectedCard = self.hands[interaction.user].pop(self.selectorpos)
                handimage = self.mergeImages(self.hands[interaction.user])
                finalimage = self.developImage(handimage)
                await interaction.channel.send(embed=embedVar, file = discord.File(fp=finalimage, filename="image.png"), view=item)


                card = self.developImage(self.mergeImages([selectedCard]))
                select = discord.Embed(title = "Selected card", color=0x00ff00)
                select.add_field(name=f"Look at that card", value = f"Big wow", inline=False)
                select.set_image(url= "attachment://image.png")
                await interaction.channel.send(embed=select, file = discord.File(fp=card, filename="image.png"))
                await interaction.response.edit_message(embed=embedVar, view=item)


        self.loadAllCards()
        players = [interaction.user]
        self.hands = self.dealAllCards(players)
        for player in players:
            handimage = self.mergeImages(self.hands[player])
            cardimage = self.selectorDisplay(handimage)
            finalimage = self.developImage(cardimage)
            embedVar = discord.Embed(title = "Dealt cards", color=0x00ff00)
            embedVar.add_field(name=f"Here are {player}'s cards", value = f"They looking kinda fine", inline=False)
            embedVar.set_image(url= "attachment://image.png")
            await interaction.response.send_message(embed=embedVar, file = discord.File(fp=finalimage, filename="image.png"), view = ToggleSelectedCard())

        