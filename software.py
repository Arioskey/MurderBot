from cv2 import split
import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot
import asyncio

global permanent_file, alt_file
permanent_file = "Memory/permanent.txt"
alt_file = "Memory/alt.txt"

class Software(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild = self.bot.guilds[0]

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    async def isReflexive(self, ctx, relation:list, set:list):
        reflexive = True
        list = []
        for i, element in enumerate(set):
            check = f"{element}, {element}"
            if check not in relation:
                list.append(f"({check})")
                reflexive = False
        if reflexive:
            await ctx.send("RELATION IS **REFLEXIVE!**")
            return True
        else:
            await ctx.send(f"For the relation to be **reflexive** tuple(s): **{[a for a in list]}** MUST be present")
            return False
    async def isSymmetric(self, ctx, relation:list):
        symmetric = True
        list = []
        for i, element in enumerate(relation):
            element1 = element.split(",")[0]
            element2 = element.split(",")[1]
            element2 = element2.replace(" ", "")
            if element1 != element2:
                check = f"{element2}, {element1}"

                if check not in relation: 
                    list.append(f"({check})")
                    symmetric = False

        if symmetric:
            await ctx.send("RELATION IS **SYMMETRIC!**")
            return True
        else:
            await ctx.send(f"For the relation to be **symmetric** tuple(s): **{[a for a in list]}** MUST be present")
            return False


    async def isTransitive(self, ctx, relation:list):
        transitive = True
        list = []
        for i, element in enumerate(relation):
            char1 = element.split(",")[0]
            char2 = element.split(",")[1]
            char2 = char2.replace(" ", "")

            if char1 == char2:
                continue

            for i, element2 in enumerate(relation):
                char3 = element2.split(",")[0]
                char4 = element2.split(",")[1]
                char4 = char4.replace(" ", "")
                if (char2 == char3):
                    check = f"{char1}, {char4}"
                    if check not in relation and f"({check})" not in list:
                        list.append(f"({check})")
                        transitive = False
        if transitive:
            await ctx.send("RELATION IS **TRANSITIVE!**")
            return True
        else:
            await ctx.send(f"For the relation to be **transitive** tuple(s): **{[a for a in list]}** MUST be present")
            return False
    
    def equivalenceClass(self, node, relation:list):
        list = []
        for i, relationElement in enumerate(relation):
            char1 = relationElement.split(",")[0]
            char2 = relationElement.split(",")[1]
            char2 = char2.replace(" ", "")

            if node == char1:
                list.append(char2)
        return list

    async def computeEquivalence(self, ctx, relation:list, set:list):
        list = []
        for i, element in enumerate(set):
            if element not in str(list):
                list.append(self.equivalenceClass(element, relation))

        for i, classes in enumerate(list):
            await ctx.send(f"EQUIVALENCE CLASS: **{classes}**")
        
        




    @commands.command(brief="Check's a relation's properties")
    async def check(self, ctx, property:str, *, sets="<Relation>, <Set>"):
        sets = sets.split("}")
        sets[0] = sets[0].replace("{", "")
        sets[1] = sets[1].replace(" {", "")
        sets[1] = sets[1].replace("}", "")
        sets[1] = sets[1].split(",")
        sets.pop(2)
        relation = sets[0]
        set = sets[1]
        relation = relation.replace("(", "")
        relation = relation.split("), ")
        relation[len(relation)-1] = relation[len(relation)-1].replace(")", "")
        if property == "r":
            await self.isReflexive(ctx, relation, set)
        
        elif property == "s":
            await self.isSymmetric(ctx, relation)
        elif property == "t":
            await self.isTransitive(ctx, relation)
        elif property == "e":
            ref = await self.isReflexive(ctx, relation, set)
            sym = await self.isSymmetric(ctx, relation) 
            tran = await self.isTransitive(ctx, relation)
            if (ref & sym & tran):
                await ctx.send("RELATION IS **EQUIVALENT**")
                await self.computeEquivalence(ctx, relation, set)
            else:
                await ctx.send("RELATION IS **NOT EQUIVALENT**")
        await ctx.send("DONE!!!!")


    
        