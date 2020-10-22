import discord
from discord.ext import commands

bot = commands.Bot(command_prefix = '!')

@bot.event
async def on_ready():
    print('Bot online')

@bot.event #command recognition
async def on_message(message):
    if message.author == bot.user:
        return
    if message.content.startswith('!commands'):
        await message.channel.send('Available commands: !pinboards, !newpb')
    if message.content.startswith('!pinboards'):
        await message.channel.send('To be implemented, show a list of pinboards')
    if message.content.startswith('!cdaily'):
        await message.channel.send('To be implemented; create a new pinboard')




bot.run('NzY3NDk5MzM1MjM5NDY3MDA4.X4yzdA.j6Ryhhwww9M0zxEgra3yIHTAcC8')#bot token
