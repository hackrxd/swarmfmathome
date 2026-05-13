import json
import os
import random
import discord
import dotenv
from discord.ext import commands

dotenv.load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!eliv ', intents=intents)

emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]

@bot.command()
async def search(ctx, category, *, query):
    categories = {
        "evil": "audio/evil",
        "neuro": "audio/neuro",
        "extra": "audio/extra",
        "anniversary": "audio/anniversary",
        "duet": "audio/duet"
    }
    if category not in categories:
        await ctx.send("Invalid category. Please choose from: evil, neuro, extra, anniversary, duet.")
        print(f"User {ctx.author} attempted to search with invalid category: {category}")
        return
    category_path = categories[category]
    if not os.path.exists(category_path):
        await ctx.send(f"Error: hackr was too stupid to write the actual category path so now you have to suffer for it XD. actually wait i can ping him about it. <@759167810814476319>")
        return
    results = []
    for file in os.listdir(category_path):
        if query.lower() in file.lower():
            results.append(file)
    if not results:
        await ctx.send("nothing was found (probably becuase you speld wong)")
        print(f"User {ctx.author} searched for '{query}' in category '{category}' but found no results.")
        return
    overflow = False
    if len(results) > 9:
        results = random.sample(results, 9)
        overflow = True
    
    # Build message with reactions
    message_text = "**Search results:**\n" + "\n".join(f"{emojis[i]} {result}" for i, result in enumerate(results))
    if overflow:
        message_text += "\n\n-# too many results, try being a little more specific because i don't know what you're talking about."
    print(f"User {ctx.author} searched for '{query}' in category '{category}' and found {len(results)} results.")
    
    msg = await ctx.send(message_text)
    
    # Add emoji reactions
    for i in range(len(results)):
        await msg.add_reaction(emojis[i])

bot.run(os.getenv("BOT_TOKEN"))