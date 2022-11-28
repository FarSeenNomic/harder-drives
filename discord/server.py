import asyncio
import discord
from multiprocessing import Process, Pipe, freeze_support

intents = discord.Intents.none()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    global write, read
    guild = await client.fetch_guild(762483221379416094)
    channel = await guild.fetch_channel(1040049848520544258)

    history_itor = None
    while True:
        get = read.recv()
        if get == "SEND":
            await channel.send(read.recv())
        elif get == "HIST":
            history_itor = channel.history(limit=None)
        elif get == "WANT":
            try:
                message = await history_itor.__anext__()
                write.send(message.content)
            except:
                write.send("")
        elif get == "ENDR":
            await client.close()
        elif get == "FUA":
            #FUA takes in a single argument to wipe from history
            targets = read.recv()
            async for m in channel.history(limit=128):
                if m.content.split(",")[0] in targets:
                    m.delete()
        elif get == "FLUSH":
            #FLUSH takes in no argument, but makes sure there are no dupes anyway
            foundlist = []
            async for m in channel.history(limit=128):
                if m.content.split(",")[0] in foundlist:
                    await m.delete()
                else:
                    foundlist.append(m.content.split(",")[0])

def callabl(l_write, l_read):
    global write, read
    write = l_write
    read = l_read
    asyncio.get_event_loop().run_until_complete(client.start(open("SECRET", "r").read().rstrip()))



