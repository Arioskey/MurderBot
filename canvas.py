import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot
from datetime import datetime

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
            
                if announcement._parent_id not in announcements_dict:
                    announcements_dict[announcement._parent_id] = list()
                
                if announcement.read_state == "unread":
                    announce_counter += 1
                    announcements_dict[announcement._parent_id].append(announcement)
                    announcement.mark_as_read()
            # returns list
            return announcements_dict, announce_counter

    @tasks.loop(minutes = 10)
    async def check_announcements(self):
        for key, canvas in self.canvas_instances.items():
            if canvas.notifications == True:
                await self.async_announcement(ctx, canvas, True)


    async def async_announcement(self, ctx, canvas, looped = False):
        announce_info = self.announcement(canvas)
        #print(announce_info)
        if looped:
            channel = await self.guild.get_member(int(key)).create_dm()
        else:
            channel = await ctx.author.create_dm()
        if announce_info[1] > 0:
            for key, announcements in announce_info[0].items():
                await channel.send(f"**{canvas.get_course(key).name}**")
                for i, announcement in enumerate(announcements):
                    html = announcement.message
                    text = self.cleanText(html)

                    embed=discord.Embed(
                    title=f"{announcement.title or 'This announcement has no title'}",
                    url=f"{announcement.html_url or 'https://canvas.auckland.ac.nz'}",
                    description=f"{text[0:500]}",
                    color=0xFF5733) 


                    if announcement.author['display_name'] != None:

                        embed.set_author(
                        name=announcement.author['display_name'],
                        icon_url=announcement.author['avatar_image_url'],
                        url=announcement.author['html_url'] or "https://canvas.auckland.ac.nz"
                        )
                    #if announcement.unread_count != None:
                        # embed.set_footer(
                        #     text=f"This announcement was sent to {announcement.unread_count} people"
                        # )
                    # if announcement.posted_at != None or announcement.created_at != None:
                    #     print('here')
                        
                    #     #time2 = announcement.created_at.replace(tzinfo=None)
                    #     print(time1)
                    #     embed.timestamp = time1 #or time2

                    await channel.send(embed=embed)
        else:
            if looped:
                pass
            else:
                await channel.send("You have no unread announcements.")


    @commands.command(brief="Pulls latest unread announcements", aliases=["an"])
    async def announcements(self, ctx):
        if not (canvas := self.checkCanvasUser(ctx)):
            return await ctx.send("User's not registered!")
        await self.async_announcement(ctx, canvas)

        

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
    async def toggle_read_all_announcements(self, ctx):
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

    
    def calc_time_diff(self, due_date):
        #Remove time zone info
        now: datetime.datetime = datetime.now()
        due_date = due_date.replace(tzinfo=None)
        now = now.replace(tzinfo=None)
        #Get time diff
        time_diff = due_date - now
        time_diff = time_diff.total_seconds()
        return time_diff

    def get_upcoming_assignments_time(self, canvas: CanvasUser, days:int, locked:bool = True) -> dict:
        # Gets the current user from canvas
        user = canvas.get_current_user()
        # Gets the favourite courses of user
        courses = user.get_favorite_courses()
        # Empty course id lists
        # Get course ids and put in list
        assignments = {}
        for course in courses:
            if course not in assignments:
                assignments[course.name] = list()
            
            all_assignments = course.get_assignments()
            for assignment in all_assignments:
                if assignment.locked_for_user == True and not locked:
                    continue
                try:
                    due_date = assignment.due_at_date
                except AttributeError:
                    continue
                seconds = self.calc_time_diff(due_date)
                if seconds > (86400 * days) or seconds < 0:
                    continue
                assignments[course.name].append(assignment)

        return assignments


    @commands.command(brief="Gathers upcoming assignments (up to 7 days)", aliases = ["due"])
    async def get_upcoming_assignments(self, ctx, course:str = "None", days = 7, locked: str = "False"):
        try:
            days = int(course)
            course = None
        except ValueError:
            pass
        if course is not None:
            course = course.lower()
        if course == "all":
            course = None
        if locked == "True" or locked == "true":
            locked = True
        elif locked == "False" or locked == "false":
            locked = False
        else:
            return await ctx.send("Please specify a valid option for the locked parameter")
        if not (canvas := self.checkCanvasUser(ctx)):
            return await ctx.send("User's not registered!")
        upcoming_assignments = self.get_upcoming_assignments_time(canvas, days, locked)

        no_assignments = 0
        await ctx.send("Sending privately...", delete_after=2)
        channel = await ctx.author.create_dm()

        for key, assignments in upcoming_assignments.items():
            if course != None:
                course = course.upper()
                check = key.replace(" ", "")

                if course not in check:
                    no_assignments += 1
                    continue
            if len(assignments) == 0:
                no_assignments += 1
                continue
            

            await channel.send(f"**{key}**")
            for assignment in assignments:
                embed=discord.Embed(
                title=f"{assignment.name}",
                url=f"{assignment.html_url}",
                description=f"This assignment is due at {assignment.due_at_date.strftime('%H:%M:%S, %m/%d/%Y, ')}",
                color=0xFF5733) 
                await channel.send(embed=embed)
        if no_assignments == len(upcoming_assignments):
            await ctx.send(f"You have no upcoming assignments! (for at least {days} days)")
        


            



        