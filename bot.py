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
    if not os.path.exists(category_path):
        await ctx.send(f"Error: hackr was too stupid to write the actual category path so now you have to suffer for it XD")
        return
    results = []
    for file in os.listdir(category_path):
        if query.lower() in file.lower():
            results.append(file)
    if not results:
        await ctx.send("nothing was found (probably becuase you speld wong)")
        return
    overflow = False
    if len(results) > 9:
        results = random.sample(results, 9)
        overflow = True
    
    # Build message with reactions
    message_text = "**Search results:**\n" + "\n".join(f"{emojis[i]} {result}" for i, result in enumerate(results))
    if overflow:
        message_text += "\n\n-# too many results, try being a little more specific because i don't know what you're talking about."
    
    msg = await ctx.send(message_text)
    
    # Add emoji reactions
    for i in range(len(results)):
        await msg.add_reaction(emojis[i])