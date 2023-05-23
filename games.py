import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ext.commands import Bot
import asyncio


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild = self.bot.guilds[0]

    @app_commands.command(description = "Play Connect4 once I actually make this work")
    async def connect4(self, interaction: discord.Interaction):
        def generateDisplay(board):
            pBoard = ''
            for row in board:
                for col in row:
                    pBoard += col
                pBoard += '\n'
            return pBoard

        async def reactControls(game):
            await game.add_reaction("1️⃣")
            await game.add_reaction("2️⃣")
            await game.add_reaction("3️⃣")
            await game.add_reaction("4️⃣")
            await game.add_reaction("5️⃣")
            await game.add_reaction("6️⃣")
            await game.add_reaction("7️⃣")

        def reactValid(reaction, user):
            return user == interaction.user and str(reaction.emoji) in ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣"]
        
        board = [['⚫', ] * 7] * 6
        display = generateDisplay(board)
        game = await interaction.channel.send(display)
        await reactControls(game)

        while True:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=15, check = reactValid)
            if reactValid:
                await game.remove_reaction(reaction,user)

        

        
