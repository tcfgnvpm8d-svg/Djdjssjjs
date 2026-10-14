
import os
import re
import discord
import aiohttp

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

    # Only process messages containing a filtered word
    if not BAD_WORDS_PATTERN.search(original_text):
        return

    webhook = None
    files = []
    attachment_links = []

    try:
        username = message.author.display_name
        avatar_url = message.author.display_avatar.url

        # Add a mention of the person being replied to
        if message.reference and message.reference.message_id:
            try:
                replied_message = message.reference.resolved

                if replied_message is None:
                    replied_message = await message.channel.fetch_message(
                        message.reference.message_id
                    )

                if replied_message:
                    original_text = (
                        f"{replied_message.author.mention} "
                        f"{original_text}"
                    )

            except discord.HTTPException as error:
                print(f"Could not fetch reply: {error}")

        # Download each attachment before deleting the original
        for attachment in message.attachments:
            try:
                data = await attachment.read()
                files.append(
                    discord.File(
                        fp=__import__("io").BytesIO(data),
                        filename=attachment.filename
                    )
                )
            except (discord.HTTPException, discord.NotFound):
                attachment_links.append(attachment.url)

        # Include embeds such as linked videos where possible
        # Discord attachments are handled above.
        if attachment_links:
            original_text += "\n\nAttachment links:\n" + "\n".join(
                attachment_links
            )

        # Create a webhook using the author's profile
        avatar_bytes = await message.author.display_avatar.read()

        webhook = await message.channel.create_webhook(
            name=username,
            avatar=avatar_bytes,
            reason="Filtered message repost"
        )

        # Delete original only after downloading its attachments
        await message.delete()

        # Send content and media via the webhook
        await webhook.send(
            content=original_text or None,
            username=username,
            avatar_url=avatar_url,
            files=files,
            allowed_mentions=discord.AllowedMentions(users=True)
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
        # Close downloaded files
        for file in files:
            file.close()

        # Remove temporary webhook
        if webhook is not None:
            try:
                await webhook.delete()
            except discord.HTTPException as error:
                print(f"Webhook cleanup error: {error}")


bot.run(TOKEN)
