
import discord
import os

TOKEN = os.environ["DISCORD_TOKEN"]

BAD_WORDS = [
    "fuck",
    "shit",
    "bitch",
    "asshole",
    "bastard",
    "cunt",
    "nigger",
    "nigga",
    "faggot",
    "fag"
]

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f"Bot online: {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    text = message.content.lower()

    if any(word in text for word in BAD_WORDS):
        try:
            original = message.content
            username = message.author.display_name

            await message.delete()

            await message.channel.send(
                f"**{username}:** {original}",
                allowed_mentions=discord.AllowedMentions.none()
            )

        except discord.Forbidden:
            print("Missing permission to delete or send messages.")

bot.run(TOKEN)
