#Shared commands for all games
import discord
from discord import app_commands, Embed
from discord.ext import commands, tasks
from discord.utils import format_dt
from discord.ext.commands import Bot
import asyncio
import time
import random
import os
from datetime import datetime

from requests import get
from io import BytesIO
from PIL import Image, ImageDraw, ImageOps

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild = self.bot.guilds[0]
        self.allcards = []
        self.customvalues = {}

    #Shared commands for all games
    async def reactControls(self):
        for _, item in enumerate(self.reactions):
            await self.game_message.add_reaction(item)

    def readReaction(self, reaction):
        return self.reactions.index(str(reaction.emoji))

    def reactValid(self, reaction, user, message):
        if self.turnNo % 2 == 0:
            return user == self.player1 and str(reaction.emoji) in self.reactions and message == self.game_message.id
        else:
            return user == self.player2 and str(reaction.emoji) in self.reactions and message == self.game_message.id
    
    def loadAllCards(self):
        self.allcards = os.listdir("playingcards/")
    
    def removeJokers(self):
        self.allcards.remove("cardBlackJoker.png")
        self.allcards.remove("cardRedJoker.png")
    
    def loadRandomCard(self, cardnumber, includeJokers):
        if not includeJokers:
            self.removeJokers()
        cardimages = [None]*cardnumber
        for i in range(cardnumber):
            selectedCard = random.randint(0, len(self.allcards) - 1)
            cardimages[i] = self.allcards.pop(selectedCard)
        return cardimages

    def developImage(self, cardimage):
        image_buffer = BytesIO()
        cardimage.save(image_buffer, format="PNG")  # Save the image to the buffer
        image_buffer.seek(0)
        return image_buffer
    
    #TODO: Make merge look loads better with high numbers of cards
    def mergeImages(self, cards):
        startcard = Image.open("playingcards/"+ cards[0]).convert("RGBA")
        cardsize = startcard.size
        new_image = Image.new('RGBA',(len(cards)*cardsize[0], cardsize[1]), (250,250,250))
        for i, card in enumerate(cards):
            addcard = Image.open("playingcards/"+ cards[i]).convert("RGBA")
            new_image.paste(addcard,(cardsize[0]*i,0))   
        return new_image
    
    def totalCards(self, cards):
        total = 0
        for card in cards:
            if card in self.customvalues:
                total += self.customvalues[card]
            elif card[-5] == "A":
                total += 11
            elif card[-5] == "r":
                total += 0
            elif card[-5] == "K" or card[-5] == "Q" or card[-5] == "J" or card[-5] == "0":
                total += 10
            else:
                total += int(card[-5])
        return total
    
    def assignCardValue(self, card, value):
        if card in os.listdir("playingcards/"):
            self.customvalues[card] = value
        else:
            print("Card not valid")