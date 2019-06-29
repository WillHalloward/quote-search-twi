import json
from itertools import cycle

import discord
from discord.ext import commands, tasks

import createSearchableData
import patreon_poll
import prediction
import search
import secrets

bot = commands.Bot(
    command_prefix='!',
    description="The wandering inn bot",
    case_insensitive=True, )
bot.remove_command("help")

status = cycle(["Killing the mages of Wistram", "Cleaning up a mess", ""])
with open("api_url.json", 'r') as f:
    json_data = json.load(f)

@bot.event
async def on_ready():
    status_loop.start()
    if json_data['poll_update']:
        auto_update_poll.start()
    # poll_end.start()
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@tasks.loop(seconds=10)
async def poll_end():
    print("10")


@tasks.loop(minutes=10)
async def auto_update_poll():
    try:
        with open("api_url.json", 'r') as f:
            file_json = json.load(f)
    except OSError.filename:
        return
    msg_cha = bot.get_channel(file_json['ch_poll_id'])
    msg = await msg_cha.fetch_message(file_json['poll_id'])
    await msg.edit(embed=await patreon_poll.p_poll())


@tasks.loop(seconds=10)
async def status_loop():
    await bot.change_presence(activity=discord.Game(next(status)))

@bot.command(aliases=["u"])
async def updatepoll(ctx):
    try:
        with open("api_url.json", 'r') as f:
            file_json = json.load(f)
    except OSError.filename:
        return
    msg_cha = bot.get_channel(file_json['ch_poll_id'])
    msg = await msg_cha.fetch_message(file_json['poll_id'])
    await msg.edit(embed=await patreon_poll.p_poll())


@bot.command(aliases=["tp"])
async def togglepoll(ctx):
    if json_data["poll_update"]:
        with open("api_url.json", "w") as e:
            json_data.update({"poll_update": False})
            json.dump(json_data, e)
            auto_update_poll.start()
            await ctx.send("Poll will no longer auto update every 10 min")
    else:
        with open("api_url.json", "w") as e:
            json_data.update({"poll_update": True})
            json.dump(json_data, e)
            auto_update_poll.stop()
            await ctx.send("Poll will now auto update every 10 min")

@bot.command()
async def ping(ctx):
    latency = int(bot.latency * 100)
    await ctx.send("{} ms".format(latency))


@bot.command(aliases=["e"])
@commands.is_owner()
async def evaluate(ctx, ev):
    await ctx.send(eval(ev))


@bot.command(aliases=["f"])
async def find(ctx, query):
    await search.search(query, ctx)


@bot.command(aliases=["wc"])
async def wordcount(ctx, chapter):
    await search.word_count(chapter, ctx)


@bot.command()
@commands.is_owner()
async def refreshUrl(ctx):
    createSearchableData.createSearchableDatafromUrl()
    await ctx.send("@everyone Done")


@bot.command()
@commands.is_owner()
async def refreshIndex(ctx):
    createSearchableData.createSearchableData("TWI")
    await ctx.send("@everyone Done")


@bot.command(aliases=["p"])
async def poll(ctx):
    await ctx.send(embed=await patreon_poll.p_poll(ctx))


@bot.command()
async def bet(ctx, time, words):
    await prediction.bet(ctx, time, words)


@bot.command(aliases=["avatar"])
async def av(ctx):
    embed = discord.Embed(title="Avatar", color=discord.Color(0x3cd63d))
    embed.set_image(url=ctx.author.avatar_url)
    await ctx.send(embed=embed)


@bot.command(aliases=["sp"])
@commands.is_owner()
async def setpoll(ctx):
    if await patreon_poll.set_poll(ctx):
        message = await ctx.send(embed=await patreon_poll.p_poll())
        await message.pin()
        with open("api_url.json", 'r') as f:
            file_json = json.load(f)
        try:
            ch = bot.get_channel(file_json['ch_poll_id'])
            msg = await ch.fetch_message(file_json['poll_id'])
            if msg.pinned:
                await msg.unpin()
        except KeyError:
            print("no previous poll")
        file_json.update({"poll_id": message.id})
        file_json.update({"ch_poll_id": message.channel.id})
        file_json.update({"poll_update": True})
        with open("api_url.json", "w+") as d:
            json.dump(file_json, d)
    else:
        await ctx.send("No poll found")


@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Help", color=discord.Color(0x3cd63d), description="List of commands")
    embed.add_field(name="!find", value="Searches in The Wandering Inn after the text given.\n"
                                        "**Usage:** !find [Search text]\n"
                                        "**Ex:** !find: \"the dragon roared\", !find magnolia.\n"
                                        "**Note:** searches longer than 1 word need to be surrounded in \"\"")
    embed.add_field(name="!wordcount", value="Gets the wordcount of the chapter given.\n"
                                             "Usage: !wordcount [title]\n"
                                             "**Ex:** !wordcount 6.25, !wordcount \"1.06 D\"\n"
                                             "**Note:** searches longer than 1 word need to be surrounded in \"\"")
    embed.add_field(name="!poll", value="Posts the current tally of the patreon poll.")
    embed.add_field(name="!setPoll", value="Retrieves and pins the latest poll from patreon")
    embed.add_field(name="!updatePoll", value="Updates the pinned poll created via !setpoll")
    embed.add_field(name="!bet", value="Stake a bet on the time and word count of the next chapter.\n"
                                       "**Usage:** !bet [time] [wordcount]\n"
                                       "**Ex:** !bet 1h 1k, !bet \"2h 30m\" 17324")
    embed.add_field(name="!av", value="Posts the full version of your current avatar")
    await ctx.send(embed=embed)


bot.run(secrets.bot_token)
# TODO Write a better help list for !find that explains date: and title:, sub '' and more.
