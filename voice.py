import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ext.commands import Bot
import asyncio

class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild = self.bot.guilds[0]



    @app_commands.command(description="Mutes a person")
    async def mute(self, interaction:discord.Interaction, member:discord.Member=None):
        if member == None:
            member = interaction.user
        if member.voice is None:
            return await interaction.response.send_message("User is not in a channel", ephemeral=True)
        elif member.voice.mute:
            return await interaction.response.send_message("User is already muted!", ephemeral=True)
        await interaction.response.send_message(f"Muted {member.name}")
        vc = discord.utils.get(self.bot.voice_clients, guild = self.guild)
        if vc is None:
            current_vc = interaction.user.voice.channel
            try:
                await current_vc.connect()
            except AttributeError:
                await interaction.channel.send("Murderbot was unable to join")
                return await member.edit(mute = True)
        vc = discord.utils.get(self.bot.voice_clients, guild = self.guild)
        if not vc.is_playing():
            if member.id == 694382869367226368:
                vc.play(discord.FFmpegPCMAudio("Songs/shut.mp3"))
            else:
                vc.play(discord.FFmpegPCMAudio("Songs/silence.mp3"))
        return await member.edit(mute = True)

    @app_commands.command(description="Unmutes a person")
    async def unmute(self, interaction:discord.Interaction, member:discord.Member=None):
        if member == None:
            member = interaction.user
        if member.voice is None:
            return await interaction.response.send_message("User is not in a channel")
        elif not member.voice.mute:
            return await interaction.response.send_message("User is not muted!")
        await interaction.response.send_message(f"Unmuted {member.name}")
        return await member.edit(mute = False)

    @app_commands.command(description="Mutes all")
    async def mute_all(self, interaction:discord.Interaction):
        for i, channel in enumerate(self.guild.voice_channels):
            for member in channel.members:
                await member.edit(mute = True)
        await interaction.response.send_message("Muted all")
        return

    @app_commands.command(description="Unmutes all")
    async def unmute_all(self, interaction:discord.Interaction):

        for i, channel in enumerate(self.guild.voice_channels):
            for member in channel.members:
                await member.edit(mute = False)
        await interaction.response.send_message("Unmuted all")
        return
        
    @app_commands.command(description="Deafens a person")
    async def deafen(self, interaction:discord.Interaction, member:discord.Member=None):
        if member == None:
            member = interaction.user

        if member.voice is None:
            return await interaction.response.send_message("User is not in a channel")
            i
        elif member.voice.deaf:
            return await interaction.response.send_message("User is already deafened!")
        await interaction.response.send_message(f"Deafened {member.name}")
        return await member.edit(deafen = True)

    @app_commands.command(description="Undeafens a person")
    async def undeafen(self, interaction:discord.Interaction, member:discord.Member=None):
        if member == None:
            member = interaction.user

        if member.voice is None:
            return await interaction.response.send_message("User is not in a channel")
        elif not member.voice.deaf:
            return await interaction.response.send_message("User is not deafened!")
        await interaction.response.send_message(f"Undeafened {member.name}")
        return await member.edit(deafen = False)

    @app_commands.command(description="Deafens all")
    async def deafen_all(self, interaction:discord.Interaction):

        for i, channel in enumerate(self.guild.voice_channels):
            for member in channel.members:
                await member.edit(deafen = True)
        await interaction.response.send_message("Deafened all")
        return

    @app_commands.command(description="Undeafens all")
    async def undeafen_all(self, interaction:discord.Interaction):
        for i, channel in enumerate(self.guild.voice_channels):
            for member in channel.members:
                await member.edit(deafen = False)
        await interaction.response.send_message("Undeafened all")
        return

    @app_commands.command(description="Disconnects a user")
    async def disconnect(self, interaction:discord.Interaction, member:discord.Member=None, *, reason:str=None):
        if member == None:
            member = interaction.user

        if member.voice is None:
            return await interaction.response.send_message("User is not in a channel")
        await interaction.response.send_message(f"Disconnected {member.name}")
        await member.move_to(None, reason=reason)
        if reason != None:
            await interaction.response.send_message(f"Reason: {reason}")
        return

    @app_commands.command(description="Disconnects all users")
    async def disconnect_all(self, interaction:discord.Interaction, *, reason:str=None):

        for i, channel in enumerate(self.guild.voice_channels):
            for member in channel.members:
                await member.edit(voice_channel=None, reason=reason)
        await interaction.response.send_message("Disconnected all")
        if reason != None:
            await interaction.response.send_message(f"Reason: {reason}")
        return
    #Bot join VC
    @app_commands.command(description="Make bot join a channel")
    async def join(self, interaction:discord.Interaction, *, channel:discord.VoiceChannel=None):
        vc = discord.utils.get(self.bot.voice_clients, guild=self.guild)
        vc_already = False
        if vc is not None:
            vc_already = True
        #Check if the channel argument is empty
        if channel == None:
            channel = interaction.user.voice.channel
        await interaction.response.send_message("MurderBot connected")
        try:
            if not vc_already:
                await channel.connect()
            else:
                await self.guild.get_member(975378100630216704).move_to(channel)
        except AttributeError:
            await interaction.user.edit(mute=True)
            await interaction.user.edit(mute=False)
            channel = interaction.user.voice.channel
            if not vc_already:
                await channel.connect()
            else:
                await self.guild.get_member(975378100630216704).move_to(channel)

            
        
    
    #Bot leave VC
    @app_commands.command(description="Make bot leave current channel")
    async def leave(self, interaction:discord.Interaction):
        #Get current vc bot is in
        vc = discord.utils.get(self.bot.voice_clients, guild=self.guild)
        #Disconnect bot
        if vc is None:
            return await interaction.response.send_message("MurderBot not connected to a vc")
        await vc.disconnect()
        return await interaction.response.send_message("MurderBot disconnected")

