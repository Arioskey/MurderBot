import discord
from discord import TextChannel, DMChannel, VoiceChannel, Member
from discord.ext import commands, tasks
from discord.ext.commands import Bot
from datetime import datetime, timedelta

import canvasapi
from canvasapi import Canvas
from canvasapi.exceptions import InvalidAccessToken, ResourceDoesNotExist, Forbidden
from bs4 import BeautifulSoup
from typing import Union,TypeVar

Announcement = canvasapi.discussion_topic.DiscussionTopic
Assignment = canvasapi.assignment.Assignment
import asyncio
import time

#URl we use to access Canvas
API_URL = "https://auckland.instructure.com/"

global GLOBAL_DAYS
GLOBAL_DAYS = 14

#Sub Class of Canvas such that we can add our own attributes and methods
class CanvasUser(Canvas):
    def __init__(self, base_url, access_token):
        super().__init__(base_url, access_token)
        #By default turn off announcement notifications
        self.notifications = True
        self.due = True

class CanvasCog(commands.Cog):
    def __init__(self, bot):
        #Get Discord Bot
        self.bot = bot
        #Get Acad server
        self.guild = self.bot.guilds[0]
        #Instantiate Tokens so they do not need to login
        tokens = open(".git/canvas token.txt","r").readlines()
        self.canvas_instances = {
            "238063640601821185": CanvasUser(API_URL,tokens[0]), #aaron
            "288884848012296202": CanvasUser(API_URL,tokens[1]) #elise
            }
        #Start loops to check for announcements and assignments
        #self.check_announcements.start()
       # self.check_assignments.start()

    #Method to check if user is a discord user
    def checkCanvasUser(self, ctx):
        #Loop through current canvas instances
        for key, value in self.canvas_instances.items():
            #Check if the ctx user is in the dict
            if key == str(ctx.author.id):
                #Return the canvas Obj
                return value
        return False
    
    @commands.command(brief="Register user temporarily")
    async def login(self, ctx, token:str):
        #If logging in a public channel remove the login message
        if not isinstance(ctx.channel, discord.channel.DMChannel):
            await ctx.message.delete()
        #Check if user is already registered
        if isinstance(self.checkCanvasUser(ctx), CanvasUser):
            return await ctx.send("User already registered")
        #Create a new CanvasUSer instance for the user
        newUser = CanvasUser(API_URL, token)
        
        #Check if the user's token was valid...
        try:
            newUser.get_course(1)

        except InvalidAccessToken:
            return await ctx.send("Invalid Access Token!")

        except (ResourceDoesNotExist, Forbidden):
            pass
        # Add user into the dictionary
        temp_dict = {str(ctx.author.id):newUser}
        self.canvas_instances.update(temp_dict)
        return await ctx.send("Successfully registered user!")

        
    @commands.command(brief="Returns person's grades")
    async def grades(self, ctx):
        #Check if the user is verified
        if not (canvas := self.checkCanvasUser(ctx)):
            return await ctx.send("User's not registered!")
        #Get their enrollments
        user = canvas.get_current_user()        
        enrollments = user.get_enrollments()
        course_ids = []
        channel = await ctx.author.create_dm()
        await channel.send("Loading...")
        grades_string = ""
        #Loop through their enrollmenets
        for course in enrollments:
            #Skip repeated enrollments (bug)
            if course.course_id in course_ids:
                continue
            #Add the course id to the list
            course_ids.append(course.course_id)
            #Add the grades to the grade string
            grades_string = f"{grades_string}+ {canvas.get_course(course.course_id).name}: {course.grades.get('final_grade')} \n"
        #Send's dm to user about info on their grades
        await channel.send(f"Grades for **{user.name}**")
        await channel.send(grades_string)


    #Function clean up HTML texts
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

    def get_announcements(self, canvas: CanvasUser) -> list[Announcement]:
        # Gets the current user from canvas
        user = canvas.get_current_user()
        # Gets the favourite courses of user
        courses = user.get_favorite_courses()
        # Empty course id lists
        course_ids = []
        # Get course ids and put in list
        for i in courses:
            course_ids.append(i.id)
        # Get the announcements from canvas
        announcements = canvas.get_announcements([i for i in course_ids])
        return announcements

    #Announcement function
    def announcement(self, canvas: CanvasUser) -> list[dict[str, Announcement], int]:
            # Get canvas anouncements
            announcements: list = self.get_announcements(canvas)
            # Initialise an announcement dictionary
            announcements_dict = {}
            # Set announce counter to 0
            announce_counter = 0
            # Loop through announcements
            for _, announcement in enumerate(announcements):
                # Check if the course is in the dict
                if announcement._parent_id not in announcements_dict:
                    #Create an empty list for that course
                    announcements_dict[announcement._parent_id] = list()
                # Check if the announcement is not yet read
                if announcement.read_state == "unread":
                    # Increment the counter
                    announce_counter += 1
                    # Add the announcement to the announcements dict
                    announcements_dict[announcement._parent_id].append(announcement)
                    # Mark the announcement as read via canvas
                    announcement.mark_as_read()
            # returns list
            return announcements_dict, announce_counter

    @tasks.loop(minutes = 10)
    async def check_announcements(self) -> None:
        #Loop through all CanvasUser instances
        for key, canvas in self.canvas_instances.items():
            #Check if they have announcement notifications on
            if canvas.notifications == True:
                await self.async_announcement(None, canvas, True, key)

    # Gets announcements asynchronously
    async def async_announcement(self, ctx, canvas: CanvasUser, looped:bool = False, key:str = None) -> None:
        # Get announcements info
        announce_info = self.announcement(canvas)
        #Create a private dm with user
        channel = await self.guild.get_member(int(key)).create_dm() if looped else await ctx.author.create_dm()

        #Check if the user has unread announcements
        if announce_info[1] > 0:
            #Loop through each course's announcements
            for key, announcements in announce_info[0].items():
                #Notify which course we are on
                if len(announcements) > 0:
                    await channel.send(f"**{canvas.get_course(key).name}**") 
                #Loop through that courses' announcements
                for i, announcement in enumerate(announcements):
                    # Get html and convert it to text
                    html = announcement.message
                    text = self.cleanText(html)

                    #Create a discord embed of message (Beautifies it)
                    embed=discord.Embed(
                    title=f"{announcement.title or 'This announcement has no title'}",
                    url=f"{announcement.html_url or 'https://canvas.auckland.ac.nz'}",
                    description=f"{text[0:500]}",
                    color=0xFF5733) 

                    # Checks if we can see the an author
                    #note that author's attributes are NOT in class format, rather it is in a dict format
                    if announcement.author['display_name'] != None:

                        embed.set_author(
                        name=announcement.author['display_name'],
                        icon_url=announcement.author['avatar_image_url'],
                        url=announcement.author['html_url'] or "https://canvas.auckland.ac.nz"
                        )
                    #TO DO
                    #if announcement.unread_count != None:
                        # embed.set_footer(
                        #     text=f"This announcement was sent to {announcement.unread_count} people"
                        # )
                    # if announcement.posted_at != None or announcement.created_at != None:
                    #     print('here')
                        
                    #     #time2 = announcement.created_at.replace(tzinfo=None)
                    #     print(time1)
                    #     embed.timestamp = time1 #or time2
                    # Send the embed
                    await channel.send(embed=embed)
        else:
            #If no unread messages are found execute this
            if not looped:
                return await channel.send("You have no unread announcements.")


    @commands.command(brief="Pulls latest unread announcements", aliases=["an"])
    async def announcements(self, ctx) -> Union[str, None]:
        if not (canvas := self.checkCanvasUser(ctx)):
            return await ctx.send("User's not registered!")
        return await self.async_announcement(ctx, canvas)

        

    @commands.command(brief="Toggles Canvas to Discord Notifications", aliases=["tog"])
    async def toggle(self, ctx, toggleType:str = None) -> Union[str, None]:
        if not (canvas := self.checkCanvasUser(ctx)):
            return await ctx.send("User's not registered!")
        #If no input is given 
        if toggleType == None:
            # Send toggle stats
            await ctx.send(f"Canvas Announcement Notifications: {canvas.notifications}")
            await ctx.send(f"Upcoming Assignment Notifications: {canvas.due}")
            return
        elif toggleType == "all":
            #Invert togle stats
            canvas.notifications = not canvas.notifications
            canvas.due = not canvas.due
            #Send toggle stats
            await ctx.send(f"Canvas Announcement Notifications: {canvas.notifications}")
            await ctx.send(f"Upcoming Assignment Notifications: {canvas.due}")
            return
        elif "announce" in toggleType:
            #Invert announcement stat
            canvas.notifications = not canvas.notifications
            return await ctx.send(f"Canvas Announcement Notifications: {canvas.notifications}")
        elif "assign" in toggleType:
            #Invert assignment stat
            canvas.due = not canvas.due
            return await ctx.send(f"Upcoming Assignment Notifications: {canvas.due}")


    @commands.command(brief="Read/unread announcements", aliases = ["toggleran"])
    async def toggle_read_all_announcements(self, ctx) -> str:
        #Check if user is registered
        if not (canvas := self.checkCanvasUser(ctx)):
            return await ctx.send("User's not registered!")
        #Get announcements
        announcements: list[Announcement] = self.get_announcements(canvas)
        all_read = []
        #Loop through announcements
        for i, announcement in enumerate(announcements):
            #Get the read states of all announcements
            all_read.append(announcement.read_state)
        #Check if there is any unread announcements
        if any("unread" in read_check for read_check in all_read):
            #Mark all announcements as read
            for i, announcement in enumerate(announcements):
                announcement.mark_as_read()
            return await ctx.send("Read all announcements!")
        #All announcements are read
        else:
            #Mark all announcements as unread
            for i, announcement in enumerate(announcements):
                announcement.mark_as_unread()
            return await ctx.send("Unread all announcements!")

    #Calculates the time difference between two dates
    def calc_time_diff(self, due_date: datetime) -> int:
        #Remove time zone info
        now: datetime.datetime = datetime.now()
        due_date = due_date.replace(tzinfo=None)
        now = now.replace(tzinfo=None)
        #Get time diff
        time_diff = due_date - now
        time_diff = time_diff.total_seconds()
        return time_diff


    def get_upcoming_assignments_time(self, canvas: CanvasUser, course, days:int, want_locked:bool = False) -> dict[str, list[Assignment]]:
        # Gets the current user from canvas
        user = canvas.get_current_user()
        # Gets the favourite courses of user
        courses = user.get_favorite_courses()
        # Empty course id lists
        # Get course ids and put in list
        assignments = {}
        # Loop through all courses
        for course in courses:
            #Check if the course is not already in the assignments dict
            if course not in assignments:
                #assign an empty list to that course
                assignments[course.name] = list()
            #Get all assignments from that course
            all_assignments: list[Assignment] = course.get_assignments()
            #Loop through the assignments for that course
            for assignment in all_assignments:
                #Check if assignment is locked and we want dont want locked assignments
                if assignment.locked_for_user == True and not want_locked:
                    continue
                try:
                    #Get the due date for that assignment
                    due_date: datetime = assignment.due_at_date
                except AttributeError:
                    continue
                #Calculate the time difference in seconds from now until the due time
                seconds: int = self.calc_time_diff(due_date)
                #Check if its within our range
                if seconds > (86400 * days) or seconds < 0:
                    continue
                #Add the assignment to our list
                assignments[course.name].append(assignment)

        return assignments

    @tasks.loop(minutes = 60)
    async def check_assignments(self):
        # Loop through Canvas User instances
        for key, canvas in self.canvas_instances.items():
            # Check if they have notifications on for due assignments
            if canvas.due == True:
                # Get the assignments
                await self.async_assignments(None, self.get_upcoming_assignments_time(canvas, None, GLOBAL_DAYS, True), key, None, GLOBAL_DAYS, True)

    async def async_assignments(self, ctx, upcoming_assignments: dict[str, list[Assignment]], key: str, course: Union[str, int, None], days: int, looped: bool = False):
        # Get user's channel
        channel: Union[TextChannel, DMChannel]  = await self.guild.get_member(int(key)).create_dm() if looped else await ctx.author.create_dm()
        # Establish number of assignments
        no_assignments: int = 0

        # Loop through the upcoming assignments
        for key, assignments in upcoming_assignments.items():
            #If we have a valid course
            if course != None:
                # Capitalize the course
                course = course.upper()
                #Formatting issues
                check = key.replace(" ", "")
                # Check if it is the course we are looking for 
                if course not in check:
                    # Add to the number of assignments
                    no_assignments += 1
                    continue
            # If there are no assignments
            if len(assignments) == 0:
                no_assignments += 1
                continue
            
            # Loop through each assignment
            for assignment in assignments:
                #Get the due date
                due_date: datetime = assignment.due_at_date
                # Get complete by date in UNIX time
                complete_by = str(int(time.mktime(due_date.timetuple())) + 43200)

                # Create embed for discord
                embed=discord.Embed(
                title=f"{assignment.name or 'This assignment has no name'}",
                url=f"{assignment.html_url or 'https://canvas.auckland.ac.nz'}",
                description=f"**This assignment is due <t:{complete_by}:R> on <t:{complete_by}:F>**\n\nMessages sent about assignment reminders may be delayed or not even be sent at all! *Don't solely rely on this for reminders, this is may be unstable and should serve as a last resort*",
                color=0xFF5733) 
                #C Check if we have a key
                if key:
                    embed.set_author(
                    name=f"{key or 'Unknown Course'}",
                    #icon_url=assignment.profile['avatar_url'],
                    url=f"{assignment.html_url or 'https://canvas.auckland.ac.nz'}"
                    )
                # Send the messages
                await channel.send(f"\n**There will be an assignment/quiz due soon:** {assignment.name or ''}\n{assignment.html_url}\n*This __won't__ be updated if the assignment due date is changed.*")

                await channel.send(embed=embed)
        # Check if we have no announcements
        if no_assignments == len(upcoming_assignments):
            await channel.send(f"You have no upcoming assignments! (for at least {days} days)")
            
    @commands.command(brief="Gathers upcoming assignments", aliases = ["due"])
    async def get_upcoming_assignments(self, ctx, course: Union[str, int] = None, days: int = GLOBAL_DAYS, locked: str = "False"):
        # Check if the Canvas User instance exists
        if not (canvas := self.checkCanvasUser(ctx)):
            return await ctx.send("User's not registered!")

        # Check if the days is the default amount
        # Might need to fix this
        locked = locked.capitalize()
        if days == GLOBAL_DAYS:
            try:
                days = int(course)
                course = None
            except (ValueError, TypeError):
                days = GLOBAL_DAYS
        # Check if a valid course is provided
        if course is not None:
            #Lower the course string
            course = course.lower()
        # CHeck if all courses are wanted
        if course == "all":
            # Set course to None
            course = None
        # Change from bool to string
        if locked == "True":
            locked = True
        elif locked == "False": 
            locked = False
        else:
            return await ctx.send("Please specify a valid option for the locked parameter")
        #Check for valid days
        
        if days < 1:
            return await ctx.send("Please enter a valid amount of days")
        #Get the assignments
        await self.async_assignments(ctx, self.get_upcoming_assignments_time(canvas, course, days, locked), None, course, days, False)

        
        


            



        