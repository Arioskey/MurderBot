import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot
import asyncio

class Voice(commands.Cog):
    def __init__(self, bot, higher_admins):
        self.bot = bot
        self.guild = self.bot.guilds[0]
        self.higher_admins = higher_admins


    @commands.command(brief="Mutes a person", aliases=['silence'])
    async def mute(self, ctx, member:discord.Member=None):
        if member == None:
            member = ctx.author
        if ctx.message.author not in self.higher_admins:
            return await ctx.send("You do not have permission to mute")
        if member.voice is None:
            return await ctx.send("User is not in a channel")
        elif member.voice.mute:
            return await ctx.send("User is already muted!")
        await ctx.send(f"Muted {member.name}")
        vc = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)
        if vc is None:
            current_vc = ctx.author.voice.channel
            await current_vc.connect()
        vc = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)
        if not vc.is_playing():
            if member.id == 694382869367226368:
                vc.play(discord.FFmpegPCMAudio("Songs/shut.mp3"))
            else:
                vc.play(discord.FFmpegPCMAudio("Songs/silence.mp3"))
        return await member.edit(mute = True)

    @commands.command(brief="Unmutes a person", aliases=['unsilence'])
    async def unmute(self, ctx, member:discord.Member=None):
        if member == None:
            member = ctx.author
        if ctx.author not in self.higher_admins:
            return await ctx.send("You do not have permission to unmute")
        if member.voice is None:
            return await ctx.send("User is not in a channel")
        elif not member.voice.mute:
            return await ctx.send("User is not muted!")
        await ctx.send(f"Unmuted {member.name}")
        return await member.edit(mute = False)

    @commands.command(brief="Mutes all", aliases=["muteall", "silenceall", "silence_all"])
    async def mute_all(self, ctx):
        if ctx.author not in self.higher_admins:
            return await ctx.send("You do not have permission to mute all")
        for i, channel in enumerate(self.guild.voice_channels):
            for member in channel.members:
                await member.edit(mute = True)
        await ctx.send("Muted all")
        return

    @commands.command(brief="Unmutes all", aliases=["unmuteall", "unsilenceall", "unsilence_all"])
    async def unmute_all(self, ctx):
        if ctx.author not in self.higher_admins:
            return await ctx.send("You do not have permission to unmute all")
        for i, channel in enumerate(self.guild.voice_channels):
            for member in channel.members:
                await member.edit(mute = False)
        await ctx.send("Unmuted all")
        return
        
    @commands.command(brief="Deafens a person")
    async def deafen(self, ctx, member:discord.Member=None):
        if member == None:
            member = ctx.author
        if ctx.message.author not in self.higher_admins:
            return await ctx.send("You do not have permission to deafen")
        if member.voice is None:
            return await ctx.send("User is not in a channel")
            i
        elif member.voice.deaf:
            return await ctx.send("User is already deafened!")
        await ctx.send(f"Deafened {member.name}")
        return await member.edit(deafen = True)

    @commands.command(brief="Undeafens a person")
    async def undeafen(self, ctx, member:discord.Member=None):
        if member == None:
            member = ctx.author
        if ctx.author not in self.higher_admins:
            return await ctx.send("You do not have permission to undeafen")
        if member.voice is None:
            return await ctx.send("User is not in a channel")
        elif not member.voice.deaf:
            return await ctx.send("User is not deafened!")
        await ctx.send(f"Undeafened {member.name}")
        return await member.edit(deafen = False)

    @commands.command(brief="Deafens all", aliases=["deafenall"])
    async def deafen_all(self, ctx):
        if ctx.author not in self.higher_admins:
            return await ctx.send("You do not have permission to deafen all")
        for i, channel in enumerate(self.guild.voice_channels):
            for member in channel.members:
                await member.edit(deafen = True)
        await ctx.send("Deafened all")
        return

    @commands.command(brief="Undeafens all", aliases=["undeafenall"])
    async def undeafen_all(self, ctx):
        if ctx.author not in self.higher_admins:
            return await ctx.send("You do not have permission to undeafen all")
        for i, channel in enumerate(self.guild.voice_channels):
            for member in channel.members:
                await member.edit(deafen = False)
        await ctx.send("Undeafened all")
        return

    @commands.command(brief="Disconnects a user", aliases=["dc"])
    async def disconnect(self, ctx, member:discord.Member=None, *, reason:str=None):
        if member == None:
            member = ctx.author
        if ctx.message.author not in self.higher_admins:
            return await ctx.send("You do not have permission to disconnect")
        if member.voice is None:
            return await ctx.send("User is not in a channel")
        await ctx.send(f"Disconnected {member.name}")
        await member.move_to(None, reason=reason)
        if reason != None:
            await ctx.send(f"Reason: {reason}")
        return

    @commands.command(brief="Disconnects all users", aliases=["dca", "dc_all", "dc_a", "dcall"])
    async def disconnect_all(self, ctx, *, reason:str=None):
        if ctx.author not in self.higher_admins:
            return await ctx.send("You do not have permission to deafen all")
        for i, channel in enumerate(self.guild.voice_channels):
            for member in channel.members:
                await member.edit(voice_channel=None, reason=reason)
        await ctx.send("Disconnected all")
        if reason != None:
            await ctx.send(f"Reason: {reason}")
        return
    #Bot join VC
    @commands.command(brief="Make bot join a channel")
    async def join(self, ctx, *, channel:str=None):

        #Check if the channel argument is empty
        if channel == None:
            channel = ctx.author.voice.channel
        #Check if their specified channel is valid
        else:
            #Check if the channel argument is valid
            for i, chan in enumerate(self.guild.voice_channels):
                if channel.lower() == str(chan.name).lower():
                    channel = chan
                    break

            if isinstance(channel, discord.VoiceChannel):
                pass
            else: 
                #Tell user they did not put in a correct argument
                await ctx.send("You did not provide a valid voice channel")
        await channel.connect()
    
    #Bot leave VC
    @commands.command(brief="Make bot leave current channel")
    async def leave(self, ctx):
        #Get current vc bot is in
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        #Disconnect bot
        await vc.disconnect()

