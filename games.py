import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ext.commands import Bot
import asyncio


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild = self.bot.guilds[0]

    global Connect4Game
    class Connect4Game:
        def __init__(self, game):
            self.game = game
            self.parentInteraction = self.game.interaction
            self.reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣"]
            self.channel: discord.TextChannel = self.parentInteraction.channel
            self.reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣"]
            self.board = [["⚫" for _ in range(7)] for _ in range(6)]
            self.turnNo = 1
            self.player1 = self.parentInteraction.user
            self.player2 = None
            self.game_message: discord.Message = None
            self.errorMessage: discord.Message = None


        def generateDisplay(self, board):
            pBoard = ''
            for row in board:
                for col in row:
                    pBoard += col
                pBoard += '\n'
            return pBoard

        async def reactControls(self):
            for _, item in enumerate(self.reactions):
                await self.game_message.add_reaction(item)

        def reactValid(self, reaction, user):
            if self.turnNo % 2 == 0:
                return user == self.player1 and str(reaction.emoji) in self.reactions
            else:
                return user == self.player2 and str(reaction.emoji) in self.reactions

        def readReaction(self, reaction):
            return self.reactions.index(str(reaction.emoji))

        async def UpdateBoard(self, reactionIndex, board):
            for i in range(5, -1, -1):
                if board[i][reactionIndex] == '⚫':
                    if self.turnNo % 2 == 0:
                        board[i][reactionIndex] = '🔴'
                    else:
                        board[i][reactionIndex] = '🟡'
                    self.turnNo += 1
                    break
                elif i == 0:
                    self.errorMessage = await self.channel.send("Column is full! Do another move")
                    break
            display = self.generateDisplay(board)
            await self.game_message.edit(content=display)
            await self.errorMessage.delete(delay=3) if self.errorMessage else None


        class Connect4View(discord.ui.View):
            def __init__(self, game_instance):
                super().__init__(timeout=None)
                self.game_instance:Connect4Game = game_instance
                



                @self.game_instance.game.bot.event
                async def on_reaction_add(reaction, user):
                    if self.game_instance.reactValid(reaction, user):
                        await self.game_instance.game_message.remove_reaction(reaction, user)
                        await self.game_instance.UpdateBoard(self.game_instance.readReaction(reaction), self.game_instance.board)

            @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
            async def acceptButton(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.game_instance.player2 = interaction.user
                for child in self.children:
                    child.disabled = True

                await interaction.response.edit_message(view=self)

                display = self.game_instance.generateDisplay(self.game_instance.board)
                self.game_instance.game_message:discord.Message = await self.game_instance.channel.send(display)
                await self.game_instance.reactControls()

            @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
            async def declineButton(self, interaction: discord.Interaction, button: discord.ui.Button):
                button.view.disable_all_items()
                await interaction.response.edit_message(view=self)
                return

    def __init__(self, bot):
        self.bot = bot
        self.guild = self.bot.guilds[0]

    @app_commands.command(description="Play Connect4")
    async def connect4(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)

        

        # Challenge user to game
        await interaction.channel.send(f'{interaction.user.mention} has challenged you to a game of Connect4! Do you accept?')
        await interaction.edit_original_response(content="Game request sent")
        self.interaction = interaction
        # Create an instance of the Connect4Game class
        connect4_game:Connect4Game = Connect4Game(self)
        # Sends message with buttons
        await interaction.channel.send("Click the button to accept or decline", view=connect4_game.Connect4View(connect4_game))





        

        
