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


class Scum(commands.Cog):
    games = {}
    def __init__(self, bot):
        self.bot:Bot = bot
        self.guild = self.bot.guilds[0]

    global ScumGame
    class ScumGame(Games):
        def __init__(self, game):
            self.game = game
            self.allcards = []
            self.customvalues = {}
            self.users:discord.User = []
            self.usersPlaying:discord.User = []
            self.usersFinished:discord.User = []
            self.hands = {}
            self.game_instance = None
            self.currentPlayer:str = None
            self.selectorpos = []
            self.max_cols = 8
            self.game_int: discord.Interaction = None
            self.lastcard:str = None
            self.cardvalues = {}
            
        
        class GameView(discord.ui.View):
            def __init__(self, game_instance):
                super().__init__(timeout=None)
                self.game_instance:ScumGame = game_instance

            @discord.ui.button(label="View Hand", style=discord.ButtonStyle.success)
            async def viewHand(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user not in self.game_instance.users:
                    await interaction.response.send_message("You are not in the game!", ephemeral=True)
                else:
                    await interaction.response.defer(thinking = True, ephemeral=True)
                    if self.game_instance.hands[interaction.user] == None:
                        await interaction.response.edit_message("You have no cards!")
                    else:
                        await self.game_instance.displayToggle(interaction)

            @discord.ui.button(label="Pass", style=discord.ButtonStyle.red)
            async def passRound(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user not in self.game_instance.users:
                    await interaction.response.send_message("You are not in the game!", ephemeral=True)
                elif interaction.user in self.game_instance.usersPlaying:
                    arrayPos = self.game_instance.usersPlaying.index(interaction.user)
                    del self.game_instance.usersPlaying[arrayPos]
                    await interaction.response.send_message(f"{interaction.user.mention} passed turn!", delete_after=3)
                else:
                    await interaction.response.send_message("You have passed!", ephemeral=True, delete_after = 3)
                
                if len(self.game_instance.usersPlaying) <= 1: #everyone has passed except 1 person
                    await interaction.channel.send(f"{self.game_instance.usersPlaying[0].mention} has won the round!", delete_after = 3)
                    await self.game_instance.newRound(interaction)

        class ToggleSelectedCard(discord.ui.View):
            def __init__(self, game_instance, embedVar:discord.Embed):
                super().__init__(timeout=None)
                self.game_instance:ScumGame = game_instance
                self.embedVar = embedVar

            @discord.ui.button(label="⬅️", style=discord.ButtonStyle.blurple)
            async def leftButton(self, interaction: discord.Interaction, button: discord.ui.Button):
                finalimage = self.game_instance.hand_image(interaction.user, -1)
                await interaction.response.edit_message(embed=self.embedVar, attachments = [discord.File(fp=finalimage, filename="image.png")], view=self)
                

            @discord.ui.button(label="➡️", style=discord.ButtonStyle.blurple)
            async def rightbutton(self, interaction: discord.Interaction, button: discord.ui.Button):
                finalimage = self.game_instance.hand_image(interaction.user, 1)
                await interaction.response.edit_message(embed=self.embedVar, attachments = [discord.File(fp=finalimage, filename="image.png")], view=self)
            
            @discord.ui.button(label="Select card", style=discord.ButtonStyle.green)
            async def selectbutton(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user != self.game_instance.currentPlayer:
                    await interaction.response.send_message("It is not your turn!", ephemeral=True)
                elif interaction.user not in self.game_instance.usersPlaying:
                    await interaction.response.send_message("You have passed!", ephemeral=True)
                else:
                    playCard:str = self.game_instance.hands[interaction.user][self.game_instance.selectorpos[self.game_instance.users.index(interaction.user)]]
                    if self.game_instance.lastcard != None and self.game_instance.cardvalues[playCard] < self.game_instance.cardvalues[self.game_instance.lastcard]:
                        await interaction.response.send_message("You cannot play that card!", ephemeral=True)
                    else:
                        #if move is valid play card and update game
                        await self.game_instance.processTurn(interaction, self.embedVar)
                        #Check if player has won
                        if len(self.game_instance.hands[interaction.user]) == 0:
                            self.game_instance.usersFinished.append(interaction.user)
                            self.game_instance.usersPlaying.remove(interaction.user)
                            await interaction.channel.send(f"{interaction.user.mention} has finished!", delete_after = 3)
                            if len(self.game_instance.usersPlaying) == 1:
                                await self.game_instance.terminateGame(interaction, )

        class blank(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)

        async def terminateGame(self, interaction : discord.Interaction):
            await interaction.channel.send(f"The game has finished!", delete_after = 3)
            #Display win list
            embedVar = discord.Embed(title="Scum", color=0x00ff00)
            #Add the user who didnt finish (lol)
            for user in self.users:
                if user not in self.usersFinished:
                    self.usersFinished.append(user)
                    break
            embedVar.add_field(name="Win order:", value=f"{await self.generateUserList(self.usersFinished)}", inline=False)
            embedVar.set_image(url= "https://i.giphy.com/media/ZEILv6a8KBDFq4KhbB/giphy.webp")
            await interaction.channel.send(embed=embedVar, view=self.blank())
            return

        async def displayToggle(self, interaction : discord.Interaction):
            finalimage = self.hand_image(interaction.user, 0)
            embedVar = discord.Embed(title="Your cards:", color=0x00ff00)
            embedVar.set_image(url= "attachment://image.png")
            await interaction.edit_original_response(embed=embedVar, attachments= [discord.File(fp=finalimage, filename="image.png")], view=self.ToggleSelectedCard(self, embedVar))

        async def newRound(self, interaction : discord.Interaction):
            #Reset the board and let the winner start
            self.currentPlayer = self.usersPlaying[0]
            self.usersPlaying = self.users
            self.lastcard = None
            embedVar = await self.roundStartEmbed()
            gamemessage = await interaction.channel.fetch_message(self.game_int.message.id)
            await gamemessage.edit(embed=embedVar, view = self.GameView(self))


        async def roundStartEmbed(self):
            embedVar = discord.Embed(title="Scum", color=0x00ff00)
            embedVar.add_field(name=f"{str(self.currentPlayer)}'s turn", value="Waiting for first card", inline=False)
            embedVar.set_image(url= "https://cdn.dribbble.com/users/97383/screenshots/1926705/media/f634e1062e79ce236070493cd3f81d9b.gif")
            embedVar.add_field(name="Play order:", value  = f"{await self.generateTurnList(self.users, self.currentPlayer)}", inline = False)
            return embedVar  

        async def processTurn(self, interaction : discord.Interaction, embedVar):
            #Remove card and redisplay hand
            selectedCard = self.hands[interaction.user].pop(self.selectorpos[self.users.index(interaction.user)])
            self.lastcard = selectedCard
            if (self.selectorpos[self.users.index(interaction.user)] == len(self.hands[interaction.user])):
                self.selectorpos[self.users.index(interaction.user)] -= 1 
            finalimage = self.hand_image(interaction.user, 0)
            if finalimage == None:
                noCards = discord.Embed(title = "You have no cards!", color=0x00ff00)
                await interaction.response.edit_message(embed = noCards, attachments = [], view = self.blank())
            else:
                await interaction.response.edit_message(embed=embedVar, attachments = [discord.File(fp=finalimage, filename="image.png")], view=self.ToggleSelectedCard(self, embedVar))

            #Update main game
            card = self.card_image([selectedCard])
            self.currentPlayer = await self.findNextPlayer(self.usersPlaying, self.currentPlayer)
            select = discord.Embed(title = "Scum", color=0x00ff00)
            select.add_field(name='\u200b', value = f"{str(self.currentPlayer)}'s turn", inline=False)
            select.add_field(name="Play order:", value  = f"{await self.generateTurnList(self.usersPlaying, self.currentPlayer)}", inline = False)
            select.set_image(url= "attachment://image.png")
            gamemessage = await interaction.channel.fetch_message(self.game_int.message.id)
            await gamemessage.edit(embed=select, attachments = [discord.File(fp=card, filename="image.png")], view=self.GameView(self))

        async def loadGame(self, interaction : discord.Interaction):
            self.game_int = interaction
            self.loadAllCards()
            self.cardvalues = await self.loadCardValues()
            self.hands = self.dealAllCards(self.users)
            self.usersPlaying = self.users
            #Check who has the 3 of clubs
            for user in self.users:
                self.usersPlaying.append(user)
                await self.sortCards(self.hands[user])
                self.selectorpos.append(0)
                if "cardClubs3.png" in self.hands[user]:
                    self.currentPlayer = user

            embedVar = await self.roundStartEmbed()
            gamemessage = await interaction.channel.fetch_message(self.game_int.message.id)
            await gamemessage.edit(embed=embedVar, view = self.GameView(self))

        class ScumStart(discord.ui.View):
            def __init__(self, game_instance):
                super().__init__(timeout=None)  
                self.game_instance:ScumGame = game_instance

            @discord.ui.button(label="Join", style=discord.ButtonStyle.success)
            async def joinButton(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user in self.game_instance.users:
                    await interaction.response.send_message("You are already in the game!", ephemeral=True)
                else:
                    self.game_instance.users.append(interaction.user)
                    embedVar = await self.game_instance.displayusers(self.game_instance.users)
                    await interaction.response.edit_message(embed=embedVar, view=self)

            @discord.ui.button(label="Leave", style=discord.ButtonStyle.red)
            async def declineButton(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user == self.game_instance.users[0]:
                    await interaction.channel.send("Game disbanded! (Host has left)")
                    for child in self.children:
                        child.disabled = True
                    await interaction.response.edit_message(view=self)
                    return 
                elif interaction.user in self.game_instance.users:
                    self.game_instance.users.remove(interaction.user)
                    embedVar = await self.game_instance.displayusers(self.game_instance.users)
                    await interaction.response.edit_message(embed=embedVar, view=self)

                else:
                    await interaction.response.send_message("You are not in the game!", ephemeral=True)
            
            @discord.ui.button(label="Start", style=discord.ButtonStyle.blurple)
            async def startButton(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user == self.game_instance.users[0]:
                    if len(self.game_instance.users) < 3:
                        await interaction.response.send_message("You need at least 3 players to start!", ephemeral=True)
                    else:
                        await interaction.channel.send("Game started!")
                        for child in self.children:
                            child.disabled = True
                        await interaction.response.edit_message(view=self)
                        await self.game_instance.loadGame(interaction)
                else:
                    await interaction.response.send_message("You are not the host!", ephemeral=True)
                     

    @app_commands.command(description="Play Scum")
    async def scum(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking = True, ephemeral=True)
        scum_game:ScumGame = ScumGame(self)
        scum_game.users.append(interaction.user)
        embedVar = await scum_game.displayusers(scum_game.users)
        await interaction.edit_original_response(embed = embedVar, view=scum_game.ScumStart(scum_game))