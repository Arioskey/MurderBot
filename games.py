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

        reactions = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣"]
        board = [['⚫', ] * 7] * 6
        global turns
        turns = 1

        def generateDisplay(board):
            pBoard = ''
            for row in board:
                for col in row:
                    pBoard += col
                pBoard += '\n'
            return pBoard

        async def reactControls(game):
            for item in reactions:
                await game.add_reaction(item)

        def reactValid(reaction, user):
            return user == interaction.user and str(reaction.emoji) in reactions

        def readReaction(reaction):
            return reactions.index(str(reaction.emoji))
        
        async def UpdateBoard(reactionIndex, board):
            global turns
            count = 0
            for row in reversed(board):
                if row[reactionIndex] == '⚫':
                    if turns % 2 == 0:
                        board[count][reactionIndex] = '🟡'
                    else:
                        board[count][reactionIndex] = '🔴'
                    turns += 1
                count += 1
            generateDisplay(board)
            game = await interaction.channel.send(display)
            await reactControls(game)

        #Initialises board
        display = generateDisplay(board)
        game = await interaction.channel.send(display)
        await reactControls(game)

        while True:
            reaction, user = await self.bot.wait_for("reaction_add", check = reactValid)
            if reactValid:
                await game.remove_reaction(reaction,user)
                await UpdateBoard(readReaction(reaction), board)



        

        
