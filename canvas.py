import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot

from canvasapi import Canvas
from canvasapi.exceptions import InvalidAccessToken, ResourceDoesNotExist, Forbidden
from bs4 import BeautifulSoup

import asyncio
import time

API_URL = "https://auckland.instructure.com/"

class CanvasUser(Canvas):
    def __init__(self, base_url, access_token):
        super().__init__(base_url, access_token)
        #By default turn off announcement notifications
        self.notifications = False

class CanvasCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild = self.bot.guilds[0]
        tokens = open(".git/canvas token.txt","r").readlines()
        self.canvas_instances = {
            "238063640601821185": CanvasUser(API_URL,tokens[0]), #aaron
            "288884848012296202": CanvasUser(API_URL,tokens[1]) #elise
            }
        self.check_announcements.start()

    def checkCanvasUser(self, ctx):
        for key, value in self.canvas_instances.items():
            if key == str(ctx.author.id):
                return value
        return False
    
    @commands.command(brief="Register user temporarily")
    async def login(self, ctx, token:str):

        if not isinstance(ctx.channel, discord.channel.DMChannel):
            await ctx.message.delete()
        if isinstance(self.checkCanvasUser(ctx), CanvasUser):
            if isinstance(ctx.channel, discord.channel.DMChannel):
                channel = await ctx.author.create_dm()
                return await channel.send("You already have registered")
            else:
                return await ctx.send("User already registered")

        newUser = CanvasUser(API_URL, token)

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

    def cleanText(self, text):
        soup = BeautifulSoup(text, features="html.parser")

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
        
        return text

    def get_announcements(self, canvas: CanvasUser):
        # Gets the current user from canvas
        user = canvas.get_current_user()
        # Gets the favourite courses of user
        courses = user.get_favorite_courses()
        # Empty course id lists
        course_ids = []
        # Get course ids and put in list
        for i in courses:
            course_ids.append(i.id)

        announcements = canvas.get_announcements([i for i in course_ids])
        return announcements

    #Announcement function
    def announcement(self, canvas: CanvasUser) -> list:
            announcements = self.get_announcements(canvas)
            
            announcements_dict = {}
            announce_counter = 0

            for i, announcement in enumerate(announcements):
                # Gets message in HTML format

                html = announcement.message
                text = self.cleanText(html)
                if announcement._parent_id not in announcements_dict:
                    announcements_dict[announcement._parent_id] = list()
                
                if announcement.read_state == "unread":
                    announce_counter += 1
                    announcements_dict[announcement._parent_id].append(text)
                    announcement.mark_as_read()
            # returns list
            return announcements_dict, announce_counter

    @tasks.loop(minutes = 10)
    async def check_announcements(self):
        for key, canvas in self.canvas_instances.items():
            if canvas.notifications == True:
                announce_info = self.announcement(canvas)
                channel = await self.guild.get_member(int(key)).create_dm()
                if announce_info[1] > 0:
                    for key, value in announce_info[0].items():
                        await channel.send(f"**{canvas.get_course(key).name}**")
                        for i, text in enumerate(value):
                            if len(text) > 1500:
                                await channel.send(f"```{text[0:1000]}...```")
                            else:
                                await channel.send(f"```{text}```")
                else:
                    pass
                    #await channel.send("You have no unread announcements.")

    @commands.command(brief="Pulls latest unread announcements", aliases=["an"])
    async def announcements(self, ctx):
        if not (canvas := self.checkCanvasUser(ctx)):
            return await ctx.send("User's not registered!")

        announce_info = self.announcement(canvas)
        if announce_info[1] > 0:
            for key, value in announce_info[0].items():
                await ctx.send(f"**{canvas.get_course(key).name}**")
                for i, text in enumerate(value):
                    if len(text) > 1500:
                        await ctx.send(f"```{text[0:1000]}...```")
                    else:
                        await ctx.send(f"```{text}```")
        else:
            await ctx.send("You have no unread announcements.")

    @commands.command(brief="Toggles Canvas Announcements Discord Notifications", aliases=["togglea", "toggle_a"])
    async def toggle_anouncements(self, ctx):
        if not (canvas := self.checkCanvasUser(ctx)):
            return await ctx.send("User's not registered!")
        if canvas.notifications == False:
            canvas.notifications = True
            return await ctx.send("Turning on Canvas Announcement Notifications")
        else:
            canvas.notifications = False
            return await ctx.send("Turning off Canvas Announcement Notifications")

    @commands.command(brief="Read/unread announcements", aliases = ["toggleran"])
    async def toggle_all_announcements(self, ctx):
        if not (canvas := self.checkCanvasUser(ctx)):
            return await ctx.send("User's not registered!")
        announcements = self.get_announcements(canvas)
        all_read = []
        for i, announcement in enumerate(announcements):
            all_read.append(announcement.read_state)
        #There is an unread announcement
        if any("unread" in read_check for read_check in all_read):
            for i, announcement in enumerate(announcements):
                announcement.mark_as_read()
            return await ctx.send("Read all announcements!")
        else:
            for i, announcement in enumerate(announcements):
                announcement.mark_as_unread()
            return await ctx.send("Unread all announcements!")

            



        