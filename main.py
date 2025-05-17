import os
import discord
from discord.ext import commands, tasks
import aiohttp # for async operations
from datetime import datetime, timedelta, UTC 
from dotenv import load_dotenv
from flask import Flask # dirty fix
from threading import Thread # dirty fix

# loads env variables
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
ACTIVE_CH_ID = None


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
bot = commands.Bot(
    command_prefix='/',
    heartbeat_timeout=150.0, # because we are hosting this on an ass web-service
    intents=intents
        )


# ---------Setup----------
@bot.event
async def on_ready():
    await bot.tree.sync()
    custom_status = discord.CustomActivity(name="Watching over Upcoming CTF's!")
    await bot.change_presence(status=discord.Status.online, activity=custom_status)
    print(f"bot logged in.")

    # STARTING!!!
    daily_updates.start()


# -----------functions------------
async def fetch_events(days: int):
    now = int(datetime.now(UTC).timestamp())
    future = int((datetime.now(UTC) + timedelta(days=int(days))).timestamp())
    url = f"https://ctftime.org/api/v1/events/?limit=100&start={now}&finish={future}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            return await r.json()

async def instant_updates(days: int):
    ctfs = await fetch_events(days)
    if not ctfs:
        return
    
    message = discord.Embed(title="CTF's in the Next 3 Days", color=discord.Color.purple())

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
@tasks.loop(259200)
async def daily_updates():
    if not ACTIVE_CH_ID:
        return

    channel = bot.get_channel(ACTIVE_CH_ID)
    if not channel:
        return

    ctfs = await fetch_events(days=3)
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

            message = discord.Embed(title=name, url=url_ctf, description=description)
            message.add_field(name='Organized by', value=org, inline=True)
            message.add_field(name='Type', value=onsite, inline=True)
            message.add_field(name='Starts on', value=start, inline=True)
            message.add_field(name='Ends on', value=end, inline=True)
            if logo:
                message.set_thumbnail(url=logo)

            await channel.send(embed=message)


# -----------Commands----------
@bot.hybrid_command(name='active', description='Set this channel for CTF updates.')
@commands.has_permissions(administrator=True)
async def active(ctx):
    global ACTIVE_CH_ID
    ACTIVE_CH_ID = ctx.channel.id
    await ctx.send(f"✅ This channel is now set for updates.")

@bot.hybrid_command(name='weekly', description='ctf events in next 7 days.')
async def ctf_weekly(ctx, days=7):
    embed = await instant_updates(days)
    await ctx.send(embed=embed)

@bot.hybrid_command(name='monthly', description='ctf events in next 30 days.')
async def ctf_monthly(ctx, days=30):
    embed = await instant_updates(days)
    await ctx.send(embed=embed)


# dirty fix
keep_alive()

if __name__ == "__main__":
    bot.run(TOKEN)
