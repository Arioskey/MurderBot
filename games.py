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
from math import floor
from datetime import datetime
import json

from requests import get
from io import BytesIO
from PIL import Image, ImageDraw, ImageOps

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild = self.bot.guilds[0]
        self.allcards = []
        self.customvalues = {}
        self.max_cols = 8
        self.cardsize = []

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
        self.allcards = os.listdir("playingcards")
    
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
    
    def mergeImages(self, cards):
        if len(cards) == 0:
            return None
        startcard = Image.open("playingcards/"+ cards[0]).convert("RGBA")
        self.cardsize = startcard.size
        new_image = Image.new('RGBA',((self.max_cols)*self.cardsize[0], self.cardsize[1]*(floor((len(cards)-1)/self.max_cols)+1)), (0,0,0,0))
        for i, card in enumerate(cards):
            addcard = Image.open("playingcards/" + cards[i]).convert("RGBA")
            new_image.paste(addcard, [self.cardsize[0]*(i%self.max_cols), self.cardsize[1]*floor((i/self.max_cols))])
        return new_image
    
    async def loadCardValues(self):
        data = open('cards.json')
        return (json.load(data))


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
    
    def dealAllCards(self, players):
        hands = {}
        handsize = floor(54/len(players))
        handExtra = 54%len(players)
        for player in players:
            if handExtra > 0:
                hands[player] = self.loadRandomCard(handsize+1, True)
                handExtra -= 1
            else:
                hands[player] = self.loadRandomCard(handsize, True)
        return hands
        
    async def sortCards(self, hand):
        values = await self.loadCardValues()
        hand.sort(key=lambda x: values[x])
        return hand
    

    def selectorDisplay(self, printimage, selecpos):
        selector = Image.open("images/selector.png").convert("RGBA")
        mainsize = printimage.size
        selector_image = Image.new('RGBA', (mainsize[0], mainsize[1]), (0,0,0,0))
        selector_image.paste(selector, [self.cardsize[0]*(selecpos%self.max_cols), self.cardsize[1]*floor((selecpos/self.max_cols))])
        printimage.paste(selector_image, [0,0], selector_image)
        return printimage

    def moveSelector(self, hand, direction, user):
        length = len(self.hands[user])
        if length == 0:
            return None
        
        self.selectorpos[self.users.index(user)] = self.selectorpos[self.users.index(user)] + direction
        #Wrap around
        if (self.selectorpos[self.users.index(user)] < 0 or (self.selectorpos[self.users.index(user)] + direction) > length):
            self.selectorpos[self.users.index(user)] = self.selectorpos[self.users.index(user)] - (direction*length)

        printimage = self.selectorDisplay(hand, self.selectorpos[self.users.index(user)])
        return printimage
    
    def hand_image(self, user, direction):
        handimage = self.mergeImages(self.hands[user])
        select_image = self.moveSelector(handimage, direction, user)
        if select_image == None:
            return None
        else:
            return (self.developImage(select_image))
    
    def card_image(self, cards):
        cardimage = self.mergeImages(cards)
        return (self.developImage(cardimage))
    
    async def generateUserList(self, userlist):
        users = "Host: "
        for user in userlist:
            users += user.mention + "\n"
        return users

    async def displayusers(self, userlist):
        userlist = await self.generateUserList(userlist)
        embedVar = discord.Embed(title="Scum", color=0x00ff00)
        embedVar.add_field(name="Click the button to join", value=f"{userlist}", inline=False)
        embedVar.set_image(url= "attachment://image.png")
        return embedVar
    
    async def generateTurnList(self, userlist, currentPlayer):
        playerPos = userlist.index(currentPlayer)
        for user in userlist:
            users = userlist[playerPos].mention + "\n"
            playerPos = (playerPos + 1) % len(userlist)
        return users
    
    async def findNextPlayer(self, userlist, currentPlayer):
        nextPlayer = userlist[(userlist.index(currentPlayer) + 1) % len(userlist)]
        return nextPlayer