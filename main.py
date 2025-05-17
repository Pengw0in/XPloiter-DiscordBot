import os
import discord, asyncio, aiohttp
from datetime import datetime, timedelta, UTC
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# loads env variables
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
CHANNEL = int(os.getenv('ID'))


intents = discord.Intents.default()
client = discord.Client(intents=intents)

app = Flask("")
@app.route("/")
def home():
    return "Bot is running!"

def run_web():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.start()


async def fetch_events():
    now = int(datetime.now(UTC).timestamp())
    future = int((datetime.now(UTC) + timedelta(days=2)).timestamp())
    url = f"https://ctftime.org/api/v1/events/?limit=100&start={now}&finish={future}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            return await r.json()


async def daily_updates():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL)
    while not client.is_closed():
        ctfs = await fetch_events()
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
        await asyncio.sleep(86400)

@client.event
async def on_ready():
    print(f"we have logged in as {client.user}")


keep_alive()

async def main():
    asyncio.create_task(daily_updates())
    await client.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())



