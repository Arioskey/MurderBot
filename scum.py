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
            self.users:list = []
            self.game_instance = None

        async def displayJoin(self, userlist):
            embedVar = discord.Embed(title="Scum", color=0x00ff00)
            embedVar.add_field(name="Click the button to join", value=f"{userlist}", inline=False)
            embedVar.set_image(url= "attachment://image.png")
            return embedVar

        def startGame(self):
            return 

        class ScumStart(discord.ui.View):
            def __init__(self, game_instance):
                super().__init__(timeout=None)  
                self.game_instance:ScumGame = game_instance
                
                

            @discord.ui.button(label="Join", style=discord.ButtonStyle.success)
            async def joinButton(self, interaction: discord.Interaction, button: discord.ui.Button):
                if str(interaction.user.mention) in self.game_instance.users:
                    await interaction.response.send_message("You are already in the game!", ephemeral=True)
                else:
                    print(self.game_instance.users)
                    self.game_instance.users.append(str(interaction.user.mention))
                    userlist = await self.game_instance.generateUserList(self.game_instance.users)
                    embedVar = await self.game_instance.displayJoin(userlist)
                    print("Users updated")
                    await interaction.response.edit_message(embed=embedVar, view=self)
                await interaction.response.edit_message(view=self)

            @discord.ui.button(label="Leave", style=discord.ButtonStyle.red)
            async def declineButton(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.mention == self.game_instance.users[0]:
                    await interaction.channel.send("Game disbanded! (Host has left)")
                    for child in self.children:
                        child.disabled = True
                    await interaction.response.edit_message(view=self)
                    return 
                elif interaction.user.mention in self.game_instance.users:
                    self.game_instance.users.remove(interaction.user.mention)
                    userlist = await self.game_instance.generateUserList(self.game_instance.users)
                    embedVar = await self.game_instance.displayJoin(userlist)
                    await interaction.response.edit_message(embed=embedVar, view=self)

                else:
                    await interaction.response.send_message("You are not in the game!", ephemeral=True)
            
            @discord.ui.button(label="Start", style=discord.ButtonStyle.blurple)
            async def startButton(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.mention == self.game_instance.users[0]:
                    #if len(self.game_instance.users) < 3:
                        #await interaction.response.send_message("You need at least 3 players to start!", ephemeral=True)
                    #else:
                        await interaction.channel.send("Game started!")
                        for child in self.children:
                            child.disabled = True
                        await interaction.response.edit_message(view=self)
                        await self.game_instance.startGame(self.game_instance.users, interaction)
                else:
                    await interaction.response.send_message("You are not the host!", ephemeral=True)
                
                

    @app_commands.command(description="Play Scum")
    async def scum(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        scum_game:ScumGame = ScumGame(self)
        scum_game.users.append(str(interaction.user.mention))
        userlist = await scum_game.generateUserList(scum_game.users)
        embedVar = await scum_game.displayJoin(userlist) 
        await interaction.channel.send(embed = embedVar, view=scum_game.ScumStart(scum_game))
        await interaction.edit_original_response(content="Game created!")
