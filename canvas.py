import discord
from discord import TextChannel, DMChannel, VoiceChannel, Member
from discord import app_commands
from discord.ext import commands, tasks
from discord.ext.commands import Bot
from datetime import datetime, timedelta

import canvasapi
import os
from canvasapi import Canvas
from canvasapi.exceptions import InvalidAccessToken, ResourceDoesNotExist, Forbidden
from html2text import HTML2Text
from pathlib import Path

import random
import json
from io import BytesIO
from fpdf import FPDF

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
        self.notifications = False
        self.due = False
        self.get_grades()


    def get_grades(self):
        course_ids = []
        user = super().get_current_user()        
        enrollments = user.get_enrollments()
        #await interaction.channel.send("Loading...", ephemeral=True)
        self.grades_string = ""
        #Loop through their enrollmenets
        for i, course in enumerate(enrollments):
            #Skip repeated enrollments (bug)
            if course.course_id in course_ids:
                continue
            #Add the course id to the list
            course_ids.append(course.course_id)
            #Add the grades to the grade string
            self.grades_string = f"{self.grades_string}+ {super().get_course(course.course_id).name}: {course.grades.get('final_grade')} \n"

def RandomColor(): #generates a random discord colour that will be used in the embeds
  randcolor = discord.Color(random.randint(0x000000, 0xFFFFFF))
  return randcolor

class CanvasCog(commands.Cog):
    def __init__(self, bot):
        #Get Discord Bot
        self.bot = bot
        #Get Acad server
        self.guild = self.bot.guilds[0]
        #Instantiate Tokens so they do not need to login
        json_file = open(".git/canvas_tokens.json")
        # Load the JSON data from the file
        tokens:dict = json.load(json_file)


        #Create a dictionary of canvas instances
        self.canvas_instances = {user["discord_id"]: CanvasUser(API_URL,user["canvas_token"]) for user in tokens["users"]}
        #Close the file
        json_file.close()
        #Start loops to check for announcements and assignments
        # self.check_announcements.start()
        self.check_assignments.start()
    
    #Method to check if user is a discord user
    def checkCanvasUser(self, interaction:discord.Interaction):
        #Loop through current canvas instances
        for key, value in self.canvas_instances.items():
            #Check if the interaction user is in the dict
            if key == str(interaction.user.id):
                #Return the canvas Obj
                return value
        return False
    

    @app_commands.command(description="Login to canvas")
    async def login(self, interaction:discord.Interaction, token:str):
        #If logging in a public channel remove the login message
        #Check if user is already registered
        if isinstance(self.checkCanvasUser(interaction), CanvasUser):
            return await interaction.response.send_message("User already registered", ephemeral=True)
        #Create a new CanvasUSer instance for the user
        newUser = CanvasUser(API_URL, token)
        
        #Check if the user's token was valid...
        try:
            newUser.get_course(1)

        except InvalidAccessToken:

            return await interaction.response.send_message("Invalid Access Token!", ephemeral=True)

        except (ResourceDoesNotExist, Forbidden):
            await interaction.response.send_message("Successfully registered user!", ephemeral=True)
        # Add user into the dictionary
        temp_dict = {str(interaction.user.id):newUser}
        self.canvas_instances.update(temp_dict)
        

    def get_modules(self, canvas: CanvasUser):
        user = canvas.get_current_user()
        courses = user.get_favorite_courses()
        modules = {}
        for course in courses:
            modules[course.id] = list(course.get_modules())
        return modules

    @app_commands.command(description="gets downloadable modules")
    async def modules(self, interaction:discord.Interaction, check_course:str=None):

        def check(reaction, user):
            return user == interaction.user and str(reaction.emoji) in ["⬇️"]

        #Check if the user is verified
        if not (canvas := self.checkCanvasUser(interaction)):
            return await interaction.response.send_message("User's not registered!")
        all_modules = self.get_modules(canvas)
        
        await interaction.response.send_message("Printing modules...")
        messages = {}
        for module_id, course_modules in all_modules.items():
            
            course = canvas.get_course(module_id)
            
            if check_course != None:
                check_course = check_course.upper()
                #Formatting issues
                course_name = course.name.replace(" ", "")

                if check_course not in course_name:
                    continue
            message = await interaction.channel.send(f"Modules for {course.name}")
            messages[message] = None
            for module in course_modules:
                for module_item in module.get_module_items():
                    if module_item.type != "File":
                        continue
                    message = await interaction.channel.send(module_item.title)
                    await message.add_reaction("⬇️")
                    messages[message] = module_item
                    
                
        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=5, check=check)
                if reaction.message in messages.keys():
                    message = reaction.message
                    module_item = messages.get(message)
                    if str(reaction.emoji) == "⬇️":
                        await message.remove_reaction(reaction, user)
                        
                        course = canvas.get_course(module_item.course_id)
                        file_download = course.get_file(module_item.content_id)
                        await interaction.channel.send(f"Downloading {file_download.filename}")
                        #file_download.download(f"{str(Path.home())}\\Downloads\\{file_download.filename}")
                        #await asyncio.sleep(5)
                        await interaction.channel.send(file=discord.File(BytesIO(file_download.get_contents(binary=True)), filename = f"{file_download.filename}"))


                    else:
                        await reaction.message.remove_reaction(reaction, user)

            except asyncio.TimeoutError:
                return await interaction.channel.delete_messages([message for message in messages.keys()])
                

    @app_commands.command(description="Returns person's grades")
    async def grades(self, interaction:discord.Interaction):
        #Check if the user is verified
        if not (canvas := self.checkCanvasUser(interaction)):
            return await interaction.response.send_message("User's not registered!")

        await interaction.response.send_message(canvas.grades_string, ephemeral=True)


    #Function clean up HTML texts
    def cleanText(self, text):
        h = HTML2Text()
        h.ignore_links = False
        text = h.handle(text)
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



    # Gets announcements asynchronously
    async def async_announcement(self, interaction:discord.Interaction, canvas: CanvasUser, looped:bool = False, key:str = None) -> None:
        # Get announcements info
        announce_info = self.announcement(canvas)
        #Create a private dm with user
        channel = await self.guild.get_member(int(key)).create_dm() if looped else await interaction.user.create_dm()
        
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
                    description=f"{text[0:1500]}" if len(text) > 1500 else f"{text}",
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


    @app_commands.command(description="Pulls latest unread announcements")
    async def announcements(self, interaction:discord.Interaction) -> str:
        if not (canvas := self.checkCanvasUser(interaction)):
            return await interaction.response.send_message("User's not registered!")
        await interaction.response.send_message("Getting latest announcements")
        return await self.async_announcement(interaction, canvas)

        

    @app_commands.command(description="Toggles Canvas to Discord Notifications")
    async def toggle(self, interaction:discord.Interaction, toggle_type:str = None) -> str:
        if not (canvas := self.checkCanvasUser(interaction)):
            return await interaction.response.send_message("User's not registered!")
        #If no input is given 
        if toggle_type == None:
            # Send toggle stats
            return await interaction.response.send_message(f"Canvas Announcement Notifications: {canvas.notifications}\nUpcoming Assignment Notifications: {canvas.due}")
        elif toggle_type == "all":
            #Invert togle stats
            canvas.notifications = not canvas.notifications
            canvas.due = not canvas.due
            #Send toggle stats
            return await interaction.response.send_message(f"Canvas Announcement Notifications: {canvas.notifications}\nUpcoming Assignment Notifications: {canvas.due}")
            
        elif "announce" in toggle_type:
            #Invert announcement stat
            canvas.notifications = not canvas.notifications
            return await interaction.send(f"Canvas Announcement Notifications: {canvas.notifications}")
        elif "assign" in toggle_type:
            #Invert assignment stat
            canvas.due = not canvas.due
            return await interaction.response.send_message(f"Upcoming Assignment Notifications: {canvas.due}")


    @app_commands.command(description="Read/unread announcements")
    async def toggle_read(self, interaction:discord.Interaction) -> str:
        #Check if user is registered
        if not (canvas := self.checkCanvasUser(interaction)):
            return await interaction.response.send_message("User's not registered!")
        #Get announcements
        await interaction.response.send_message("Toggling")
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
            return await interaction.channel.send("Read all announcements!")
        #All announcements are read
        else:
            #Mark all announcements as unread
            for i, announcement in enumerate(announcements):
                announcement.mark_as_unread()
            return await interaction.channel.send("Unread all announcements!")

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

    @tasks.loop(minutes = 10)
    async def check_announcements(self) -> None:
        #Loop through all CanvasUser instances
        for key, canvas in self.canvas_instances.items():
            #Check if they have announcement notifications on
            if canvas.notifications == True:
                await self.async_announcement(None, canvas, True, key)
                
    @tasks.loop(minutes = 60)
    async def check_assignments(self):
        # Loop through Canvas User instances
        for key, canvas in self.canvas_instances.items():
            # Check if they have notifications on for due assignments
            if canvas.due == True:
                # Get the assignments
                await self.async_assignments(None, self.get_upcoming_assignments_time(canvas, None, GLOBAL_DAYS, False), key, None, GLOBAL_DAYS, True)

    async def async_assignments(self, interaction:discord.Interaction, upcoming_assignments: dict[str, list[Assignment]], key: str, course: str, days: int, looped: bool = False):
        # Get user's channel
        channel = await self.guild.get_member(int(key)).create_dm() if looped else await interaction.user.create_dm()
        # Establish number of assignments
        no_assignments: int = 0

        # Loop through the upcoming assignments
        text = ""
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
                text = text + f"**[{assignment.name or 'No title'}]({assignment.html_url or 'https://canvas.auckland.ac.nz'})**\n*[{key or 'Unknown Course'}]({assignment.html_url or 'https://canvas.auckland.ac.nz'})*\n> due <t:{complete_by}:R> on <t:{complete_by}:F>\n\n"
           
            # Create embed for discord
        embed=discord.Embed(
        title = "Deadlines",
        description=text,
        color=0xFF5733) 
        await channel.send(embed=embed)
        # Check if we have no announcements
        if no_assignments == len(upcoming_assignments):
            if not looped:
                await channel.send(f"You have no upcoming assignments! (for at least {days} days)")
            
    @app_commands.command(description="Gathers upcoming assignments")
    async def assignments(self, interaction:discord.Interaction, course: str = None, days: int = GLOBAL_DAYS, locked: str = "False"):
        # Check if the Canvas User instance exists
        await interaction.response.defer(ephemeral=True, thinking=True)
        if not (canvas := self.checkCanvasUser(interaction)):
            return await interaction.edit_original_response(content="User's not registered!")

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
            return await interaction.edit_original_response(content="Please specify a valid option for the locked parameter")
        #Check for valid days
        
        if days < 1:
            return await interaction.edit_original_response(content="Please enter a valid amount of days")
        await interaction.edit_original_response(content="Loading assignments")
        #Get the assignments
        await self.async_assignments(interaction, self.get_upcoming_assignments_time(canvas, course, days, locked), None, course, days, False)