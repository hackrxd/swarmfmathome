import json
import os
import random
import asyncio
from pathlib import Path
import discord
import subprocess
import sys
import dotenv
from discord.ext import commands

dotenv.load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!eliv ', intents=intents)

emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]

AUDIO_CATEGORIES = {
    "evil": "audio/evil",
    "neuro": "audio/neuro",
    "extra": "audio/extra",
    "anniversary": "audio/anniversary",
    "duet": "audio/duet"
}

priority_queue = []
song_queue = []
result_cache = {}  # Map message IDs to search results
reacted_users = set()  # Track (message_id, user_id) pairs to prevent duplicate adds
now_playing_message = None  # Track the message showing current song
is_playing = False  # Track if currently playing
restart = False  # Flag to trigger restart after current song


def get_all_songs():
    """Return a flat list of (path, filename) tuples across all categories, with equal per-song weight."""
    all_songs = []
    for path in AUDIO_CATEGORIES.values():
        if os.path.exists(path):
            for f in os.listdir(path):
                all_songs.append((path, f))
    return all_songs


def refill_queue(target_size=5):
    """Refill song_queue up to target_size, picking songs with equal probability."""
    all_songs = get_all_songs()
    if not all_songs:
        return
    attempts = 0
    while len(song_queue) < target_size and attempts < 100:
        attempts += 1
        path, song = random.choice(all_songs)
        if song not in song_queue:
            song_queue.append(song)


async def play_next_song(voice_client):
    """Play the next song in the queue."""
    global is_playing, now_playing_message, restart

    if not voice_client or not voice_client.is_connected():
        return

    if restart:
        script_location = Path(__file__).resolve().parent
        await voice_client.disconnect()
        subprocess.run(
            ["git", "pull"],
            cwd=script_location,
            capture_output=True,
            text=True,
            check=True
        )
        os.execv(sys.executable, ['python'] + sys.argv)

    # Refill queue if low
    if len(song_queue) < 3:
        refill_queue(target_size=5)

    # Pick next song
    if priority_queue:
        song = priority_queue.pop(0)
    elif song_queue:
        song = song_queue.pop(0)
    else:
        is_playing = False
        return

    # Find song file
    song_path = None
    for path in AUDIO_CATEGORIES.values():
        full_path = os.path.join(path, song)
        if os.path.exists(full_path):
            song_path = full_path
            break

    if song_path is None:
        # Skip to next if file not found
        await play_next_song(voice_client)
        return
    #send message about now playing
    channel = 1441195017938141325
    channel_obj = bot.get_channel(channel)
    await channel_obj.send(f"Now playing: **{song}**")
    # Play the song
    source = discord.FFmpegPCMAudio(song_path)
    loop = asyncio.get_event_loop()
    voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(voice_client), loop))
    is_playing = True


@bot.event
async def on_ready():
    # join voice and start playing immediately on startup
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    # Join voice channel and start playing immediately
    channel = 1432156169203617802
    channel_obj = bot.get_channel(channel)
    if channel_obj and isinstance(channel_obj, discord.VoiceChannel):
        voice_client = await channel_obj.connect()
        await play_next_song(voice_client)

@bot.event
async def on_reaction_add(reaction, user):
    """Add song to queue when user reacts with emoji."""
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
    if category not in AUDIO_CATEGORIES:
        await ctx.send("Invalid category. Please choose from: evil, neuro, extra, anniversary, duet.")
        return

    category_path = AUDIO_CATEGORIES[category]
    if not os.path.exists(category_path):
        await ctx.send(f"Error: Category path not found. <@759167810814476319>")
        return

    results = [f for f in os.listdir(category_path) if query.lower() in f.lower()]

    if not results:
        await ctx.send("nothing was found (probably because you spelt it wongly)")
        return

    # Limit to 9 results
    overflow = False
    if len(results) > 9:
        results = random.sample(results, 9)
        overflow = True

    message_text = "**Search results:**\n" + "\n".join(f"{emojis[i]} {result}" for i, result in enumerate(results))
    if overflow:
        message_text += "\n\n-# too many results, try being a little more specific"

    msg = await ctx.send(message_text)
    result_cache[msg.id] = results

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
        refill_queue(target_size=5)

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
    global restart  # FIX: was setting a local variable before, never actually triggered
    await ctx.send("Bot will restart after this song finishes to apply code updates.")
    restart = True


bot.run(os.getenv("BOT_TOKEN"))