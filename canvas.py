import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot
from datetime import datetime, timedelta

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
        self.notifications = True
        self.due = True

class CanvasCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild = self.bot.guilds[0]
        tokens = open(".git/canvas token.txt","r").readlines()
        self.canvas_instances = {
            "238063640601821185": CanvasUser(API_URL,tokens[0]), #aaron
            "288884848012296202": CanvasUser(API_URL,tokens[1]) #elise
            }
        #self.check_announcements.start()
        #self.check_assignments.start()

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
        #await ctx.send("Sending privately...", delete_after=2)
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
                await self.async_announcement(None, canvas, True, key)


    async def async_announcement(self, ctx, canvas, looped = False, key = None):
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

        

    @commands.command(brief="Toggles Canvas to Discord Notifications", aliases=["tog"])
    async def toggle(self, ctx, toggleType:str = None):
        if not (canvas := self.checkCanvasUser(ctx)):
            return await ctx.send("User's not registered!")
        if toggleType == None:
            await ctx.send(f"Canvas Announcement Notifications: {canvas.notifications}")
            await ctx.send(f"Upcoming Assignment Notifications: {canvas.due}")
        elif toggleType == "all":
            canvas.notifications = not canvas.notifications
            canvas.due = not canvas.due
            await ctx.send(f"Canvas Announcement Notifications: {canvas.notifications}")
            await ctx.send(f"Upcoming Assignment Notifications: {canvas.due}")
            return
        elif "announce" in toggleType:
            canvas.notifications = not canvas.notifications
            return await ctx.send(f"Canvas Announcement Notifications: {canvas.notifications}")
        elif "assign" in toggleType:
            canvas.due = not canvas.due
            return await ctx.send(f"Upcoming Assignment Notifications: {canvas.due}")


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

    def convert_to_unix_time(self, date: datetime, days: int, hours: int, minutes: int, seconds: int) -> str:
    # Get the end date
        end_date = date + timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

        # Get a tuple of the date attributes
        date_tuple = (end_date.year, end_date.month, end_date.day, end_date.hour, end_date.minute, end_date.second)

        # Convert to unix time
        return f'{int(time.mktime(datetime(*date_tuple).timetuple()))}'

    def get_upcoming_assignments_time(self, canvas: CanvasUser, course, days:int, locked:bool = True) -> dict:
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

    @tasks.loop(minutes = 60)
    async def check_assignments(self):
        for key, canvas in self.canvas_instances.items():
            if canvas.due == True:
                await self.async_assignments(None, self.get_upcoming_assignments_time(canvas, None, 14, True), key, None, 14, True)

    async def async_assignments(self, ctx, upcoming_assignments, key, course, days, looped = False):
        if looped:
            channel = await self.guild.get_member(int(key)).create_dm()
        else:
            channel = await ctx.author.create_dm()

        no_assignments = 0
        #await channel.send("Sending privately...", delete_after=2)


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
            

            #await channel.send(f"**{key}**")

            for assignment in assignments:
                
                due_date = assignment.due_at_date

                complete_by = str(int(time.mktime(due_date.timetuple())) + 43200)


                embed=discord.Embed(
                title=f"{assignment.name or 'This assignment has no name'}",
                url=f"{assignment.html_url or 'https://canvas.auckland.ac.nz'}",
                description=f"**This assignment is due <t:{complete_by}:R> on <t:{complete_by}:F>**\n\nMessages sent about assignment reminders may be delayed or not even be sent at all! *Don't solely rely on this for reminders, this is may be unstable and should serve as a last resort*",
                color=0xFF5733) 
                if key:
                    embed.set_author(
                    name=f"{key or 'Unknown Course'}",
                    #icon_url=assignment.profile['avatar_url'],
                    url=f"{assignment.html_url or 'https://canvas.auckland.ac.nz'}"
                    )
                await channel.send(f"\n**There will be an assignment/quiz due soon:** {assignment.name or ''}\n{assignment.html_url}\n*This __won't__ be updated if the assignment due date is changed.*")

                await channel.send(embed=embed)
        if no_assignments == len(upcoming_assignments):
            await channel.send(f"You have no upcoming assignments! (for at least {days} days)")
            
    @commands.command(brief="Gathers upcoming assignments", aliases = ["due"])
    async def get_upcoming_assignments(self, ctx, course = None, days = 14, locked: str = "False"):
        if days == 14:
            try:
                days = int(course)
                course = None
            except (ValueError, TypeError):
                days = 14
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
        
        await self.async_assignments(ctx, self.get_upcoming_assignments_time(canvas, course, days, locked), None, course, days, False)

        
        


            



        