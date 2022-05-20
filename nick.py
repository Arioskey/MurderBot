import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot
import asyncio

global permanent_file, alt_file
permanent_file = "Memory/permanent.txt"
alt_file = "Memory/alt.txt"

class Nick(commands.Cog):
    def __init__(self, bot, lists):
        self.bot = bot
        self.perm_nicknames = lists[0]
        self.alt_nicknames = lists[1]
        self.time = 1
        self.guild = self.bot.guilds[0]

    @commands.Cog.listener()
    async def on_ready(self):
        pass
    
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.id in self.perm_nicknames:
            self.perm_nicknames.remove(before.id)
            await after.edit(nick=before.nick)
            self.perm_nicknames.append(before.id)
            

        bools = [before.id in id for i, id in enumerate(self.alt_nicknames)]
        if True in bools:
            await asyncio.sleep(self.time)
            await after.edit(nick=before.nick)




    def check_nickname(self, user:int, type:str) -> bool:
        if "perm" in type:
            type_nick = self.perm_nicknames
            file = permanent_file
        elif "alt" in type:
            type_nick = self.alt_nicknames
            file = alt_file
        with open(file, "r") as fd:
            lines = fd.readlines()
            for i, line in enumerate(lines):
                if str(user) in line or user in type_nick:
                    return True
            fd.close()
        return False
    
    @commands.command(aliases=["check_p", "check_perm", "checkp", "checkperm"])
    async def check_perm_nick(self, ctx, member:discord.Member) -> bool:
        user = member.id
        if self.check_nickname(user, "permanent"):
            await ctx.send(f"{member.name} does HAVE a permanent nickname!")
            return True
        else:
            await ctx.send(f"{member.name} does NOT HAVE a permanent nickname!")
            return False

    @commands.command(aliases=["clear_p", "clear_perm", "clearp", "clearperm"])
    async def clear_perm_nick(self, ctx, member:discord.Member):
        user = member.id
        if self.check_nickname(user, "permanent"):
            self.perm_nicknames.remove(user)
            await ctx.send(f"Cleared {member.name}'s permanent nickname!")
        else:
            await ctx.send(f"{member.name} does not have a permanent nickname!")
            return
        with open(permanent_file, "r") as fd:
            lines = fd.readlines()
            for i, line in enumerate(lines):
                if str(user) in line:
                    del lines[i]
                    break
            fd.close()
        with open(permanent_file, "w") as fd:
            for line in lines:
                fd.write(line)
            fd.close()

    @commands.command(aliases=["set_p", "set_perm", "setp", "setperm"])
    async def set_perm_nick(self, ctx, member:discord.Member, *, nickname:str):
        user = member.id
        if self.check_nickname(user, "permanent"):
            await ctx.send(f"{member.name} already has a permanent nickname!")
            return
        elif self.check_nickname(user, "alt"):
            await ctx.send(f"{member.name} already has an alternating nickname!")
            return


        with open(permanent_file, "a") as fd:
            fd.write(f"{str(user)}:{nickname}\n")
        fd.close()
        await member.edit(nick = nickname)
        self.perm_nicknames.append(user)
        await ctx.send(f"Changed {member.name}'s nickname!")

        

    @commands.command(aliases=["check_a", "check_alt", "checka", "checkalt"])
    async def check_alt_nick(self, ctx, member:discord.Member):
        user = member.id
        if self.check_nickname(user, "alt"):
            await ctx.send(f"{member.name} does HAVE a alternating nickname!")
            return True
        else:
            await ctx.send(f"{member.name} does NOT HAVE a alternating nickname!")
            return False

    async def set_alt_nick_on_ready(self):
        for i, current_user in enumerate(self.alt_nicknames):
            id = current_user[0]
            nick = current_user[1]
            self.time = int(current_user[2])
            await self.guild.get_member(id).edit(nick=nick)

        

    @commands.command(aliases=["set_a", "set_alt", "seta", "setalt"])
    async def set_alt_nick(self, ctx, member:discord.Member, nick1:str, nick2:str, time:float = 3):
        user = member.id
        self.time = time

        if self.check_nickname(user, "permanent"):
            await ctx.send(f"{member.name} already has a permanent nickname!")
            return
        elif self.check_nickname(user, "alt"):
            await ctx.send(f"{member.name} already has an alternating nickname!")
            return

        if time < 3:
            await ctx.send(f"{time} seconds is too quick! Try something greater than 3!")
            return

        with open(alt_file, "a") as fd:
            fd.write(f"{str(user)}:{nick1} {nick2} {time}\n")
        fd.close()


        await member.edit(nick=nick1)
        self.alt_nicknames.append([user, nick2, self.time])
        await member.edit(nick=nick2)
    
        await ctx.send(f"Changing {member.name}'s nickname!")

    @commands.command(aliases=["clear_a", "clear_alt", "cleara", "clearalt"])
    async def clear_alt_nick(self, ctx, member:discord.Member):
        user = member.id
        if self.check_nickname(user, "alt"):
            index = [(i, id.index(user)) for i, id in enumerate(self.alt_nicknames) if user in id][0][0]
            self.alt_nicknames.pop(index)
            await ctx.send(f"Cleared {member.name}'s alternating nickname!")
        else:
            await ctx.send(f"{member.name} does not have a alternating nickname!")
            return

        with open(alt_file, "r") as fd:
            lines = fd.readlines()
            for i, line in enumerate(lines):
                if str(user) in line:
                    del lines[i]
                    break
            fd.close()
        with open(alt_file, "w") as fd:
            for line in lines:
                fd.write(line)
            fd.close()
        
        