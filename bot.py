import json
import os
import random
import asyncio
import discord
import dotenv
from discord.ext import commands

dotenv.load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!eliv ', intents=intents)

emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]

priority_queue = []
song_queue = []
result_cache = {}  # Map message IDs to search results
reacted_users = set()  # Track (message_id, user_id) pairs to prevent duplicate adds
now_playing_message = None  # Track the message showing current song
is_playing = False  # Track if currently playing

async def play_next_song(voice_client):
    """Play the next song in the queue"""
    global is_playing, now_playing_message
    
    if not voice_client or not voice_client.is_connected():
        return
    
    # Refill queue if low
    if len(song_queue) < 3:
        allaudio = [
            files for files in [
                os.listdir("audio/evil"),
                os.listdir("audio/neuro"),
                os.listdir("audio/extra"),
                os.listdir("audio/anniversary"),
                os.listdir("audio/duet")
            ] if files
        ]
        while len(song_queue) < 5 and allaudio:
            category = random.choice(allaudio)
            song_choice = random.choice(category)
            if song_choice not in song_queue:
                song_queue.append(song_choice)
    
    # Pick next song
    if priority_queue:
        song = priority_queue.pop(0)
    elif song_queue:
        song = song_queue.pop(0)
    else:
        is_playing = False
        return
    
    # Find song file
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
        # Skip to next if file not found
        await play_next_song(voice_client)
        return
    
    # Play the song
    source = discord.FFmpegPCMAudio(os.path.join(path, song))
    voice_client.play(source, after=lambda e: asyncio.create_task(play_next_song(voice_client)))
    is_playing = True

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

@bot.command(name="queue")
async def queuelist(ctx):
    if not priority_queue and not song_queue:
        await ctx.send("The queue is currently empty.")
        return
    message = ""
    if priority_queue:
        message += "**Priority Queue:**\n" + "\n".join(f"- {song}" for song in priority_queue) + "\n"
    if song_queue:
        message += "**Queue:**\n" + "\n".join(f"- {song}" for song in song_queue) + "\n"

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
    
    global is_playing
    
    if is_playing and ctx.voice_client.is_playing():
        await ctx.send("Already playing! Use `!eliv skip` to skip or check `!eliv queue`.")
        return
    
    # Generate initial queue if empty
    if not priority_queue and not song_queue:
        allaudio = [
            files for files in [
                os.listdir("audio/evil"),
                os.listdir("audio/neuro"),
                os.listdir("audio/extra"),
                os.listdir("audio/anniversary"),
                os.listdir("audio/duet")
            ] if files
        ]
        
        while len(song_queue) < 5 and allaudio:
            category = random.choice(allaudio)
            song_choice = random.choice(category)
            if song_choice not in song_queue:
                song_queue.append(song_choice)
    
    await ctx.send("▶️ Starting playback...")
    await play_next_song(ctx.voice_client)

@bot.command()
async def skip(ctx):
    if ctx.voice_client is None or not ctx.voice_client.is_playing():
        await ctx.send("Nothing is playing.")
        return
    ctx.voice_client.stop()
    await ctx.send("⏭️ Skipped to next song.")

@bot.command()
async def stop(ctx):
    if ctx.voice_client is None:
        await ctx.send("I'm not in a voice channel.")
        return
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
    await ctx.send("⏹️ Stopped playback.")

@bot.command()
async def restartandupdate(ctx):
    await ctx.send("Bot will restart after this song finishes to apply code updates.")
    restart = True

bot.run(os.getenv("BOT_TOKEN"))