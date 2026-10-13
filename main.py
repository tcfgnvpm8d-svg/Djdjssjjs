
import os
import discord

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
    if message.author.bot or not message.guild:
        return

    original_text = message.content

    # Only process messages containing a selected swear word
    if not any(word in original_text.lower() for word in BAD_WORDS):
        return

    # Mention the person whose message is being replied to
    if message.reference and message.reference.message_id:
        try:
            replied_message = message.reference.resolved

            if replied_message is None:
                replied_message = await message.channel.fetch_message(
                    message.reference.message_id
                )

            if replied_message:
                mention = replied_message.author.mention
                original_text = f"{mention} {original_text}"

        except (
            discord.NotFound,
            discord.Forbidden,
            discord.HTTPException
        ):
            pass

    webhook = None

    try:
        username = message.author.display_name
        avatar_url = message.author.display_avatar.url
        avatar_bytes = await message.author.display_avatar.read()

        # Create a webhook using the original author's name and avatar
        webhook = await message.channel.create_webhook(
            name=username,
            avatar=avatar_bytes,
            reason="Filtered message repost"
        )

        # Delete the original message
        await message.delete()

        # Repost under the author's name and profile picture
        await webhook.send(
            content=original_text,
            username=username,
            avatar_url=avatar_url,
            allowed_mentions=discord.AllowedMentions(
                users=True
            )
        )

        print(f"Reposted message from {username}")

    except discord.Forbidden:
        print("Missing Manage Messages or Manage Webhooks permission.")

    except discord.HTTPException as error:
        print(f"Discord API error: {error}")

    finally:
        if webhook is not None:
            try:
                await webhook.delete()
            except discord.HTTPException as error:
                print(f"Webhook cleanup error: {error}")


bot.run(TOKEN)
