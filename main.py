import os
import discord
from discord.ext import commands, tasks
import aiohttp # for async operations
from datetime import datetime, timedelta, UTC 
from dotenv import load_dotenv
from flask import Flask # dirty fix
from threading import Thread # dirty fix
import pytz
import json

# loads env variables
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
ACTIVE_CH_ID = None

# Persistent storage for ACTIVE_CH_ID
ACTIVE_CH_FILE = "active_channel.json"


# ---------dirty fix-------------
app = Flask("")
@app.route("/")
def home():
    return "Bot is running!"

def run_web():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.start()
# ---------------------------------


# --------Config-----------
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(
    command_prefix='/',
    heartbeat_timeout=150.0, # because we are hosting this on an ass web-service
    intents=intents
        )


# ---------Setup----------
@bot.event
async def on_ready():
    load_active_channel()
    await bot.tree.sync()
    custom_status = discord.CustomActivity(name="Watching over Upcoming CTF's!")
    await bot.change_presence(status=discord.Status.online, activity=custom_status)
    print(f"bot logged in.")

    # STARTING!!!
    weekly_updates.start()

# -----------functions------------
def load_active_channel():
    global ACTIVE_CH_ID
    try:
        with open(ACTIVE_CH_FILE, "r") as f:
            data = json.load(f)
            ACTIVE_CH_ID = data.get("channel_id")
    except Exception:
        ACTIVE_CH_ID = None

def save_active_channel():
    with open(ACTIVE_CH_FILE, "w") as f:
        json.dump({"channel_id": ACTIVE_CH_ID}, f)
        
async def fetch_events(days: int):
    now = int(datetime.now().replace(tzinfo=UTC).timestamp())
    future = int((datetime.now().replace(tzinfo=UTC) + timedelta(days=int(days))).timestamp())
    url = f"https://ctftime.org/api/v1/events/?limit=100&start={now}&finish={future}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                if r.status != 200:
                    print(f"Failed to fetch events: {r.status}")
                    return []
                return await r.json()
    except Exception as e:
        print(f"Error fetching events: {e}")
        return []

async def instant_updates(days: int):
    ctfs = await fetch_events(days)
    if not ctfs:
        return discord.Embed(title="No CTFs found.", color=discord.Color.red())
    
    message = discord.Embed(title=f"CTF's in the Next {days} Days", color=discord.Color.purple())

    for i, ctf in enumerate(ctfs, 1):
        name = ctf['title']
        url_ctf = ctf['ctftime_url']
        org = ctf['organizers'][0]['name']
        start = ctf['start'].split('T')[0]
        end = ctf['finish'].split('T')[0]
        onsite = "On-site" if ctf.get('onsite') else 'Online'

        summary = f"‣ **Organized by**: {org}\n‣ **Type**: {onsite}\n‣ **Start**: {start} | **End**: {end}\n‣ [View Event]({url_ctf})"
        message.add_field(name=f"{i}. {name}", value=summary, inline=False)
    
    return message

# Ok ok , this is not daily, but who cares.
@tasks.loop(minutes=1)
async def weekly_updates():
    if not ACTIVE_CH_ID:
        return

    now_ist = datetime.now(pytz.timezone("Asia/Kolkata"))
    
    if now_ist.weekday() == 6 and now_ist.hour == 23 and now_ist.minute == 0:
        channel = bot.get_channel(ACTIVE_CH_ID)
        if not channel:
            return

        ctfs = await fetch_events(days=7)
        if ctfs:
            for ctf in ctfs:
                name = ctf['title']
                org = ctf['organizers'][0]['name']
                url_ctf = ctf['ctftime_url']
                start = ctf['start'].split('T')[0]
                end = ctf['finish'].split('T')[0]
                logo = ctf.get('logo') or None
                onsite = "On-site" if ctf.get('onsite') else 'Online'
                description = ctf['description']

                embed = discord.Embed(title=name, url=url_ctf, description=description)
                embed.add_field(name='Organized by', value=org, inline=True)
                embed.add_field(name='Type', value=onsite, inline=True)
                embed.add_field(name='Starts on', value=start, inline=True)
                embed.add_field(name='Ends on', value=end, inline=True)
                if logo:
                    embed.set_thumbnail(url=logo)

                await channel.send(embed=embed)


# -----------Commands----------
@bot.hybrid_command(name='active', description='Set this channel for CTF updates.')
@commands.has_permissions(administrator=True)
async def active(ctx):
    global ACTIVE_CH_ID
    ACTIVE_CH_ID = ctx.channel.id
    save_active_channel()
    await ctx.send(f"✅ This channel is now set for updates.")

@bot.hybrid_command(name='unsetactive', description='Unset the active channel for CTF updates.')
@commands.has_permissions(administrator=True)
async def unsetactive(ctx):
    global ACTIVE_CH_ID
    ACTIVE_CH_ID = None
    save_active_channel()
    await ctx.send("❌ CTF updates channel unset.")

@bot.hybrid_command(name='monthly', description='ctf events in next 30 days.')
async def ctf_monthly(ctx, days=30):
    embed = await instant_updates(days)
    await ctx.send(embed=embed)

@bot.hybrid_command(name='ctf', description='Get CTF events in the next N days.')
async def ctf_days(ctx, days: int = 7):
    """Send CTF events for the next N days (user input)."""
    if days < 1 or days > 60:
        await ctx.send("Please enter a number of days between 1 and 60.")
        return
    embed = await instant_updates(days)
    await ctx.send(embed=embed)


# dirty fix
keep_alive()

if __name__ == "__main__":
    bot.run(TOKEN)
