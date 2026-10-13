
import os
import re
import discord

TOKEN = os.environ["DISCORD_TOKEN"]

BAD_WORDS = [
    # Profanity
    "fuck", "fucking", "fucked", "fucker", "fuckers",
    "shit", "shitty", "bullshit", "horseshit",
    "bitch", "bitches", "bitchy",
    "asshole", "assholes", "arsehole", "arseholes",
    "bastard", "bastards", "cunt", "cunts",
    "motherfucker", "motherfuckers",
    "dick", "dickhead", "dicks",
    "cock", "cocksucker",
    "piss", "pissed", "piss off",
    "damn", "dammit", "goddamn",
    "prick", "pricks", "wanker", "wankers",
    "twat", "twats", "bollocks", "bugger",
    "slut", "sluts", "whore", "whores",
    "skank", "skanks", "dumbass", "jackass",
    "dipshit", "shithead", "dumbfuck", "fuckwit",

    # Discriminatory slurs
    "nigger", "nigga", "faggot", "fag",
    "retard", "retarded", "kike", "spic",
    "chink", "wetback", "tranny",

    # Other insults
    "idiot", "moron"
]

# Match complete words or phrases, ignoring capitalization
BAD_WORDS_PATTERN = re.compile(
    r"(?<!\w)(?:" +
    "|".join(
        re.escape(word).replace(r"\ ", r"\s+")
        for word in sorted(BAD_WORDS, key=len, reverse=True)
    ) +
    r")(?!\w)",
    re.IGNORECASE
)

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)


@bot.event
async def on_ready():
    print(f"Bot online as {bot.user}")


@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    original_text = message.content

    # Check for a whole-word match
    if not BAD_WORDS_PATTERN.search(original_text):
        return

    webhook = None

    try:
        username = message.author.display_name
        avatar_url = message.author.display_avatar.url

        # Mention the person being replied to
        if message.reference and message.reference.message_id:
            try:
                replied_message = message.reference.resolved

                if replied_message is None:
                    replied_message = await message.channel.fetch_message(
                        message.reference.message_id
                    )

                if replied_message:
                    original_text = (
                        f"{replied_message.author.mention} {original_text}"
                    )

            except discord.HTTPException as error:
                print(f"Could not fetch reply: {error}")

        # Get the author's profile picture
        avatar_bytes = await message.author.display_avatar.read()

        # Create a temporary webhook
        webhook = await message.channel.create_webhook(
            name=username,
            avatar=avatar_bytes,
            reason="Filtered message repost"
        )

        # Delete the original message
        await message.delete()

        # Repost through the webhook
        await webhook.send(
            content=original_text,
            username=username,
            avatar_url=avatar_url,
            allowed_mentions=discord.AllowedMentions(
                users=True
            )
        )

        print(f"Webhook repost sent as {username}")

    except discord.Forbidden:
        print(
            "Permission error: the bot needs "
            "Manage Messages and Manage Webhooks."
        )

    except discord.HTTPException as error:
        print(f"Discord API error: {error}")

    finally:
        if webhook is not None:
            try:
                await webhook.delete()
            except discord.HTTPException as error:
                print(f"Webhook cleanup error: {error}")


bot.run(TOKEN)
