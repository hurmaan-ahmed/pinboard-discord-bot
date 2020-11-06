import discord
from discord.ext import commands
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import date

# Initialize Firebase credentials
cred = credentials.Certificate('./discord-pin-bot-cred.json')
firebase_admin.initialize_app(cred)

# Start up the firebase client
db = firestore.client()

# Set command prefix for the bot
bot = commands.Bot(command_prefix = '!')

# Runs when the bot comes online
@bot.event
async def on_ready():
    print('Bot online')

# Creates the board
@bot.command()
async def create(ctx, name):
    board_name_ref = db.collection('boards').document(f'{name}')
    if board_name_ref.get().exists:
        await ctx.send(f"The following board: '{name}' already exists! :x:")
    else:
        # messages_ref = board_name_ref.collection("messages").document(ctx.message.author.id).set
        today = date.today()
        board_name_ref.set(
            {
                "createdBy": ctx.message.author.id,
                "dateCreated": today.strftime("%d/%m/%Y")
            }
        )
        await ctx.send(f"The board: '{name}' was created! :white_check_mark:")

# Add permissions to only allow user who created their board, or admin to delete specific board
@bot.command()
async def delete(ctx, name):
    board_name_ref = db.collection('boards').document(f'{name}')
    if board_name_ref.get().exists == False:
        await ctx.send(f"The following board: '{name}' does not exist! :slight_frown:")
    else:
        board_name_ref.delete()
        await ctx.send(f"The following board: '{name}' was deleted! :white_check_mark:")

# Bot token
bot.run('TOKEN GOES HERE')
