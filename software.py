from cv2 import split
import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot
from discord import app_commands
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

    async def isReflexive(self, interaction:discord.Interaction, relation:list, set:list, eqv:bool=None):
        reflexive = True
        list = []
        for i, element in enumerate(set):
            check = f"{element}, {element}"
            if check not in relation:
                list.append(f"({check})")
                reflexive = False
        if reflexive:
            if not eqv:
                await interaction.response.send_message("RELATION IS **REFLEXIVE!**")
            return True
        else:
            if not eqv:
                await interaction.response.send_message(f"For the relation to be **reflexive** tuple(s): **{[a for a in list]}** MUST be present")
            return False

    async def isSymmetric(self, interaction:discord.Interaction, relation:list,eqv:bool=None):
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
            if not eqv:
                await interaction.response.send_message("RELATION IS **SYMMETRIC!**")
            return True
        else:
            if not eqv:
                await interaction.response.send_message(f"For the relation to be **symmetric** tuple(s): **{[a for a in list]}** MUST be present")
            return False


    async def isTransitive(self, interaction:discord.Interaction, relation:list, eqv:bool=None):
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
            if not eqv:
                await interaction.response.send_message("RELATION IS **TRANSITIVE!**")
            return True
        else:
            if not eqv:
                await interaction.response.send_message(f"For the relation to be **transitive** tuple(s): **{[a for a in list]}** MUST be present")
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

    async def computeEquivalence(self, interaction:discord.Interaction, relation:list, set:list):
        list = []
        for i, element in enumerate(set):
            if element not in str(list):
                list.append(self.equivalenceClass(element, relation))

        for i, classes in enumerate(list):
            await interaction.channel.send(f"EQUIVALENCE CLASS: **{classes}**")
        
        




    @app_commands.command(description="Check's a relation's properties\n <Relation> <Set>")
    async def check(self, interaction:discord.Interaction, property:str, *, sets:str):
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
        eqv = True
        if property == "r":
            await self.isReflexive(interaction, relation, set)
        
        elif property == "s":
            await self.isSymmetric(interaction, relation)
        elif property == "t":
            await self.isTransitive(interaction, relation)
        elif property == "e":
            ref = await self.isReflexive(interaction, relation, set, eqv)
            sym = await self.isSymmetric(interaction, relation, eqv) 
            tran = await self.isTransitive(interaction, relation, eqv)
            if (ref and sym and tran):
                await interaction.response.send_message("RELATION IS **EQUIVALENT**")
                await self.computeEquivalence(interaction, relation, set)
            else:
                await interaction.response.send_message("RELATION IS **NOT EQUIVALENT**")
        else:
            return await interaction.response.send_message("Unknown property!")


    
        