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
        await interaction.response.defer(ephemeral=True, thinking=True)
        global game, board, turnNo, channel
        channel = interaction.channel
        reactions = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣"]
        board = [["⚫" for x in range(7)] for y in range(6)]
        turnNo = 1
        player1 = interaction.user
        player2 = None
        

        def generateDisplay(board):
            pBoard = ''
            for row in board:
                print (row)
                for col in row:
                    pBoard += col
                pBoard += '\n'
            return pBoard

        async def reactControls(game: discord.Message):
            for _, item in enumerate(reactions):
                await game.add_reaction(item)


        def reactValid(reaction, user):
            if turnNo % 2 == 0:
                return user == player1 and str(reaction.emoji) in reactions
            else:
                return user == player2 and str(reaction.emoji) in reactions

        def readReaction(reaction):
            return reactions.index(str(reaction.emoji))
        
        async def UpdateBoard(reactionIndex, board):
            global turnNo
            for i in range(5, -1, -1):
                print(f'Board iterate: row number {i} with reaction index {reactionIndex}')
                if (board[i][reactionIndex] == '⚫'):
                    if turnNo % 2 == 0:
                        board[i][reactionIndex] = '🔴'
                    else:
                        board[i][reactionIndex] = '🟡'
                    turnNo += 1
                    break
                elif i == 0:
                    errorMessage = await interaction.channel.send("Column is full! Do another move")
                    break
            display = generateDisplay(board)
            await game.edit(content = display)
            await errorMessage.delete(delay = 3)

        #Challenge user to game
        await interaction.channel.send(f'{interaction.user.mention} has challenged you to a game of Connect4! Do you accept?')  
        await interaction.edit_original_response(content = "Game request sent")

        @self.bot.event
        async def on_reaction_add(reaction, user):
            if reactValid(reaction, user):
                await game.remove_reaction(reaction,user)
                await UpdateBoard(readReaction(reaction), board)
                
        class Connect4View(discord.ui.View):
            def __init__(self, parentInteraction):
                super().__init__(timeout = None)
                self.parentInteraction: discord.Interaction = parentInteraction

            @discord.ui.button(label = "Accept", style = discord.ButtonStyle.success)
            async def acceptButton(self, interaction: discord.Interaction, button: discord.ui.Button):

                player2 = interaction.user
                for child in self.children:
                    child.disabled = True

                await interaction.response.edit_message(view=self)
                
                #Initialises board
                print(f'Player 1: {player1}, Player2: {player2}')
                display = generateDisplay(board)
                game = await self.parentInteraction.channel.send(display)
                await reactControls(game)

            @discord.ui.button(label = "Decline", style = discord.ButtonStyle.red)
            async def declineButton(self, interaction: discord.Interaction, button: discord.ui.Button):
                button.view.disable_all_items()
                await interaction.response.edit_message(view=self)
                return
        
        #Sends message with buttons
        await interaction.channel.send("Click the button to accept or decline", view = Connect4View(interaction))
        




        

        
