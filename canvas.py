import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot

from canvasapi import Canvas
from canvasapi.exceptions import InvalidAccessToken, ResourceDoesNotExist, Forbidden
from bs4 import BeautifulSoup

import asyncio
import time

API_URL = "https://auckland.instructure.com/"


class CanvasCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild = self.bot.guilds[0]
        tokens = open(".git/canvas token.txt","r").readlines()
        self.canvas_instances = {
            "238063640601821185": Canvas(API_URL,tokens[0]), #aaron
            "288884848012296202": Canvas(API_URL,tokens[1]) #elise
            }

    def checkCanvasUser(self, ctx):
        for key, value in self.canvas_instances.items():
            if key == str(ctx.author.id):
                return value
        return False
    
    @commands.command(brief="Register user temporarily")
    async def login(self, ctx, token:str):

        if not isinstance(ctx.channel, discord.channel.DMChannel):
            await ctx.message.delete()
        if isinstance(self.checkCanvasUser(ctx), Canvas):
            if isinstance(ctx.channel, discord.channel.DMChannel):
                channel = await ctx.author.create_dm()
                return await channel.send("You already have registered")
            else:
                return await ctx.send("User already registered")

        newUser = Canvas(API_URL, token)

        try:
            newUser.get_course(1)

        except InvalidAccessToken:
            if isinstance(ctx.channel, discord.channel.DMChannel):
                channel = await ctx.author.create_dm()
                return await channel.send("Invalid Access Token!")
            return await ctx.send("Invalid Access Token!")

        except (ResourceDoesNotExist, Forbidden):
            pass
            
        temp_dict = {str(ctx.author.id):newUser}
        self.canvas_instances.update(temp_dict)
        if isinstance(ctx.channel, discord.channel.DMChannel):
            channel = await ctx.author.create_dm()
            return await channel.send("You have successfully registered!")
        return await ctx.send("Successfully registered user!")

        
    @commands.command(brief="Returns person's grades")
    async def grades(self, ctx):
        if not (canvas := self.checkCanvasUser(ctx)):
            return await ctx.send("User's not registered!")

        user = canvas.get_current_user()
        await ctx.send("Sending privately...", delete_after=2)
        enrollments = user.get_enrollments()
        course_ids = []
        channel = await ctx.author.create_dm()
        await channel.send("Loading...")
        grades_string = ""
        for course in enrollments:
            if course.course_id in course_ids:
                continue
            course_ids.append(course.course_id)
            grades_string = f"{grades_string}+ {canvas.get_course(course.course_id).name}: {course.grades.get('final_grade')} \n"
        #Send's dm to user
        await channel.send(f"Grades for **{user.name}**")
        await channel.send(grades_string)
        