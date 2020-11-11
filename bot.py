import discord
from discord.ext import commands
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime, timedelta
import time
import sched

# Initialize Firebase credentials
cred = credentials.Certificate('./discord-pin-bot-cred.json')
firebase_admin.initialize_app(cred)

# Start up the firebase client
db = firestore.client()

# Set command prefix for the bot
bot = commands.Bot(command_prefix='!', help_command=None)

# Runs when the bot comes online
@bot.event
async def on_ready():
    print('Bot online')

# Determines if correct positional arguments are passed into the function
@bot.event
async def on_command_error(ctx, error):
    # If the correct parameters are not inputted with the command, then raise this error
    if isinstance(error, commands.MissingRequiredArgument):
        # Create an embed and send it to the chat
        embed = discord.Embed(color=discord.Color.red(),
                              description=str(error))
        await ctx.send(embed=embed)

# Gives an overview of the bot and its various functionality
@bot.command()
async def help(ctx):
    # Add fields for all of the different commands that can be used, helpful for the user
    bot_description = "The Pinboard Bot brings the world-renowned pinboard to discord and allows you to organize messages and build communities!"
    embed = discord.Embed(title="Available Commands",
                          color=discord.Color.dark_gold(), description=bot_description)
    embed.set_author(name="Pinboard Bot",
                     icon_url="https://cdn-0.emojis.wiki/emoji-pics/twitter/pushpin-twitter.png")
    embed.add_field(
                    name="!help",
                    value="Learn more about the bot", inline=False)
    embed.add_field(name="!create <board_name>",
                    value="Create a new board", inline=False)
    embed.add_field(name="!create_daily <board_name>",
                    value="Create a new daily board", inline=False)
    embed.add_field(name="!delete <board_name>",
                    value="Delete a board", inline=False)
    embed.add_field(name="!pin <board_name> <msg>",
                    value="Pin a message to the board", inline=False)
    embed.add_field(name="!edit_pin <board_name> <pin_id> <new_msg>",
                    value="Edit a specific pin", inline=False)
    embed.add_field(name="!delete_pin <board_name> <pin_id>",
                    value="Delete a specific pin", inline=False)
    embed.add_field(name="!show <board_name>",
                    value="Show the contents of a board", inline=False)
    await ctx.send(embed=embed)


# Creates the board
@bot.command()
async def create(ctx, name):
    # Get the board document name
    board_name_ref = db.collection('boards').document(f'{name}')
    # If the board already exists in the database, then send message saying that it already exists 
    if board_name_ref.get().exists:
        embed = discord.Embed(color=discord.Color.red(
        ), description=f"The following board: '{name}' already exists! :x:")
        await ctx.send(embed=embed)
        return -1
    else:
        # Get current time
        today = datetime.now()
        # Set the appropriate fields based on when the board has been created
        board_name_ref.set(
            {
                "createdBy": ctx.message.author.id,
                "userName": str(bot.get_user(ctx.message.author.id)),
                "dateCreated": today.strftime("%m/%d/%Y %I:%M %p")
            }
        )
        # Notify user that the board has been created
        embed = discord.Embed(color=discord.Color.green(
        ), description=f"The board: '{name}' was created! :white_check_mark:")
        await ctx.send(embed=embed)
        return 0

# Ability to delete a board, permissions are set to prevent users from deleting other user's boards
@bot.command()
async def delete(ctx, name):
    # Get the specified board from the database
    board_name_ref = db.collection('boards').document(f'{name}')
    # If the board does not exist, then let the user know
    if board_name_ref.get().exists == False:
        await ctx.send(embed=discord.Embed(color=discord.Color.red(), description=f"The following board: '{name}' does not exist! :slight_frown:"))
        return
    # Permissions: If user did not create the board, then they cannot delete it
    if board_name_ref.get().to_dict()['createdBy'] != ctx.message.author.id:
        await ctx.send(embed=discord.Embed(color=discord.Color.red(), description=f"You cannot delete a board that is not yours! :slight_frown:"))
        return
    # If they can delete, then delete the board then notify the user
    board_name_ref.delete()
    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"The following board: '{name}' was deleted! :white_check_mark:"))

# Creates a daily board which clears out the pins every 24 hours from its creation
@bot.command()
async def create_daily(ctx, name):
    # Get the name that is to be used for the creation of the daily board
    board_name_ref = db.collection('boards').document(f'{name}')
    # If it already exists, then let user know
    if board_name_ref.get().exists:
        embed = discord.Embed(color=discord.Color.red(
        ), description=f"The following board: '{name}' already exists! :x:")
        await ctx.send(embed=embed)
        return
    else:
       # Get current time, and set appropriate fields for the database board
        today = datetime.now()
        board_name_ref.set(
            {
                "createdBy": ctx.message.author.id,
                "userName": str(bot.get_user(ctx.message.author.id)),
                "dateCreated": today.strftime("%m/%d/%Y %I:%M %p")
            }
        )
        embed = discord.Embed(color=discord.Color.green(
        ), description=f"The board: '{name}' was created! :white_check_mark:\nNote: The board created will be deleted in 24 hours!")
        await ctx.send(embed=embed)
        schedule = sched.scheduler(time.perf_counter, time.sleep)
        # Schedule to delete after 24 hours
        schedule.enter(86400, 1)
        # Delete all pins from the board
        board_name_ref = db.collection('boards').document(f'{name}')
        messages_ref = board_name_ref.get().to_dict()['messages']
        messages_ref = []
        board_name_ref.update(
            {
                "messages": messages_ref,
            }
        )
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f'All pins from the daily board: {name} were removed after 24 hours! :white_check_mark:'))


# Ability to pin messages on a specific board
@bot.command()
async def pin(ctx, name, *, message):
    # Get the current time
    today = datetime.now()
    # Get the board name in which the message should be pinned
    board_name_ref = db.collection('boards').document(f'{name}')
    # If the board doesn't exist, then let the user know
    if board_name_ref.get().exists == False:
        await ctx.send(embed=discord.Embed(color=discord.Color.red(), description=f"The following board: '{name}' does not exist! :slight_frown:"))
        return
    # Update the board with the new message
    board_name_ref.update(
        {
            "messages": firestore.ArrayUnion([{
                "message": message,
                "postedBy": ctx.message.author.id,
                "datePinned": today.strftime("%m/%d/%Y %I:%M %p"),
            }])
        }
    )
    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"Your message was pinned! :grinning:"))

# Ability to delete a pin on a particular board
@bot.command()
async def delete_pin(ctx, name, pin_id):
    # If the user passes in an incorrect pin_id such as a letter, then throw an exception, let the user know
    try:
        pin_id = int(pin_id)
    except:
        await ctx.send(embed=discord.Embed(color=discord.Color.red(), description=f"Ensure that the pin id is an integer! :slight_frown:"))
        return
    # Get the board name, if it doesn't exist, let the user know
    board_name_ref = db.collection('boards').document(f'{name}')
    if board_name_ref.get().exists == False:
        await ctx.send(embed=discord.Embed(color=discord.Color.red(), description=f"The following board: '{name}' does not exist! :slight_frown:"))
        return
    # User cannot delete pin that they didn't post
    if board_name_ref.get().to_dict()['createdBy'] != ctx.message.author.id:
        await ctx.send(embed=discord.Embed(color=discord.Color.red(), description=f"You cannot delete a pin that you didn't post! :slight_frown:"))
        return
    # If there are no pins on the board, then let the user know
    try:
        messages_ref = board_name_ref.get().to_dict()['messages']
    except:
        await ctx.send(embed=discord.Embed(color=discord.Color.red(), description="No pins were found on the specified board! :pushpin::slight_frown:"))
        return
    numMessages = len(messages_ref)
    if numMessages == 0:
        await ctx.send(embed=discord.Embed(color=discord.Color.red(), description="No pins were found on the specified board! :pushpin::slight_frown:"))
        return
    # If an incorrect pin_id is specified, such as being out of range, then let the user know
    if(pin_id <= 0 or pin_id > len(messages_ref)):
        await ctx.send(embed=discord.Embed(color=discord.Color.red(), description="Ensure that you are entering a correct pin id! :pushpin::slight_frown:"))
        return
    # Delete the pin and update the board
    del messages_ref[pin_id-1]
    board_name_ref.update(
        {
            "messages": messages_ref,
        }
    )
    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f'Pin {pin_id} was removed from the board! :white_check_mark:'))

# Ability to edit a pin on a particular pin
@bot.command()
async def edit_pin(ctx, name, pin_id, *, message):
    try:
        pin_id = int(pin_id)
    except:
        await ctx.send(embed=discord.Embed(color=discord.Color.red(), description=f"Ensure that the pin id is an integer! :slight_frown:"))
        return
    board_name_ref = db.collection('boards').document(f'{name}')
    if board_name_ref.get().exists == False:
        await ctx.send(embed=discord.Embed(color=discord.Color.red(), description=f"The following board: '{name}' does not exist! :slight_frown:"))
        return
    if board_name_ref.get().to_dict()['createdBy'] != ctx.message.author.id:
        await ctx.send(embed=discord.Embed(color=discord.Color.red(), description=f"You cannot delete a pin that you didn't post! :slight_frown:"))
        return
    try:
        messages_ref = board_name_ref.get().to_dict()['messages']
    except:
        await ctx.send(embed=discord.Embed(color=discord.Color.red(), description="No pins were found on the specified board! :pushpin::slight_frown:"))
        return
    numMessages = len(messages_ref)
    if numMessages == 0:
        await ctx.send(embed=discord.Embed(color=discord.Color.red(), description="No pins were found on the specified board! :pushpin::slight_frown:"))
        return
    if(pin_id <= 0 or pin_id > len(messages_ref)):
        await ctx.send(embed=discord.Embed(color=discord.Color.red(), description="Ensure that you are entering a correct pin id! :pushpin::slight_frown:"))
        return
    # Edit the pin based on the new message that was specified
    messages_ref[pin_id-1]['message'] = message
    board_name_ref.update(
        {
            "messages": messages_ref,
        }
    )
    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f'Pin {pin_id} was updated on the following board: {name}'))

# Show all pins present within a specific board
@bot.command()
async def show(ctx, name):
    board_name_ref = db.collection('boards').document(f'{name}')
    if board_name_ref.get().exists == False:
        await ctx.send(embed=discord.Embed(color=discord.Color.red(), description=f"The following board: '{name}' does not exist! :slight_frown:"))
        return
    try:
        messages_ref = board_name_ref.get().to_dict()['messages']
    except:
        await ctx.send(embed=discord.Embed(color=discord.Color.red(), description="No pins were found on the specified board! :pushpin::slight_frown:"))
        return
    numMessages = len(messages_ref)
    if numMessages == 0:
        await ctx.send(embed=discord.Embed(color=discord.Color.red(), description="No pins were found on the specified board! :pushpin::slight_frown:"))
        return
    # Show the contents of the board
    embed = discord.Embed(
        title=f'Board Name: {name} :pushpin:', description="All Pins", color=0xffff00)
    embed.set_footer(text=f'{numMessages} pins',
                     icon_url="https://cdn-0.emojis.wiki/emoji-pics/twitter/pushpin-twitter.png")
    # Loop through each pin and update on the embed, then show it to the user
    i = 1
    for msg in messages_ref:
        embed.add_field(name="Pin", value=i, inline=True)
        embed.add_field(name="Message", value=msg["message"], inline=True)
        embed.add_field(name="Posted By", value=bot.get_user(
            msg["postedBy"]), inline=True)
        i += 1
    await ctx.send(embed=embed)

# List all the available boards that can be posted on
@bot.command()
async def list(ctx):
    # Get a list of all the board present within the database
    all_boards_ref = db.collection('boards').get()
    if len(all_boards_ref) == 0:
        await ctx.send(embed=discord.Embed(color=discord.Color.red(), description="No boards were found! :pushpin::slight_frown:"))
        return
    authors = []
    board_names = []
    # For each board, append the board names and the author names
    for board in all_boards_ref:
        authors.append(db.collection('boards').document(
            board.id).get().to_dict()["userName"])
        board_names.append(board.id)
    # Send an embed to the channel with the information regarding all of the boards
    embed = discord.Embed(
        title="Boards", description="All available boards", color=0xffff00)
    embed.add_field(name="Board List :pushpin:",
                    value="\n".join(board_names), inline=True)
    embed.add_field(name="Created by :pencil2:",
                    value="\n".join(authors), inline=True)
    await ctx.send(embed=embed)

# Bot token
bot.run('NzY3NDk5MzM1MjM5NDY3MDA4.X4yzdA.i17m622-8xipvZG7EHBVnMQmxjU')
