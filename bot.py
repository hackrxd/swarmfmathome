import json
import os
import random
import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='!eliv')

emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]

@bot.command()
async def search(ctx, *, category, query):
    categories = {
        "evil": "audio/evil",
        "neuro": "audio/neuro",
        "extra": "audio/extra",
        "anniversary": "audio/anniversary"
    }
    if category not in categories:
        await ctx.send("Invalid category. Please choose from: evil, neuro, extra, anniversary.")
        return
    category_path = categories[category]