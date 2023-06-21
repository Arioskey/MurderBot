import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ext.commands import Bot
import asyncio
from time import time

from requests import get
from io import BytesIO
from PIL import Image, ImageDraw, ImageOps

class Emoji:
    def __init__(self, name, id):
        self.name = name
        self.id = id

class Games(commands.Cog):
    games = {}
    def __init__(self, bot):
        self.bot = bot
        self.guild = self.bot.guilds[0]


    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.id in self.games and self.finished:
            print("Finished game!")
            game:Connect4Game = self.games[interaction.id]
            await game.cleanup()

    global Connect4Game
    class Connect4Game:
        def __init__(self, game):
            self.game = game
            self.parentInteraction:discord.Interaction = self.game.interaction
            self.reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣"]
            self.channel: discord.TextChannel = self.parentInteraction.channel
            self.board = [["⚫" for _ in range(7)] for _ in range(6)]
            self.turnNo = 1
            self.player1 = self.parentInteraction.user
            self.player2 = None
            self.game_message: discord.Message = None
            self.errorMessage: discord.Message = None
            self.emoji1:Emoji = None
            self.emoji2:Emoji = None
            self.lastInteractionTime = time()


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
        
        async def cleanup(self):
            await self.game_message.delete() #< --- Might not be needed (Save the game in chat history)
            if self.emoji1 is not None:
                await self.parentInteraction.guild.delete_emoji(self.emoji1, reason = "Removed Connect4 emoji")
            if self.emoji2 is not None:
                await self.parentInteraction.guild.delete_emoji(self.emoji2, reason = "Removed Connect4 emoji")
            await self.parentInteraction.delete_original_response() #< --- Might not be needed (Save the game in chat history)
            print("Cleaned up game")
            return True
        
        async def timeout_cleanup(self, custom_id):
            if custom_id in self.game.games:
                game:Connect4Game = self.game.games[custom_id]
                #print(time() - game.lastInteractionTime)
                if time() - game.lastInteractionTime > 300: # OR game has finished (set a flag)
                    print("Removing emojis")
                    await game.cleanup()
                    del self.game.games[custom_id]
                    return True
            return False


        async def timeout_cleanup_task(self, custom_id):
            while True:
                if await self.timeout_cleanup(custom_id):
                    break
                await asyncio.sleep(5)
            print("Task complete")
            return True

            

        async def UpdateBoard(self, reactionIndex, board):
            for i in range(5, -1, -1):
                if board[i][reactionIndex] == '⚫':
                    #Player 1
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
                    if user.id not in [self.game_instance.player1.id, self.game_instance.player2.id, self.game_instance.game.bot.user.id]:
                        await self.game_instance.game_message.remove_reaction(reaction, user)
                    if self.game_instance.reactValid(reaction, user):
                        await self.game_instance.game_message.remove_reaction(reaction, user)
                        await self.game_instance.UpdateBoard(self.game_instance.readReaction(reaction), self.game_instance.board)
                        self.game_instance.lastInteractionTime = time()
            
            async def cleanup(self):
                await self.game_instance.cleanup()

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
                

                #TODO delete custom emojis after game is over



                self.game_instance.player2 = interaction.user
                for child in self.children:
                    child.disabled = True

                self.lastInteractionTime = time()
                self.game_instance.game.finished = False
                self.game_instance.game.games[self.game_instance.parentInteraction.id] = self.game_instance

                await interaction.response.edit_message(view=self)
                self.game_instance.emoji1 = Emoji("player1", await create_emoji(self, "player1", self.game_instance.player1.avatar))
                self.game_instance.emoji2 = Emoji("player2", await create_emoji(self, "player2", self.game_instance.player2.avatar))

                display = self.game_instance.generateDisplay(self.game_instance.board)
                self.game_instance.game_message:discord.Message = await self.game_instance.channel.send(display)
                return await self.game_instance.reactControls()
                

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
        asyncio.create_task(connect4_game.timeout_cleanup_task(interaction.id))
        





        

        
