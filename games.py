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

class Emoji: #Change this later to use the official discord Emoji class
    def __init__(self, name, id):
        self.name = name
        self.id = id

class Games(commands.Cog):
    games = {}
    def __init__(self, bot):
        self.bot:Bot = bot
        self.guild = self.bot.guilds[0]

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction:discord.Reaction, user:discord.User):
        print("Reaction added")
        game_instance:Connect4Game = Games.games.get(reaction.message.id)
        if game_instance.finished or user.id == game_instance.game.bot.user.id:
            return
        print(reaction.message.id)
        print(game_instance.game_message.id)
            # await self.game_instance.game_message.remove_reaction(reaction, user)
            # self.game_instance.errorMessage = await self.game_instance.parentInteraction.channel.send("Please wait before making a move!")
            # return await self.game_instance.errorMessage.delete(delay=2) if self.game_instance.errorMessage else None

        if user.id not in [game_instance.player1.id, game_instance.player2.id, self.bot.user.id]:
            return await game_instance.game_message.remove_reaction(reaction, user)

        if game_instance.reactValid(reaction, user, message = game_instance.game_message.id):
            await game_instance.game_message.remove_reaction(reaction, user)
            await game_instance.update_board(game_instance.readReaction(reaction), game_instance.board)
            game_instance.lastInteractionTime = time.time()
        else:
            await game_instance.game_message.remove_reaction(reaction, user)
            game_instance.errorMessage = await game_instance.channel.send(f"It is not your turn!")
            return await game_instance.errorMessage.delete(delay=2) if game_instance.errorMessage else None

        if await game_instance.check_win_all() and not game_instance.finished:
            game_instance.finished = True
            #Creates new message with the winner
            await game_instance.channel.send(f"{game_instance.player1.mention} won!") if game_instance.turnNo % 2 != 0 else await game_instance.channel.send(f"{game_instance.player2.mention} won!")
            await game_instance.cleanup()
        if game_instance.turnNo == 42:
            game_instance.finished = True
            await game_instance.channel.send("It's a tie!")
            await game_instance.cleanup()

    global Connect4Game
    class Connect4Game:
        def __init__(self, game):
            self.game = game
            self.parentInteraction:discord.Interaction = self.game.interaction
            self.reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣"]
            self.channel: discord.TextChannel = self.parentInteraction.channel
            self.board = [["⚫" for _ in range(7)] for _ in range(6)]
            self.turnNo = 0
            self.player1: discord.User = self.parentInteraction.user
            self.player2: discord.User = None
            self.game_message: discord.Message = None
            self.errorMessage: discord.Message = None
            self.emoji1:Emoji = None
            self.emoji2:Emoji = None
            self.lastInteractionTime = time.time()
            self.lastmove = None
            self.finished = False


        def generateDisplay(self, board) -> Embed:
            randcolor = discord.Color(random.randint(0x000000, 0xFFFFFF))
            embed = Embed(title="Connect 4", color=randcolor)
            embed.add_field(name="Players", value=f"{self.player1.mention} vs {self.player2.mention}")
            progress = "Game in progress" if not self.finished else "Game finished"
            embed.add_field(name="Status", value=progress, inline=False)

            if not self.finished:
                if self.turnNo % 2 == 0:
                    embed.add_field(name="Turn", value=f"It's <@{self.player1.id}>'s turn", inline=False)
                else:
                    embed.add_field(name="Turn", value=f"It's <@{self.player2.id}>'s turn", inline=False)

            for row in board:
                row_str = ""
                for col in row:
                    row_str += col + "   "
                embed.add_field(name="\u200b", value=row_str, inline=False)
            current_time = datetime.now()  # Get current date and time
            embed.add_field(name="\u200b", value=f"Last Updated: <t:{int(current_time.timestamp())}:F>")
            if self.finished:
                # duration = datetime.now() - self.game_message.created_at.replace(tzinfo=None)  # Calculate the game duration
                # embed.add_field(name="Game Duration", value=f"<t:{int(duration.total_seconds())}:R>", inline=False)
                pass

            return embed


        async def reactControls(self):
            for _, item in enumerate(self.reactions):
                await self.game_message.add_reaction(item)

        def reactValid(self, reaction, user, message):
            if self.turnNo % 2 == 0:
                return user == self.player1 and str(reaction.emoji) in self.reactions and message == self.game_message.id
            else:
                return user == self.player2 and str(reaction.emoji) in self.reactions and message == self.game_message.id

        def readReaction(self, reaction):
            return self.reactions.index(str(reaction.emoji))
        
        async def cleanup(self):
            embed = self.generateDisplay(self.board)
            await self.game_message.edit(embed=embed)
            await asyncio.sleep(2)
            if self.emoji1 is not None:
                await self.parentInteraction.guild.delete_emoji(self.emoji1, reason = "Removed Connect4 emoji")
            if self.emoji2 is not None:
                await self.parentInteraction.guild.delete_emoji(self.emoji2, reason = "Removed Connect4 emoji")
            
            print("Cleaned up game")
            if self.game_message.id in Games.games:
                game:Connect4Game = Games.games[self.game_message.id]
                #print(time() - game.lastInteractionTime)
                if time.time() - game.lastInteractionTime > 300: # OR game has finished (set a flag)
                    print("Removing emojis")
                    del Games.games[self.game_message.id]
                    return True
        
        async def timeout_cleanup(self, custom_id):
            # print(Games.games)
            if custom_id in Games.games:
                game:Connect4Game = Games.games[custom_id]
                #print(time() - game.lastInteractionTime)
                if time.time() - game.lastInteractionTime > 300: # OR game has finished (set a flag)
                    print("Removing emojis")
                    await game.cleanup()
                    del Games.games[custom_id]
                    return True
            return False

        async def timeout_cleanup_task(self, custom_id):
            while True:
                if await self.timeout_cleanup(custom_id):
                    break
                await asyncio.sleep(5)
            print("Task complete")
            return True

        async def update_board(self, reactionIndex, board):
            for i in range(5, -1, -1):
                if board[i][reactionIndex] == '⚫':
                    # Player 1
                    if self.turnNo % 2 == 0:
                        if self.emoji1 is not None:
                            board[i][reactionIndex] = f'<:{self.emoji1.name}:{self.emoji1.id}>'
                        else:
                            board[i][reactionIndex] = '🔴'
                    else:
                        if self.emoji2 is not None:
                            board[i][reactionIndex] = f'<:{self.emoji2.name}:{self.emoji2.id}>'
                        else:
                            board[i][reactionIndex] = '🟡'
                    self.lastmove = (i, reactionIndex)
                    self.turnNo += 1
                    break
                elif i == 0:
                    self.errorMessage = await self.channel.send("Column is full! Do another move")
                    break

            embed = self.generateDisplay(board)
            await self.game_message.edit(embed=embed)
            await self.errorMessage.delete(delay=3) if self.errorMessage else None


        async def check_win_all(self):
            #check horizontal that includes last move
            if await self.check_win(0, 1):
                return True
            #check vertical that includes last move
            if await self.check_win(1, 0):
                return True
            #check diagonals that includes last move
            if await self.check_win(1, 1):
                return True
            #check other diagonal that includes last move
            if await self.check_win(1, -1):
                return True
            return False
        
        async def check_win(self, row_change, col_change):
            if self.lastmove is None:
                return False
            row = self.lastmove[0]
            col = self.lastmove[1]
            count = 1
            #check left
            while col - col_change >= 0 and row - row_change >= 0 and self.board[row][col] == self.board[row - row_change][col - col_change]:
                count += 1
                col -= col_change
                row -= row_change
            #check right
            row = self.lastmove[0]
            col = self.lastmove[1]
            while col + col_change < 7 and row + row_change < 6 and self.board[row][col] == self.board[row + row_change][col + col_change]:
                count += 1
                col += col_change
                row += row_change
            if count >= 4:
                return True
            return False


        class Connect4View(discord.ui.View):
            def __init__(self, game_instance):
                super().__init__(timeout=None)
                self.game_instance:Connect4Game = game_instance
                


            @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
            async def acceptButton(self, interaction: discord.Interaction, button: discord.ui.Button):

                async def create_emoji(self, name:str, link:str) -> int:
                    response = get(link)

                    image = Image.open(BytesIO(response.content))
                    image = image.convert("RGBA")
                    # Resize and compress the image
                    max_size = (128, 128)  # Adjust the maximum size as needed
                    image.thumbnail(max_size, Image.ANTIALIAS)


                    # Create a circular mask
                    mask = Image.new("L", image.size, 0)
                    mask_draw = ImageDraw.Draw(mask)
                    mask_draw.ellipse((0, 0) + image.size, fill=255)

                    # Apply the mask and crop the image
                    masked_image = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
                    image = Image.composite(masked_image, Image.new("RGBA", mask.size), mask)

                    image_buffer = BytesIO()
                    image.save(image_buffer, format="PNG")  # Save the image to the buffer
                    image_buffer.seek(0)
                        
                    emoji = await interaction.guild.create_custom_emoji(name=name, image=image_buffer.read())
                    return emoji.id
                
                #If user is already player 1 don't do anything
                #if self.game_instance.player1 != interaction.user:
                self.game_instance.player2 = interaction.user
                for child in self.children:
                    child.disabled = True

                self.lastInteractionTime = time.time()
                self.game_instance.game.finished = False
    

                await interaction.response.edit_message(view=self)
                self.game_instance.emoji1 = Emoji("player1", await create_emoji(self, "player1", self.game_instance.player1.avatar))
                self.game_instance.emoji2 = Emoji("player2", await create_emoji(self, "player2", self.game_instance.player2.avatar))

                display = self.game_instance.generateDisplay(self.game_instance.board)
                self.game_instance.game_message: discord.Message = await self.game_instance.channel.send(embed=display)
                Games.games[self.game_instance.game_message.id] = self.game_instance
                return await self.game_instance.reactControls()
                
                #else:
                    #await interaction.response.send_message("You are already player 1!", ephemeral=True)
  

            @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
            async def declineButton(self, interaction: discord.Interaction, button: discord.ui.Button):
                for child in self.children:
                    child.disabled = True
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
        # Schedule timeout cleanup after 10 seconds
        #this no longer works as we no do not use interaciton id anymore
        asyncio.create_task(connect4_game.timeout_cleanup_task(interaction.id))
        





        

        
