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

    @commands.command(brief="Pulls latest announcements", aliases=["an"])
    async def announcements(self, ctx):
        if not (canvas := self.checkCanvasUser(ctx)):
            return await ctx.send("User's not registered!")
        
        user = canvas.get_current_user()
        a = user.get_favorite_courses()
        #print(len(list(a)))
        course_ids = []
        for i in a:
            course_ids.append(i.id)

        announcements = canvas.get_announcements([i for i in course_ids])

        announce = {}
        announce_counter = 0
        print(len(list(announcements)))
        for i, c in enumerate(announcements):
            html = c.message
            soup = BeautifulSoup(html, features="html.parser")

            # kill all script and style elements
            for script in soup(["script", "style"]):
                script.extract()    # rip it out

            # get text
            text = soup.get_text()

            # break into lines and remove leading and trailing space on each
            lines = (line.strip() for line in text.splitlines())
            # break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)

            if c._parent_id not in announce:
                announce[c._parent_id] = list()
            if c.read_state == "unread":
                announce_counter += 1
                announce[c._parent_id].append(text)
                c.mark_as_read()

        if announce_counter > 0:
            for key, value in announce.items():
                await ctx.send(f"**{canvas.get_course(key).name}**")
                for i, x in enumerate(value):
                    if len(x) > 1500:
                        await ctx.send(f"```{x[0:1000]}...```")
                    else:
                        await ctx.send(f"```{x}```")
        else:
            await ctx.send("You have no unread announcements.")


        