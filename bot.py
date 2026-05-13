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

priority_queue = []
queue = []
result_cache = {}  # Map message IDs to search results
reacted_users = set()  # Track (message_id, user_id) pairs to prevent duplicate adds

@bot.event
async def on_reaction_add(reaction, user):
    """Add song to queue when user reacts with emoji"""
    if user.bot or reaction.message.id not in result_cache:
        return
    
    user_reaction_key = (reaction.message.id, user.id)
    if user_reaction_key in reacted_users:
        return  # Already added this song
    
    try:
        emoji_index = emojis.index(str(reaction.emoji))
        results = result_cache[reaction.message.id]
        if emoji_index < len(results):
            song = results[emoji_index]
            priority_queue.append(song)
            reacted_users.add(user_reaction_key)
            await reaction.message.channel.send(f"✓ Added **{song}** to priority queue")
    except ValueError:
        pass

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
        return
    
    category_path = categories[category]
    if not os.path.exists(category_path):
        await ctx.send(f"Error: Category path not found. <@759167810814476319>")
        return
    
    results = [f for f in os.listdir(category_path) if query.lower() in f.lower()]
    
    if not results:
        await ctx.send("nothing was found (probably because you spelt it wongly)")
        return
    
    # Limit to 9 results
    if len(results) > 9:
        results = random.sample(results, 9)
        overflow = True
    else:
        overflow = False
    
    # Send exactly ONE message
    message_text = "**Search results:**\n" + "\n".join(f"{emojis[i]} {result}" for i, result in enumerate(results))
    if overflow:
        message_text += "\n\n-# too many results, try being a little more specific"
    
    msg = await ctx.send(message_text)
    result_cache[msg.id] = results
    
    # Add emoji reactions
    for i in range(len(results)):
        await msg.add_reaction(emojis[i])

@bot.command()
async def queue(ctx):
    if not priority_queue and not queue:
        await ctx.send("The queue is currently empty.")
        return
    message = "**Current Queue:**\n"
    if priority_queue:
        message += "**Priority Queue:**\n" + "\n".join(f"- {song}" for song in priority_queue) + "\n"
    if queue:
        message += "**Queue:**\n" + "\n".join(f"- {song}" for song in queue) + "\n"

    await ctx.send(message)

@bot.command()
async def join(ctx):
    if ctx.author.voice is None:
        await ctx.send("You need to be in a voice channel to use this command.")
        return
    channel = ctx.author.voice.channel
    await channel.connect()

@bot.command()
async def play(ctx):
    if ctx.voice_client is None:
        await ctx.send("I need to be in a voice channel to play music. Use `!eliv join` to invite me.")
        return
    message = await ctx.send("Starting playback...")
    if priority_queue:
        song = priority_queue.pop(0)
    elif queue:
        song = queue.pop(0)
    else:
        await message.edit(content="Generating queue...")
        allaudio = []
        allaudio.append(os.listdir("audio/evil"))
        allaudio.append(os.listdir("audio/neuro"))
        allaudio.append(os.listdir("audio/extra"))
        allaudio.append(os.listdir("audio/anniversary"))
        allaudio.append(os.listdir("audio/duet"))
        while queue < 5:
            category = random.choice(allaudio)
            song = random.choice(category)
            if song not in queue:
                queue.append(song)
        return
    
    category = None
    for cat, path in {
        "evil": "audio/evil",
        "neuro": "audio/neuro",
        "extra": "audio/extra",
        "anniversary": "audio/anniversary",
        "duet": "audio/duet"
    }.items():
        if os.path.exists(os.path.join(path, song)):
            category = cat
            break
    
    if category is None:
        await ctx.send(f"Error: Could not find the file for **{song}**. <@759167810814476319>")
        return
    
    source = discord.FFmpegPCMAudio(os.path.join(path, song))
    ctx.voice_client.play(source)
    await message.edit(content=f"Now playing: **{song}**")

bot.run(os.getenv("BOT_TOKEN"))