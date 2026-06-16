############################################################################
######## CODED BY @paidbycrypto. | https://github.com/myth1caldev ##########
############################################################################

import discord
from discord import app_commands
import json
import random
import string
import time
import datetime
import sys
import psutil
import platform
import os
import asyncio
import io
import aiohttp
from datetime import datetime, timedelta, timezone
from discord.ext import commands, tasks
from discord.ui import Button, View
from collections import defaultdict
from threading import Timer
from discord import Embed, SyncWebhook

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.reactions = True
intents.message_content = True
intents.members = True

start_time = time.time()

bot = commands.Bot(command_prefix=["+", "-"], intents=intents)
bot.remove_command("help")

with open("settings.json", "r") as f:
    settings = json.load(f)

PENDING_FILE = "database/pending.json"
VOUCHES_FILE = "database/vouches.json"
PROFILES_FILE = "database/profiles.json"
DENIED_FILE = "database/denied.json"
MARKED_FILE = "database/marked.json"
DWC_FILE = "database/dwc.json"
BLACKLIST_FILE = "database/blacklist.json"
GUILDS_FILE = "database/guilds.json"
PENDING_CHANNEL_ID = settings["pending_channel"]

VOUCH_LOG_WEBHOOK = settings["vouch_log_webhook"]
BUG_REPORT_WEBHOOK_URL = settings["bug_report_webhook"]
GUILD_LOG_WEBHOOK = settings["guild_log_webhook"]

GLOBAL_FOOTER_TEXT = settings["global_footer_text"]
GLOBAL_THUMBNAIL_URL = settings["global_thumbnail_url"]
MAIN_GUILD_INVITE_URL = settings["main_guild_invite_url"]
GLOBAL_PROJECT_NAME = settings["global_project_name"]

ANNOUNCEMENT_CHANNELS = {
    settings["mark_channel_id"],
    settings["dwc_channel_id"],
    settings["blacklist_channel_id"],
}

cooldowns = {}
warned_users = set()

COOLDOWN_SECONDS = settings["cooldown_seconds"]

COLOR_MAP = {
    "red": discord.Color.red(),
    "blue": discord.Color.blue(),
    "green": discord.Color.green(),
    "yellow": discord.Color.yellow(),
    "black": discord.Color.default(),
    "white": discord.Color.light_grey(),
    "purple": discord.Color.purple(),
    "pink": discord.Color.magenta(),
    "orange": discord.Color.orange(),
    "brown": discord.Color.dark_orange(),
}

BADGE_EMOJIS = {
    "Owner": "<:1_:1393553125763186698> Owner",
    "Management": "<:2_:1393553123141881916> Management",
    "Developer": "<:0_:1393553694309613670> Developer",
    "AuthiX Team": "<:3_:1393553119777914981> AuthiX Team",
    "Donator": "<:13:1393554019703722134> Donator",
    "Bug Hunter": "<:5_:1393553116464681082> Bug Hunter",
    "Booster": "<:67:1504475996290682970> Booster",
    "1k+ Vouches": "<:004:1504476790565896212> 1k+ Vouches",
    "500+ Vouches": "<:003:1504476760157323424> 500+ Vouches",
    "100+ Vouches": "<:002:1504476729450692730> 100+ Vouches",
    "50+ Vouches": "<:001:1504476689357602857> 50+ Vouches",
    "User": "<:12:1393553103785037884> User",
}

BADGE_ORDER = [
    "Owner",
    "Management",
    "Developer",
    "AuthiX Team",
    "Donator",
    "Bug Hunter",
    "Booster",
    "1k+ Vouches",
    "500+ Vouches",
    "100+ Vouches",
    "50+ Vouches",
    "User",
]
BADGES = [
    "Owner",
    "Management",
    "Developer",
    "AuthiX Team",
    "Donator",
    "Bug Hunter",
    "Booster",
    "1k+ Vouches",
    "500+ Vouches",
    "100+ Vouches",
    "50+ Vouches",
    "User",
]


def generate_id():
    return "".join(random.choices(string.digits, k=6))


def load_json(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)


def default_profile(user_id):
    return {str(user_id): {"positive": 0, "negative": 0, "imported": 0, "overall": 0}}


def get_imported_vouches(user_id):
    vouches = load_json(VOUCHES_FILE)

    if user_id not in vouches:
        return 0

    imported_vouches = [
        vouch
        for vouch in vouches[user_id]
        if "Imported Vouch" in vouch["vouch_message"]
    ]

    return len(imported_vouches)


def load_marked():
    if os.path.exists(MARKED_FILE):
        with open(MARKED_FILE, "r") as f:
            return json.load(f)
    return {}


def save_marked(data):
    with open(MARKED_FILE, "w") as f:
        json.dump(data, f, indent=4)


def load_dwc():
    if os.path.exists(DWC_FILE):
        with open(DWC_FILE, "r") as f:
            return json.load(f)
    return {}


def save_dwc(data):
    with open(DWC_FILE, "w") as f:
        json.dump(data, f, indent=4)


def load_blacklist():
    if os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, "r") as f:
            return json.load(f)
    return {}


def save_blacklist(data):
    with open(BLACKLIST_FILE, "w") as f:
        json.dump(data, f, indent=4)


def load_settings():
    with open("settings.json", "r") as file:
        return json.load(file)


@bot.check
async def global_cooldown(ctx):
    user_id = ctx.author.id
    now = time.time()

    expires = cooldowns.get(user_id, 0)

    if now < expires:

        if user_id not in warned_users:
            warned_users.add(user_id)

            try:
                embed = discord.Embed(
                    title=f"{GLOBAL_PROJECT_NAME} | Cooldown Active!",
                    description="> You are currently on cooldown.\n"
                    f"> Please wait `{int(expires - now)}` seconds before using another command.",
                    color=discord.Color.red(),
                )
                embed.set_footer(text=GLOBAL_FOOTER_TEXT)
                await ctx.reply(embed=embed, mention_author=False, delete_after=1.5)
            except:
                pass

        return False

    warned_users.discard(user_id)

    return True


@bot.after_invoke
async def apply_cooldown(ctx):
    cooldowns[ctx.author.id] = time.time() + COOLDOWN_SECONDS


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Command not found!",
            description="> This command could not be found.\n> Please use `+help` to see all available commands.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, mention_author=False, delete_after=1.5)

    if isinstance(error, commands.CheckFailure):
        return

    raise error


@bot.command(name="vouch", aliases=["rep"])
async def vouch(ctx, user: discord.User = None, *, message: str = None):
    prefix = ctx.prefix
    if prefix == "+":
        vouch_type = "+"
    elif prefix == "-":
        vouch_type = "-"
    else:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Vouch Automatically Denied!",
            description=f"> Invalid prefix `{prefix}`. Use `+` for positive vouch or `-` for negative vouch.\n\n"
            "> **Example:** `+rep @user Great service` or `-rep @user Scam`",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=5)
        return

    if not user or not message:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Vouch Automatically Denied!",
            description=f"> You must specify a User and a Vouch Message.\n\n"
            f"> **Usage:** `{prefix}rep @user Your vouch message`",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=3)
        return

    blacklist = load_blacklist()
    if str(user.id) in blacklist or str(ctx.author.id) in blacklist:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Vouch Automatically Denied!",
            description="> Here is a list of possible reasons why this could be happening:\n\n"
            "> 1. The user you are trying to vouch is blacklisted.\n"
            "> 2. You are blacklisted.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=3)
        return

    if user.id == ctx.author.id:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Vouch Automatically Denied!",
            description="> You cannot vouch for yourself.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=3)
        return

    pending = load_json(PENDING_FILE)
    vouch_id = generate_id()
    timestamp = int(ctx.message.created_at.timestamp())
    timestamp_format = f"<t:{timestamp}:F>"

    vouch_data = {
        "id": vouch_id,
        "type": vouch_type,
        "vouched_by": ctx.author.id,
        "vouched_to": str(user.id),
        "message": message,
        "timestamp": timestamp_format,
    }

    pending[vouch_id] = vouch_data
    save_json(PENDING_FILE, pending)

    type_emoji = "Positive" if vouch_type == "+" else "Negative"
    embed = discord.Embed(
        title=f"Vouch #{vouch_id} ({type_emoji})",
        description=f"**Vouch ID:** `#{vouch_id}`\n"
        f"**Type:** {type_emoji}\n"
        f"**Vouch Message:** `{message}`\n\n"
        f"**Vouched By:** {ctx.author.mention} **-** `{ctx.author.id}`\n"
        f"**Vouched To:** {user.mention} **-** `{user.id}`\n\n"
        f"**Vouched At:** {timestamp_format}",
        colour=0xF5F3F2,
    )
    embed.set_footer(text="React with ✅ to approve or ❌ to deny")

    channel = bot.get_channel(PENDING_CHANNEL_ID)
    vouch_message = await channel.send(embed=embed)
    await vouch_message.add_reaction("✅")
    await vouch_message.add_reaction("❌")

    pending[vouch_id]["message_id"] = vouch_message.id
    save_json(PENDING_FILE, pending)

    try:
        await user.send(
            embed=discord.Embed(
                title="Vouch Notification System",
                description=f"You have received a **{type_emoji}** vouch from `{ctx.author.name}`.\nThe ID of this vouch is `{vouch_id}`.",
                color=discord.Color.blue(),
            ).set_footer(text="Created by @paidbycrypto. | AuthiX | discord.gg/AuthiX")
        )
    except discord.Forbidden:
        print(
            f"[AuthiX] [System] Could not DM {user.name}, they may have DMs disabled."
        )

    confirmation_embed = discord.Embed(
        title="Vouch Submitted!",
        description=f"> Your **{type_emoji}** vouch for `{user.name}` has been submitted and is waiting for review.",
        colour=0xF5F3F2,
    )
    confirmation_embed.set_footer(text=GLOBAL_FOOTER_TEXT)
    await ctx.reply(embed=confirmation_embed, delete_after=3)


async def log_vouch_approval(
    vouch_id, approved_by, vouched_for, vouch_message, vouch_type
):
    type_text = "Positive" if vouch_type == "+" else "Negative"
    embed = discord.Embed(
        title=f"Vouch #{vouch_id} Approved! ({type_text})",
        description=f"**Vouch ID:** ```#{vouch_id}```\n"
        f"**Type:** {type_text}\n"
        f"**Vouch Message:** ```{vouch_message}```\n\n"
        f"**Vouched For:** ```{vouched_for}```\n\n"
        f"**Approved By:** ```{approved_by}```",
        color=discord.Color.green(),
    )
    embed.set_footer(text=GLOBAL_FOOTER_TEXT)
    embed.set_thumbnail(url=GLOBAL_THUMBNAIL_URL)
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(VOUCH_LOG_WEBHOOK, session=session)
        await webhook.send(embed=embed)


async def log_vouch_denial(vouch_id, denied_by, deny_reason, vouch_message, vouch_type):
    type_text = "Positive" if vouch_type == "+" else "Negative"
    embed = discord.Embed(
        title=f"Vouch #{vouch_id} Denied! ({type_text})",
        description=f"**Vouch ID:** ```#{vouch_id}```\n"
        f"**Type:** {type_text}\n"
        f"**Vouch Message:** ```{vouch_message}```\n\n"
        f"**Denied By:** ```{denied_by}```\n\n"
        f"**Deny Reason:** ```{deny_reason}```",
        color=discord.Color.red(),
    )
    embed.set_footer(text=GLOBAL_FOOTER_TEXT)
    embed.set_thumbnail(url=GLOBAL_THUMBNAIL_URL)
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(VOUCH_LOG_WEBHOOK, session=session)
        await webhook.send(embed=embed)


class DenyDropdown(discord.ui.View):
    def __init__(self, vouch_id, payload, vouched_user, msg, data):
        super().__init__(timeout=None)
        self.vouch_id = vouch_id
        self.payload = payload
        self.vouched_user = vouched_user
        self.msg = msg
        self.data = data

    @discord.ui.select(
        placeholder="Select a reason for denial...",
        options=[
            discord.SelectOption(
                label="Manual Verification Required",
                value="Manual Verification required, please open a support ticket.",
            ),
            discord.SelectOption(
                label="Specify More Details",
                value="Please specify more details about the product.",
            ),
            discord.SelectOption(
                label="Specify Price And Currency",
                value="Please specify the exact price and currency (€, $, £).",
            ),
            discord.SelectOption(
                label="Free Item Vouch",
                value="Free items or giveaways are not valid for vouching.",
            ),
            discord.SelectOption(
                label="Duplicated Vouch",
                value="We have a reason to believe that this vouch has been duplicated.",
            ),
            discord.SelectOption(
                label="No Reason Provided", value="No Reason Provided."
            ),
        ],
    )
    async def select_callback(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        reason = select.values[0]
        denied = load_json(DENIED_FILE)
        denied[self.vouch_id] = {
            "type": self.data["type"],
            "vouched_by": self.data["vouched_by"],
            "vouched_to": self.data["vouched_to"],
            "vouch_message": self.data["message"],
            "denied_by": self.payload.member.id,
            "reason": reason,
            "timestamp": str(interaction.created_at),
        }
        save_json(DENIED_FILE, denied)

        type_emoji = "Positive" if self.data["type"] == "+" else "Negative"
        try:
            await self.vouched_user.send(
                embed=discord.Embed(
                    title="Vouch Notification System",
                    description=f"Your {type_emoji} vouch with ID `{self.vouch_id}` was denied for reason: `{reason}`",
                    color=discord.Color.red(),
                ).set_footer(
                    text="Created by @paidbycrypto. | AuthiX | discord.gg/AuthiX"
                )
            )
        except discord.Forbidden:
            print(f"[AuthiX] [System] Could not send DM to {self.vouched_user.name}")

        await self.msg.delete()
        print(f"[AuthiX] [Vouch Management] Vouch {self.vouch_id} has been denied!")
        await log_vouch_denial(
            self.vouch_id,
            self.payload.member.name,
            reason,
            self.data["message"],
            self.data["type"],
        )
        self.stop()


@bot.event
async def on_raw_reaction_add(payload):
    if payload.member.bot:
        return

    pending = load_json(PENDING_FILE)
    to_delete = []

    for vouch_id, data in pending.items():
        if data.get("message_id") == payload.message_id:
            vouched_user_id = int(data["vouched_to"])
            vouched_user = await bot.fetch_user(vouched_user_id)
            channel = bot.get_channel(payload.channel_id)
            msg = await channel.fetch_message(payload.message_id)

            if str(payload.emoji) == "✅":
                vouches = load_json(VOUCHES_FILE)
                if str(vouched_user_id) not in vouches:
                    vouches[str(vouched_user_id)] = []

                vouch_entry = {
                    "id": data["id"],
                    "type": data["type"],
                    "vouched_by": data["vouched_by"],
                    "vouch_message": data["message"],
                    "timestamp": data["timestamp"],
                }
                vouches[str(vouched_user_id)].append(vouch_entry)
                save_json(VOUCHES_FILE, vouches)

                type_emoji = "Positive" if data["type"] == "+" else "Negative"
                try:
                    await vouched_user.send(
                        embed=discord.Embed(
                            title="Vouch Notification System",
                            description=f"Your {type_emoji} vouch with ID `{vouch_id}` was approved!",
                            color=discord.Color.green(),
                        ).set_footer(
                            text="Created by @paidbycrypto. | AuthiX | discord.gg/AuthiX"
                        )
                    )
                except discord.Forbidden:
                    print(f"[AuthiX] [System] Could not send DM to {vouched_user.name}")

                to_delete.append(vouch_id)
                await msg.delete()
                print(f"[AuthiX] [Management] Vouch {vouch_id} has been approved!")
                await log_vouch_approval(
                    vouch_id,
                    payload.member.name,
                    vouched_user.name,
                    data["message"],
                    data["type"],
                )

            elif str(payload.emoji) == "❌":
                view = DenyDropdown(vouch_id, payload, vouched_user, msg, data)
                deny_embed = discord.Embed(
                    title=f"Vouch #{vouch_id} Denied",
                    description=f"- {payload.member.mention}, please select a reason for denial.",
                    color=discord.Color.red(),
                )
                await msg.edit(embed=deny_embed, view=view)
                to_delete.append(vouch_id)

    for vouch_id in to_delete:
        del pending[vouch_id]

    save_json(PENDING_FILE, pending)


@bot.command()
async def shop(ctx, shop_url: str):
    profiles = load_json(PROFILES_FILE)

    user_profile = profiles.get(str(ctx.author.id), {})
    user_profile["shop"] = shop_url

    profiles[str(ctx.author.id)] = user_profile
    save_json(PROFILES_FILE, profiles)

    embed = discord.Embed(
        title=f"{GLOBAL_PROJECT_NAME} | Shop URL Updated!",
        description=f"> Your shop link has been updated to:\n\n```{shop_url}```",
        colour=0xF5F3F2,
    )
    embed.set_footer(text=GLOBAL_FOOTER_TEXT)
    embed.set_thumbnail(url=GLOBAL_THUMBNAIL_URL)

    await ctx.reply(embed=embed, delete_after=3)


@bot.command()
async def forum(ctx, forum_url: str):
    profiles = load_json(PROFILES_FILE)

    user_profile = profiles.get(str(ctx.author.id), {})
    user_profile["forum"] = forum_url

    profiles[str(ctx.author.id)] = user_profile
    save_json(PROFILES_FILE, profiles)

    embed = discord.Embed(
        title=f"{GLOBAL_PROJECT_NAME} | Forum URL Updated!",
        description=f"> Your forum link has been updated to:\n\n```{forum_url}```",
        colour=0xF5F3F2,
    )
    embed.set_footer(text=GLOBAL_FOOTER_TEXT)
    embed.set_thumbnail(url=GLOBAL_THUMBNAIL_URL)

    await ctx.reply(embed=embed, delete_after=3)


@bot.command()
async def products(ctx, *, product_string: str):
    product_list = [
        product.strip() for product in product_string.split(",") if product.strip()
    ]

    if not product_list:
        await ctx.send("Please provide at least one product.", delete_after=3)
        return

    profiles = load_json(PROFILES_FILE)

    user_profile = profiles.get(str(ctx.author.id), {})
    user_profile["products"] = product_list

    profiles[str(ctx.author.id)] = user_profile
    save_json(PROFILES_FILE, profiles)

    embed = discord.Embed(
        title=f"{GLOBAL_PROJECT_NAME} | Product List Updated!",
        description=f"> Your products have updated to: \n{', '.join(product_list)}",
        colour=0xF5F3F2,
    )
    embed.set_footer(text=GLOBAL_FOOTER_TEXT)
    embed.set_thumbnail(url=GLOBAL_THUMBNAIL_URL)

    await ctx.reply(embed=embed, delete_after=3)


@bot.command(name="profile", aliases=["p"])
async def profile(ctx, user1: discord.User = None):
    print(f"[AuthiX] [Debug] {ctx.author.id} Executed command: {ctx.message.content}")
    user = user1 or ctx.author
    user_id = str(user.id)

    profiles = load_json(PROFILES_FILE)
    vouches = load_json(VOUCHES_FILE)

    dwc_data = load_json("database/dwc.json")
    marked_data = load_json("database/marked.json")
    blacklist_data = load_json("database/blacklist.json")

    mark_reason = None
    embed_color = discord.Color.blue()
    user_status = None

    if user_id in marked_data or user_id in dwc_data or user_id in blacklist_data:
        user_status = (
            f"**⚠️ User is marked as a scammer!** \n**Reason:** {marked_data.get(user_id, {}).get('reason', 'No reason provided')}"
            if user_id in marked_data
            else (
                f"**⚠️ User is marked as a DWC!** \n**Reason:** {dwc_data.get(user_id, {}).get('reason', 'No reason provided')}"
                if user_id in dwc_data
                else f"**⚠️ User is Blacklisted from AuthiX!** \n**Reason:** {blacklist_data.get(user_id, {}).get('reason', 'No reason provided')}"
            )
        )
        embed_color = discord.Color.red()

    if user_id not in profiles:
        profiles[user_id] = default_profile(user_id)
        save_json(PROFILES_FILE, profiles)

    user_profile = profiles[user_id]

    user_color = user_profile.get("color")
    if user_color and user_id not in marked_data and user_id not in dwc_data:
        embed_color = COLOR_MAP.get(user_color.lower(), discord.Color.blue())

    creation_date = user.created_at.strftime("%b %d %Y")
    imported_vouch_count = get_imported_vouches(user_id)

    user_vouches = vouches.get(user_id, [])

    positive_vouches = 0
    negative_vouches = 0
    for vouch in user_vouches:
        if vouch.get("vouch_message") == "Imported Vouch":
            continue
        vtype = vouch.get("type")
        if vtype == "+":
            positive_vouches += 1
        elif vtype == "-":
            negative_vouches += 1
        else:
            positive_vouches += 1

    total_vouches = positive_vouches + negative_vouches + imported_vouch_count

    badge_order = BADGE_ORDER
    badges = user_profile.get("badges", ["User"])
    sorted_badges = [badge for badge in badge_order if badge in badges]
    badge_lines = [BADGE_EMOJIS.get(badge, "") for badge in sorted_badges]
    badge_str = "\n".join(badge_lines)

    products = user_profile.get("products", ["No products listed"])
    product_lines = "\n".join(products)

    embed = discord.Embed(
        title=f"{user.name}'s Profile",
        description=(
            f"**ID:** {user.id}\n"
            f"**Registration Date:** {creation_date}\n"
            f"**Display Name:** {user}\n"
            f"**Mention:** {user.mention}\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
        ),
        color=embed_color,
    )

    if user_status:
        embed.description = f"**Status:** {user_status}\n" + embed.description

    embed.add_field(
        name="__Vouch Information__",
        value=(
            f"**Overall:** {total_vouches}\n"
            f"**Positive:** {positive_vouches}\n"
            f"**Negative:** {negative_vouches}\n"
            f"**Imported:** {imported_vouch_count}"
        ),
        inline=True,
    )

    embed.add_field(
        name="__Badges__",
        value=(f"{badge_str}" if badge_str else "No badges"),
        inline=True,
    )

    if user_vouches:
        last_5_vouches = user_vouches[-5:]
        last_5_vouches.reverse()
        vouch_lines = []
        for i, v in enumerate(last_5_vouches):
            if v.get("vouch_message") == "Imported Vouch":
                continue
            msg = v["vouch_message"]
            vtype = v.get("type")
            if vtype == "-":
                msg = f"{msg}"
            vouch_lines.append(f"**{i+1}**. {msg}")
        if vouch_lines:
            vouch_details = "\n".join(vouch_lines)
        else:
            vouch_details = "No public vouches yet."
        embed.add_field(
            name="**__Past 5 Comments__**", value=vouch_details, inline=False
        )
    else:
        embed.add_field(
            name="**__Past 5 Comments__**", value="No vouches yet.", inline=False
        )

    embed.add_field(
        name="__Services and Products__",
        value=(
            f"**Shop:** {user_profile.get('shop', 'No shop link set')}\n"
            f"**Forum:** {user_profile.get('forum', 'No forum link set')}\n"
            f"**Products:**\n{product_lines}\n"
        ),
        inline=False,
    )

    embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_footer(text=GLOBAL_FOOTER_TEXT)

    thumbnail_url = user_profile.get("thumbnail")
    if thumbnail_url:
        embed.set_image(url=thumbnail_url)

    message = await ctx.reply(embed=embed, delete_after=30)


MIN_DELAY = 1.5
MAX_DELAY = 3.0
BATCH_SIZE = 5
BATCH_DELAY = 10.0

BADGE_THRESHOLDS = {
    50: "50+ Vouches",
    100: "100+ Vouches",
    500: "500+ Vouches",
    1000: "1k+ Vouches",
}


async def check_and_assign_vouch_badges(user_id: str):
    await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    try:
        profiles = load_json(PROFILES_FILE)
        vouches = load_json(VOUCHES_FILE)

        user_vouches = vouches.get(user_id, [])
        total_vouches = len(user_vouches)

        user_profile = profiles.get(user_id)
        if user_profile is None:
            return

        current_badges = set(user_profile.get("badges", []))
        new_badges = set()

        for threshold, badge_name in BADGE_THRESHOLDS.items():
            if total_vouches >= threshold and badge_name not in current_badges:
                new_badges.add(badge_name)

        if new_badges:
            current_badges.update(new_badges)
            user_profile["badges"] = list(current_badges)
            profiles[user_id] = user_profile
            save_json(PROFILES_FILE, profiles)

            print(f"[Badges] Updated {user_id} with {len(new_badges)} badges")

    except Exception as e:
        print(f"[Badge Error] {user_id}: {str(e)}")
        await asyncio.sleep(BATCH_DELAY)


@bot.event
async def on_vouch_added(user_id: str):
    await check_and_assign_vouch_badges(user_id)
    await asyncio.sleep(random.uniform(MIN_DELAY / 2, MIN_DELAY))


async def periodic_badge_check():
    while True:
        try:
            profiles = load_json(PROFILES_FILE)
            user_ids = list(profiles.keys())

            for i, user_id in enumerate(user_ids, 1):
                await check_and_assign_vouch_badges(user_id)

                if i % BATCH_SIZE == 0:
                    await asyncio.sleep(BATCH_DELAY)

        except Exception as e:
            print(f"[Periodic Check Error] {str(e)}")
            await asyncio.sleep(60)

        await asyncio.sleep(1800)


@bot.command(name="badges")
async def badges(ctx):
    embed = discord.Embed(
        title=f"{GLOBAL_PROJECT_NAME} | Badge List",
        description=(
            f"> Here is a list of all badges!\n\n"
            f"**__{GLOBAL_PROJECT_NAME} Team Badges__**\n"
            f"**<:1_:1393553125763186698> Owner**\n"
            f"**<:2_:1393553123141881916> Management**\n"
            f"**<:0_:1393553694309613670> Developer**\n"
            f"**<:3_:1393553119777914981> AuthiX Team**\n\n"
            f"**__{GLOBAL_PROJECT_NAME} Special Badges__**\n"
            f"**<:13:1393554019703722134> Donator**\n"
            f"**<:5_:1393553116464681082> Bug Hunter**\n"
            f"**<:67:1504475996290682970> Booster**\n\n"
            f"**__{GLOBAL_PROJECT_NAME} Public Badges__**\n"
            f"**<:004:1504476790565896212> 1k+ Vouches**\n"
            f"**<:003:1504476760157323424> 500+ Vouches**\n"
            f"**<:002:1504476729450692730> 100+ Vouches**\n"
            f"**<:001:1504476689357602857> 50+ Vouches**\n"
            f"**<:12:1393553103785037884> User**"
        ),
        colour=0xF5F3F2,
    )

    embed.set_footer(text=GLOBAL_FOOTER_TEXT)
    await ctx.reply(embed=embed)


@bot.command(name="invite")
async def info(ctx):
    embed = discord.Embed(
        title=f"{GLOBAL_PROJECT_NAME} | Links",
        description="> You can find the Discord Bot & Support Server Invite Links bellow!",
        colour=0xF5F3F2,
    )
    embed.set_footer(text=GLOBAL_FOOTER_TEXT)
    embed.set_thumbnail(url=GLOBAL_THUMBNAIL_URL)

    invite_button = Button(
        label="Invite the Bot",
        style=discord.ButtonStyle.link,
        url="https://discord.com/oauth2/authorize?client_id=1401358039478698064&permissions=8&integration_type=0&scope=bot",
    )
    server_button = Button(
        label="Join the Support Server",
        style=discord.ButtonStyle.link,
        url="https://dc.AuthiX.org",
    )

    view = View()
    view.add_item(invite_button)
    view.add_item(server_button)

    await ctx.reply(embed=embed, view=view)


@bot.tree.command(name="setvouches", description="Add vouches to a user.")
@app_commands.choices(
    vouch_type=[
        app_commands.Choice(name="Positive", value="+"),
        app_commands.Choice(name="Negative", value="-"),
    ]
)
async def setvouches(
    interaction: discord.Interaction,
    user: discord.Member,
    vouch_type: app_commands.Choice[str],
    reason: str,
    amount: int,
):
    with open("settings.json", "r") as f:
        settings = json.load(f)

    allowed_role_id = settings.get("allowed_role_id")

    if allowed_role_id not in [role.id for role in interaction.user.roles]:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Permission Denied!",
            description="> You don't have permission to use this command.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    vouches = load_json(VOUCHES_FILE)

    user_id = str(user.id)
    if user_id not in vouches:
        vouches[user_id] = []

    vouch_entries = []

    for _ in range(amount):
        vouch_entry = {
            "type": vouch_type.value,
            "vouched_by": interaction.user.name,
            "vouch_message": reason,
            "timestamp": str(interaction.created_at),
        }

        vouch_entries.append(vouch_entry)

    vouches[user_id].extend(vouch_entries)

    save_json(VOUCHES_FILE, vouches)

    embed = discord.Embed(
        title=f"{GLOBAL_PROJECT_NAME} | Vouch Added!",
        description=(
            f"> Successfully added {amount} "
            f"{'positive' if vouch_type.value == '+' else 'negative'} "
            f"vouches to {user.mention} for reason: {reason}."
        ),
        color=discord.Color.green() if vouch_type.value == "+" else discord.Color.red(),
    )

    embed.set_footer(text=GLOBAL_FOOTER_TEXT)

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.command()
async def reset(ctx, subject: str):
    valid_subjects = ["shop", "forum", "products", "thumb"]

    if subject.lower() not in valid_subjects:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Invalid Subject!",
            description=f"> The subject `{subject}` is not valid. Please use one of the following: `shop`, `forum`, `products`, or `thumb`.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=3)
        return

    profiles = load_json(PROFILES_FILE)
    user_profile = profiles.get(str(ctx.author.id), {})

    if subject.lower() == "shop":
        if "shop" in user_profile:
            del user_profile["shop"]
            profiles[str(ctx.author.id)] = user_profile
            save_json(PROFILES_FILE, profiles)
            embed = discord.Embed(
                title=f"{GLOBAL_PROJECT_NAME} | Shop Link Reset!",
                description=f"> Your shop link has been reset.",
                color=discord.Color.green(),
            )
            embed.set_footer(text=GLOBAL_FOOTER_TEXT)
            await ctx.reply(embed=embed, delete_after=3)
        else:
            embed = discord.Embed(
                title=f"{GLOBAL_PROJECT_NAME} | No Shop Link Found!",
                description=f"> You don't have a shop link to reset.",
                color=discord.Color.red(),
            )
            embed.set_footer(text=GLOBAL_FOOTER_TEXT)
            await ctx.reply(embed=embed, delete_after=3)

    elif subject.lower() == "forum":
        if "forum" in user_profile:
            del user_profile["forum"]
            profiles[str(ctx.author.id)] = user_profile
            save_json(PROFILES_FILE, profiles)
            embed = discord.Embed(
                title=f"{GLOBAL_PROJECT_NAME} | Forum Link Reset!",
                description=f"> Your forum link has been reset.",
                color=discord.Color.green(),
            )
            embed.set_footer(text=GLOBAL_FOOTER_TEXT)
            await ctx.reply(embed=embed, delete_after=3)
        else:
            embed = discord.Embed(
                title=f"{GLOBAL_PROJECT_NAME} | No Forum Link Found!",
                description=f"> You don't have a forum link to reset.",
                color=discord.Color.red(),
            )
            embed.set_footer(text=GLOBAL_FOOTER_TEXT)
            await ctx.reply(embed=embed, delete_after=3)

    elif subject.lower() == "products":
        if "products" in user_profile:
            del user_profile["products"]
            profiles[str(ctx.author.id)] = user_profile
            save_json(PROFILES_FILE, profiles)
            embed = discord.Embed(
                title=f"{GLOBAL_PROJECT_NAME} | Products Reset!",
                description=f"> Your products have been reset.",
                color=discord.Color.green(),
            )
            embed.set_footer(text=GLOBAL_FOOTER_TEXT)
            await ctx.reply(embed=embed, delete_after=3)
        else:
            embed = discord.Embed(
                title=f"{GLOBAL_PROJECT_NAME} | No Products Found!",
                description=f"> You don't have any products to reset.",
                color=discord.Color.red(),
            )
            embed.set_footer(text=GLOBAL_FOOTER_TEXT)
            await ctx.reply(embed=embed, delete_after=3)

    elif subject.lower() == "thumb":
        if "thumbnail" in user_profile:
            del user_profile["thumbnail"]
            profiles[str(ctx.author.id)] = user_profile
            save_json(PROFILES_FILE, profiles)
            embed = discord.Embed(
                title=f"{GLOBAL_PROJECT_NAME} | Thumbnail Reset!",
                description=f"> Your thumbnail has been reset.",
                color=discord.Color.green(),
            )
            embed.set_footer(text=GLOBAL_FOOTER_TEXT)
            await ctx.reply(embed=embed, delete_after=3)
        else:
            embed = discord.Embed(
                title=f"{GLOBAL_PROJECT_NAME} | No Thumbnail Found!",
                description=f"> You don't have a thumbnail to reset.",
                color=discord.Color.red(),
            )
            embed.set_footer(text=GLOBAL_FOOTER_TEXT)
            await ctx.reply(embed=embed, delete_after=3)


@bot.command()
async def status(ctx, vouch_id: str):
    pending = load_json(PENDING_FILE)
    vouches = load_json(VOUCHES_FILE)
    denied = load_json(DENIED_FILE)

    embed = discord.Embed(title=f"Vouch `#{vouch_id}` Status", colour=0xF5F3F2)

    if vouch_id in pending:
        vouch = pending[vouch_id]
        embed.add_field(name="Vouch Status:", value="`Pending`", inline=True)
        embed.add_field(
            name="Vouch Submitted By:",
            value=f"<@{vouch['vouched_by']}> **-** `{vouch['vouched_by']}`",
            inline=False,
        )
        embed.add_field(
            name="Vouch Message:", value=f"```{vouch['message']}```", inline=False
        )

    elif vouch_id in denied:
        vouch = denied[vouch_id]
        embed.add_field(name="Vouch Status:", value="`Denied`", inline=True)
        embed.add_field(
            name="Denied By:",
            value=f"<@{vouch['denied_by']}> **-** `{vouch['denied_by']}`",
            inline=False,
        )
        embed.add_field(name="Deny Reason:", value=f"`{vouch['reason']}`", inline=False)
        embed.add_field(
            name="Vouch Message:", value=f"```{vouch['vouch_message']}```", inline=False
        )

    else:
        found = False
        for vouch in vouches.values():
            if isinstance(vouch, dict) and vouch.get("id") == vouch_id:
                embed.add_field(name="Vouch Status:", value="`Approved`", inline=True)
                embed.add_field(
                    name="Vouch Submitted By:",
                    value=f"<@{vouch['vouched_by']}> **-** `{vouch['vouched_by']}`",
                    inline=False,
                )
                embed.add_field(
                    name="Vouch Message:",
                    value=f"```{vouch['vouch_message']}```",
                    inline=False,
                )
                found = True
                break
            elif isinstance(vouch, list):
                for sub_vouch in vouch:
                    if sub_vouch.get("id") == vouch_id:
                        embed.add_field(
                            name="Vouch Status:", value="`Approved`", inline=True
                        )
                        embed.add_field(
                            name="Vouch Submitted By:",
                            value=f"<@{sub_vouch['vouched_by']}> **-** `{sub_vouch['vouched_by']}`",
                            inline=False,
                        )
                        embed.add_field(
                            name="Vouch Message:",
                            value=f"```{sub_vouch['vouch_message']}```",
                            inline=False,
                        )
                        found = True
                        break
                if found:
                    break

        if not found:
            embed.add_field(
                name="**Error**",
                value="> Vouch ID not found in any database.",
                inline=False,
            )

    embed.set_thumbnail(url=GLOBAL_THUMBNAIL_URL)
    embed.set_footer(text=GLOBAL_FOOTER_TEXT)

    await ctx.reply(embed=embed)


@bot.command()
async def manual(ctx, vouch_id: str):
    settings = load_settings()
    vouch_mod_role_id = settings.get("vouch_mod_role_id")

    if vouch_mod_role_id not in [role.id for role in ctx.author.roles]:
        embed = discord.Embed(
            title="Permission Denied!",
            description="> You do not have permission to use this command.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)

        await ctx.reply(embed=embed, delete_after=3)
        return

    pending = load_json("database/pending.json")
    denied = load_json("database/denied.json")
    vouches = load_json("database/vouches.json")

    vouch = None

    if vouch_id in pending:
        vouch = pending.pop(vouch_id)
        vouch_message = vouch.get("message", "No message provided.")
    elif vouch_id in denied:
        vouch = denied.pop(vouch_id)
        vouch_message = vouch.get("vouch_message", "No message provided.")

    if vouch:
        vouched_by = vouch.get("vouched_by", "Unknown")
        timestamp = vouch.get("timestamp", "No timestamp")
        vouched_user_id = str(vouch.get("vouched_to"))
        vouch_type = vouch.get("type", "+")

        if vouched_user_id not in vouches:
            vouches[vouched_user_id] = []

        vouches[vouched_user_id].append(
            {
                "id": vouch_id,
                "type": vouch_type,
                "vouched_by": vouched_by,
                "vouch_message": vouch_message,
                "timestamp": timestamp,
            }
        )

        save_json("database/pending.json", pending)
        save_json("database/denied.json", denied)
        save_json("database/vouches.json", vouches)

        type_text = "Positive" if vouch_type == "+" else "Negative"

        embed = discord.Embed(
            title=f"Vouch #{vouch_id} successfully approved!",
            description=(
                f"> **Type:** `{type_text}`\n"
                f"> This vouch has been manually approved."
            ),
            color=discord.Color.green() if vouch_type == "+" else discord.Color.red(),
        )

        embed.set_footer(text=GLOBAL_FOOTER_TEXT)

        await ctx.reply(embed=embed, delete_after=3)

        try:
            vouched_user = await bot.fetch_user(int(vouched_user_id))

            dm_embed = discord.Embed(
                title="Vouch Notification System",
                description=(
                    f"Your vouch with the ID: `{vouch_id}` "
                    f"has been manually approved!\n"
                    f"**Type:** `{type_text}`"
                ),
                color=(
                    discord.Color.green() if vouch_type == "+" else discord.Color.red()
                ),
            )

            dm_embed.set_footer(text=GLOBAL_FOOTER_TEXT)

            await vouched_user.send(embed=dm_embed)

        except discord.DiscordException as e:
            await ctx.send(f"Failed to DM the user: {e}")

    else:
        await ctx.reply(f"Vouch #{vouch_id} not found in any database.", delete_after=3)


@bot.tree.command(name="setbadge", description="Assign a badge to a user")
async def setbadge(interaction: discord.Interaction, user: discord.Member, badge: str):
    settings = load_json("settings.json")
    allowed_role_id = settings.get("allowed_role_id")
    allowed_role = discord.utils.get(interaction.guild.roles, id=int(allowed_role_id))

    if allowed_role not in interaction.user.roles:
        embed = discord.Embed(
            title=f"Permission Denied!",
            description="> You do not have permission to use this command.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    valid_badges = BADGES

    if badge not in valid_badges:
        embed = discord.Embed(
            title=f"Invalid Badge!",
            description="> This badge does not exist. Please provide a valid badge name.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    profiles = load_json(PROFILES_FILE)
    user_id = str(user.id)

    if user_id not in profiles:
        profiles[user_id] = default_profile(user_id)
        save_json(PROFILES_FILE, profiles)

    user_profile = profiles[user_id]
    user_profile["badges"] = user_profile.get("badges", ["User"])

    if badge not in user_profile["badges"]:
        user_profile["badges"].append(badge)

    save_json(PROFILES_FILE, profiles)

    embed = discord.Embed(
        title=f"Badge Assigned!",
        description=f"> The badge `{badge}` has been assigned to: <@{user.id}> **-** `({user.id})`.",
        color=discord.Color.green(),
    )
    embed.set_footer(text=GLOBAL_FOOTER_TEXT)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="removebadge", description="Remove a badge from a user")
async def removebadge(
    interaction: discord.Interaction, user: discord.Member, badge: str
):
    settings = load_json("settings.json")
    allowed_role_id = settings.get("allowed_role_id")
    allowed_role = discord.utils.get(interaction.guild.roles, id=int(allowed_role_id))

    if allowed_role not in interaction.user.roles:
        embed = discord.Embed(
            title=f"Permission Denied!",
            description="> You do not have permission to use this command.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    valid_badges = BADGES

    if badge not in valid_badges:
        embed = discord.Embed(
            title=f"Invalid Badge!",
            description="> This badge does not exist. Please provide a valid badge name.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    profiles = load_json(PROFILES_FILE)
    user_id = str(user.id)

    if user_id not in profiles:
        embed = discord.Embed(
            title=f"User Profile Not Found!",
            description=f"> <@{user.id}> **-** `({user.id})` does not have a profile.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    user_profile = profiles[user_id]
    user_badges = user_profile.get("badges", [])

    if badge not in user_badges:
        embed = discord.Embed(
            title=f"Badge Not Found!",
            description=f"> <@{user.id}> **-** `({user.id})` does not have the badge '{badge}'.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    user_badges.remove(badge)
    user_profile["badges"] = user_badges
    save_json(PROFILES_FILE, profiles)

    embed = discord.Embed(
        title=f"Badge Removed!",
        description=f"> The badge `{badge}` has been removed from <@{user.id}> **-** `({user.id})`.",
        color=discord.Color.green(),
    )
    embed.set_footer(text=GLOBAL_FOOTER_TEXT)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.command(name="top")
async def top(ctx):
    try:
        with open("database/vouches.json", "r") as file:
            vouches = json.load(file)

        user_vouch_counts = {
            user_id: len(vouch_list) for user_id, vouch_list in vouches.items()
        }

        top_users = sorted(user_vouch_counts.items(), key=lambda x: x[1], reverse=True)[
            :10
        ]

        if not top_users:
            embed = discord.Embed(
                title=f"{GLOBAL_PROJECT_NAME} | Leaderboard",
                description="No vouches found!",
                colour=0xF5F3F2,
            )
            embed.set_footer(text=GLOBAL_FOOTER_TEXT)
            await ctx.reply(embed=embed)
            return

        leaderboard_text = ""
        for rank, (user_id, vouch_count) in enumerate(top_users, start=1):
            try:
                user = await bot.fetch_user(int(user_id))
                username = user.name
            except:
                username = f"Unknown User ({user_id})"

            leaderboard_text += (
                f"`{rank:02d}` | **`{username}`** | Vouch Count - `{vouch_count}`\n"
            )

        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Leaderboard",
            description=leaderboard_text,
            colour=0xF5F3F2,
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)

        await ctx.reply(embed=embed)

    except Exception as e:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Error",
            description="> An error occurred while loading the vouches. Please try again later.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed)


@bot.command()
async def mark(ctx, user_id: int, *, reason: str):
    settings = load_settings()
    report_staff_role_id = settings.get("report_staff_role_id")
    mark_channel_id = settings.get("mark_channel_id")
    main_guild_id = settings.get("main_guild_id")
    scammer_role_id = settings.get("scammer_role_id")

    if report_staff_role_id not in [role.id for role in ctx.author.roles]:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Permission Error",
            description="> You do not have the required role to use this command.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=1.5)

        return

    marked_data = load_marked()
    user_name = f"User-{user_id}"

    user = await bot.fetch_user(user_id)
    if user:
        user_name = user.name

    marked_data[str(user_id)] = {"name": user_name, "reason": reason}
    save_marked(marked_data)

    mark_channel = bot.get_channel(mark_channel_id)
    if mark_channel:
        message = f"{len(marked_data)}. @{user_name} : {user_id} | {reason}"
        await mark_channel.send(message)

    guild = bot.get_guild(main_guild_id)
    if guild:
        member = guild.get_member(user_id)
        if member:
            scammer_role = guild.get_role(scammer_role_id)
            if scammer_role:
                try:
                    await member.add_roles(
                        scammer_role, reason=f"Marked as scammer: {reason}"
                    )
                except discord.Forbidden:
                    print(
                        "[AuthiX] [Pesmission Error] I do not have permission to assign the scammer role!"
                    )

    embed = discord.Embed(
        title=f"{GLOBAL_PROJECT_NAME} | Successfully Marked",
        description=f"> **{user_name}** (`{user_id}`) has been marked as a **Scammer**\n> **Reason:** `{reason}`",
        color=discord.Color.green(),
    )
    embed.set_footer(text=GLOBAL_FOOTER_TEXT)
    await ctx.reply(embed=embed, delete_after=1.5)


@bot.command()
async def dwc(ctx, user_id: int, *, reason: str):
    settings = load_settings()
    report_staff_role_id = settings.get("report_staff_role_id")
    dwc_channel_id = settings.get("dwc_channel_id")
    main_guild_id = settings.get("main_guild_id")
    dwc_role_id = settings.get("dwc_role_id")

    if report_staff_role_id not in [role.id for role in ctx.author.roles]:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Permission Error",
            description="> You do not have the required role to use this command.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=1.5)
        return

    dwc_data = load_dwc()
    user_name = f"User-{user_id}"

    user = await bot.fetch_user(user_id)
    if user:
        user_name = user.name

    dwc_data[str(user_id)] = {"name": user_name, "reason": reason}
    save_dwc(dwc_data)

    dwc_channel = bot.get_channel(dwc_channel_id)
    if dwc_channel:
        message = f"{len(dwc_data)}. @{user_name} : {user_id} | {reason}"
        await dwc_channel.send(message)

    guild = bot.get_guild(main_guild_id)
    if guild:
        member = guild.get_member(user_id)
        if member:
            dwc_role = guild.get_role(dwc_role_id)
            if dwc_role:
                try:
                    await member.add_roles(dwc_role, reason=f"Marked as DWC: {reason}")
                except discord.Forbidden:
                    print(
                        "[AuthiX] [Pesmission Error] I do not have permission to assign the DWC role!"
                    )

    embed = discord.Embed(
        title=f"{GLOBAL_PROJECT_NAME} | Successfully Marked",
        description=f"> **{user_name}** (`{user_id}`) has been marked as a **DWC**\n> **Reason:** `{reason}`",
        color=discord.Color.green(),
    )
    embed.set_footer(text=GLOBAL_FOOTER_TEXT)
    await ctx.reply(embed=embed, delete_after=1.5)


@bot.command()
async def unmark(ctx, user_id: int):
    settings = load_settings()
    appeal_staff_role_id = settings.get("appeal_staff_role_id")
    mark_channel_id = settings.get("mark_channel_id")
    main_guild_id = settings.get("main_guild_id")
    scammer_role_id = settings.get("scammer_role_id")

    if appeal_staff_role_id not in [role.id for role in ctx.author.roles]:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Permission Error",
            description="> You do not have the required role to use this command.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=1.5)
        return

    marked_data = load_marked()

    if str(user_id) not in marked_data:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Error",
            description="> This user is not marked as a scammer!",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=1.5)
        return

    user_name = marked_data[str(user_id)]["name"]
    reason = marked_data[str(user_id)]["reason"]

    del marked_data[str(user_id)]
    save_marked(marked_data)

    mark_channel = bot.get_channel(mark_channel_id)
    if mark_channel:
        async for message in mark_channel.history(limit=200):
            if (
                message.content
                == f"{len(marked_data)+1}. @{user_name} : {user_id} | {reason}"
            ):
                await message.edit(content=f"~~{message.content}~~")
                break

    guild = bot.get_guild(main_guild_id)
    if guild:
        member = guild.get_member(user_id)
        if member:
            scammer_role = guild.get_role(scammer_role_id)
            if scammer_role:
                try:
                    await member.remove_roles(
                        scammer_role, reason="User unmarked as scammer."
                    )
                except discord.Forbidden:
                    print(
                        "[AuthiX] [Pesmission Error] I do not have permission to remove the SCAMMER role!"
                    )

    embed = discord.Embed(
        title=f"{GLOBAL_PROJECT_NAME} | Successfully Unmarked",
        description=f"> **{user_name}** (`{user_id}`) has been unmarked as a **Scammer**",
        color=discord.Color.green(),
    )
    embed.set_footer(text=GLOBAL_FOOTER_TEXT)
    await ctx.reply(embed=embed, delete_after=1.5)


@bot.command()
async def undwc(ctx, user_id: int):
    settings = load_settings()
    appeal_staff_role_id = settings.get("appeal_staff_role_id")
    dwc_channel_id = settings.get("dwc_channel_id")
    main_guild_id = settings.get("main_guild_id")
    dwc_role_id = settings.get("dwc_role_id")

    if appeal_staff_role_id not in [role.id for role in ctx.author.roles]:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Permission Error",
            description="> You do not have the required role to use this command.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=1.5)
        return

    dwc_data = load_dwc()

    if str(user_id) not in dwc_data:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Error",
            description="> This user is not marked as a DWC!",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=1.5)
        return

    user_name = dwc_data[str(user_id)]["name"]
    reason = dwc_data[str(user_id)]["reason"]

    del dwc_data[str(user_id)]
    save_dwc(dwc_data)

    dwc_channel = bot.get_channel(dwc_channel_id)
    if dwc_channel:
        async for message in dwc_channel.history(limit=200):
            if (
                message.content
                == f"{len(dwc_data) + 1}. @{user_name} : {user_id} | {reason}"
            ):
                await message.edit(content=f"~~{message.content}~~")
                break

    guild = bot.get_guild(main_guild_id)
    if guild:
        member = guild.get_member(user_id)
        if member:
            dwc_role = guild.get_role(dwc_role_id)
            if dwc_role:
                try:
                    await member.remove_roles(dwc_role, reason="User unmarked as DWC.")
                except discord.Forbidden:
                    print(
                        "[AuthiX] [Pesmission Error] I do not have permission to remove the DWC role!"
                    )

    embed = discord.Embed(
        title=f"{GLOBAL_PROJECT_NAME} | Successfully Unmarked",
        description=f"> **{user_name}** (`{user_id}`) has been unmarked as a **DWC**",
        color=discord.Color.green(),
    )
    embed.set_footer(text=GLOBAL_FOOTER_TEXT)
    await ctx.reply(embed=embed, delete_after=1.5)


FULL_OPTIONS = [
    discord.SelectOption(
        label="Main Menu", description="Return to the main help menu."
    ),
    discord.SelectOption(
        label="Profile Related Commands",
        description="Shows all AuthiX Profile Related commands.",
    ),
    discord.SelectOption(
        label="Vouch Related Commands",
        description="Shows all AuthiX Vouch Related commands.",
    ),
    discord.SelectOption(
        label="Other Commands", description="Shows all AuthiX Other commands."
    ),
]


class HelpDropdown(discord.ui.Select):
    def __init__(self, initial_exclude=None):
        if initial_exclude:
            options = [opt for opt in FULL_OPTIONS if opt.label != initial_exclude]
        else:
            options = FULL_OPTIONS.copy()
        super().__init__(placeholder="Select a category...", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]

        new_options = [opt for opt in FULL_OPTIONS if opt.label != selected]
        self.options = new_options

        embed = discord.Embed(colour=0xF5F3F2)
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)

        if selected == "Main Menu":
            command_count = len(interaction.client.commands)
            embed.title = f"{GLOBAL_PROJECT_NAME} | Commands & Information"
            embed.description = (
                f"**<:010:1504608041109291178> Prefix:** `+ | -`\n"
                f"**<:009:1504608010452992020> Total Commands:** `{command_count}`\n\n"
                f"**__Explore {GLOBAL_PROJECT_NAME} Bot & Its powerful features!__**\n"
                f"**- Use the dropdown menu below to navigate through different command categories and discover all available functions.**"
            )
        else:
            explanations = {
                "Profile Related Commands": (
                    "**`+p <user> / +profile <user>`**\n> **View a user's profile and reputation details.**\n\n"
                    "**`+products <product1, product2>`**\n> **Add or update products on your profile.**\n\n"
                    "**`+shop <url>`**\n> **Set your shop/store URL on your profile.**\n\n"
                    "**`+forum <url>`**\n> **Set your forum profile URL.**\n\n"
                    "**`+thumb <thumbnail url>`**\n> **Set a custom thumbnail/banner image.**\n\n"
                    "**`+reset <forum/shop/products/thumb>`**\n> **Reset selected profile information.**\n\n"
                    "**`+color`**\n> **Change your profile embed color.**"
                ),
                "Vouch Related Commands": (
                    "**`+vouch/rep <user> <vouch message>`**\n> **Leave a positive vouch/rep for a user.**\n\n"
                    "**`-vouch/rep <user> <vouch message>`**\n> **Leave a negative vouch/rep for a user.**\n\n"
                    "**`+status <vouch id>`**\n> **Check the status of a submitted vouch.**"
                ),
                "Other Commands": (
                    "**`+stats`**\n> **View bot statistics.**\n\n"
                    "**`+badges`**\n> **View all available badges.**\n\n"
                    "**`+invite`**\n> **Get the bot & support server invite link.**\n\n"
                    "**`+top`**\n> **View leaderboard rankings.**\n\n"
                    "**`+search <product>`**\n> **Search for a product.**\n\n"
                    "**`+storedvouches`**\n> **View all stored vouches.**\n\n"
                    "**`+exportvouches`**\n> **Export your vouches data.**\n\n"
                    "**`+allvouches / +allvouches <user>`**\n> **View all vouches for yourself or another user.**\n\n"
                    "**`+token`**\n> **Generate a profile backup token.**\n\n"
                    "**`+markedcount`**\n> **View the number of marked users.**\n\n"
                    "**`+dwccount`**\n> **View the number of DWC (Deal With Caution) marked users.**\n\n"
                    "**`+blacklistcount`**\n> **View the number of blacklisted users.**\n\n"
                    "**`+uptime`**\n> **Check how long the bot has been online.**\n\n"
                    "**`+hot`**\n> **View the top 5 vouched users in the last 24 hours.**\n\n"
                    "**`+myvouchers`**\n> **View the top 10 users who vouched for you.**"
                ),
            }
            embed.title = selected
            embed.description = explanations[selected]

        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(HelpDropdown(initial_exclude="Main Menu"))

        invite_button = discord.ui.Button(
            label="Invite the Bot",
            style=discord.ButtonStyle.link,
            url="https://discord.com/oauth2/authorize?client_id=1401358039478698064&permissions=8&integration_type=0&scope=bot",
        )
        server_button = discord.ui.Button(
            label="Join the Support Server",
            style=discord.ButtonStyle.link,
            url="https://dc.AuthiX.org",
        )
        self.add_item(invite_button)
        self.add_item(server_button)


@bot.command(name="help")
async def prefix_help(ctx):
    command_count = len(bot.commands)
    embed = discord.Embed(
        title=f"{GLOBAL_PROJECT_NAME} | Commands & Information",
        description=(
            f"**<:010:1504608041109291178> Prefix:** `+ | -`\n"
            f"**<:009:1504608010452992020> Total Commands:** `{command_count}`\n\n"
            f"**__Explore {GLOBAL_PROJECT_NAME} Bot & Its powerful features!__**\n"
            f"**- Use the dropdown menu below to navigate through different command categories and discover all available functions.**"
        ),
        colour=0xF5F3F2,
    )
    embed.set_footer(text=GLOBAL_FOOTER_TEXT)

    await ctx.reply(embed=embed, view=HelpView())


@bot.command(name="search")
async def search(ctx, *, product: str):
    profiles = load_json("database/profiles.json")
    users_with_product = []

    for user_id, user_data in profiles.items():
        if "products" in user_data:
            if any(product.lower() in p.lower() for p in user_data["products"]):
                user = await bot.fetch_user(int(user_id))
                users_with_product.append(user.name)

    if users_with_product:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Search result for `{product}`",
            description=f"```{'\n'.join(users_with_product)}```",
            colour=0xF5F3F2,
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        embed.set_thumbnail(url=GLOBAL_THUMBNAIL_URL)
    else:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Search result for `{product}`",
            description="> No users found with this product.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        embed.set_thumbnail(url=GLOBAL_THUMBNAIL_URL)

    await ctx.reply(embed=embed)


@bot.command()
async def storedvouches(ctx):
    try:
        with open("database/vouches.json", "r") as f:
            vouches_data = json.load(f)
    except FileNotFoundError:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | System Error",
            description="> Vouches database not found!\n> Please contact an administrator.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=2)
        print(f"[AuthiX] [Database] Vouches.json Data file not found!")
        return
    except json.JSONDecodeError:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | System Error",
            description="> Vouches database could not be decoded!\n> Please contact an administrator.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=2)
        print(f"[AuthiX] [Database] Error decoding the vouch data!")
        return

    total_vouches = sum(len(vouches) for vouches in vouches_data.values())

    embed = discord.Embed(
        title=f"{GLOBAL_PROJECT_NAME} | Total Vouches Stored",
        description=f"> There are `{total_vouches}` vouches stored in the AuthiX Database.",
        colour=0xF5F3F2,
    )
    embed.set_footer(text=GLOBAL_FOOTER_TEXT)
    embed.set_thumbnail(url=GLOBAL_THUMBNAIL_URL)
    await ctx.reply(embed=embed)


class sHelpDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="AuthiX Vouch Staff Commands",
                description="Shows all AuthiX Vouch Staff commands.",
            ),
            discord.SelectOption(
                label="AuthiX Report Staff Commands",
                description="Shows all AuthiX Report Staff commands.",
            ),
            discord.SelectOption(
                label="AuthiX Appeal Staff Commands",
                description="Shows all AuthiX Appeal Staff commands.",
            ),
        ]
        super().__init__(placeholder="Select a category...", options=options)

    async def callback(self, interaction: discord.Interaction):
        explanations = {
            "AuthiX Vouch Staff Commands": "\n`+manual <vouchid>`, `+blacklist <user id> <reason>`, `+unblacklist <user id>` ",
            "AuthiX Report Staff Commands": "\n`+mark <user id> <reason>`, `+dwc <user id> <reason>` ",
            "AuthiX Appeal Staff Commands": "\n`+umnark <user id>`, `+undwc <user id>`",
        }
        selected_option = self.values[0]
        await interaction.response.send_message(
            f"**{selected_option}**: {explanations[selected_option]}", ephemeral=True
        )


class sHelpView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(sHelpDropdown())


@bot.command(name="shelp")
async def prefix_help(ctx):
    embed = discord.Embed(
        title=f"{GLOBAL_PROJECT_NAME} | Staff Commands & Information",
        description="> **AuthiX´s** global prefix is `+` & `-`",
        color=0xF5F3F2,
    )
    embed.set_footer(text=GLOBAL_FOOTER_TEXT)
    embed.set_thumbnail(url=GLOBAL_THUMBNAIL_URL)

    await ctx.reply(embed=embed, view=sHelpView())


COLOR_MAP = {
    "red": discord.Color.red(),
    "blue": discord.Color.blue(),
    "green": discord.Color.green(),
    "yellow": discord.Color.yellow(),
    "black": discord.Color.default(),
    "white": discord.Color.light_grey(),
    "purple": discord.Color.purple(),
    "pink": discord.Color.magenta(),
    "orange": discord.Color.orange(),
    "brown": discord.Color.dark_orange(),
}


@bot.command(name="color", description="Change your profile color")
async def color(ctx):
    embed = discord.Embed(
        title=f"{GLOBAL_PROJECT_NAME} | Profile Color Change",
        description="> Click on the color reactions below to select your new profile color!",
        colour=0xF5F3F2,
    )

    embed.set_footer(text=GLOBAL_FOOTER_TEXT)
    embed.set_thumbnail(url=GLOBAL_THUMBNAIL_URL)

    message = await ctx.reply(embed=embed)

    emojis = ["🟥", "🟦", "🟩", "🟨", "⬛", "🤍", "🟪", "💖", "🟧", "🟫"]
    for emoji in emojis:
        await message.add_reaction(emoji)

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in emojis

    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)

        color_choice = None
        if str(reaction.emoji) == "🟥":
            color_choice = "red"
        elif str(reaction.emoji) == "🟦":
            color_choice = "blue"
        elif str(reaction.emoji) == "🟩":
            color_choice = "green"
        elif str(reaction.emoji) == "🟨":
            color_choice = "yellow"
        elif str(reaction.emoji) == "⬛":
            color_choice = "black"
        elif str(reaction.emoji) == "🤍":
            color_choice = "white"
        elif str(reaction.emoji) == "🟪":
            color_choice = "purple"
        elif str(reaction.emoji) == "💖":
            color_choice = "pink"
        elif str(reaction.emoji) == "🟧":
            color_choice = "orange"
        elif str(reaction.emoji) == "🟫":
            color_choice = "brown"

        profiles = load_json("database/profiles.json")
        user_id = str(ctx.author.id)

        if user_id in profiles:
            profiles[user_id]["color"] = color_choice
            save_json("database/profiles.json", profiles)
            embed = discord.Embed(
                title=f"{GLOBAL_PROJECT_NAME} | Profile Color Changed",
                description=f"> Your color has been changed to **{color_choice}**!",
                color=0xF5F3F2,
            )
            embed.set_footer(text=GLOBAL_FOOTER_TEXT)
            embed.set_thumbnail(url=GLOBAL_THUMBNAIL_URL)
            await ctx.reply(embed=embed, delete_after=3)
        else:
            embed = discord.Embed(
                title=f"{GLOBAL_PROJECT_NAME} | System Error",
                description="> I could not find your profile in the database.\n> Please contact an administrator!",
                color=0xF5F3F2,
            )
            embed.set_footer(text=GLOBAL_FOOTER_TEXT)
            embed.set_thumbnail(url=GLOBAL_THUMBNAIL_URL)
            await ctx.reply(embed=embed, delete_after=3)

    except Exception as e:
        await ctx.reply("You did not select a color in time!", delete_after=3)
        print(e)


@bot.command(name="thumb")
async def thumb(ctx, thumbnail_url: str):
    user_id = str(ctx.author.id)

    profiles = load_json(PROFILES_FILE)

    if user_id not in profiles:
        profiles[user_id] = default_profile(user_id)
        save_json(PROFILES_FILE, profiles)

    if not (
        thumbnail_url.startswith(("http", "https"))
        and (
            thumbnail_url.endswith((".png", ".jpg", ".jpeg", ".gif"))
            or "discordapp.net" in thumbnail_url
        )
    ):
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Invalid Image",
            description="> Please provide a valid image URL.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=1.5)
        return

    profiles[user_id]["thumbnail"] = thumbnail_url
    save_json(PROFILES_FILE, profiles)

    embed = discord.Embed(
        title=f"{GLOBAL_PROJECT_NAME} | Thumbnail Changed",
        description="> Your thumbnail has been updated successfully!",
        colour=0xF5F3F2,
    )
    embed.set_footer(text=GLOBAL_FOOTER_TEXT)
    await ctx.reply(embed=embed, delete_after=1.5)


@bot.command()
async def blacklist(ctx, user_id: int, *, reason: str):
    settings = load_settings()
    vouch_mod_role_id = settings.get("vouch_mod_role_id")
    blacklist_channel_id = settings.get("blacklist_channel_id")

    if vouch_mod_role_id not in [role.id for role in ctx.author.roles]:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Permission Error",
            description="> You do not have the required role to use this command.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=1.5)
        return

    blacklist_data = load_blacklist()
    user_name = f"User-{user_id}"

    user = await bot.fetch_user(user_id)
    if user:
        user_name = user.name

    blacklist_data[str(user_id)] = {"name": user_name, "reason": reason}
    save_blacklist(blacklist_data)

    blacklist_channel = bot.get_channel(blacklist_channel_id)
    if blacklist_channel:
        message = f"{len(blacklist_data)}. @{user_name} : {user_id} | {reason}"
        await blacklist_channel.send(message)

    embed = discord.Embed(
        title=f"{GLOBAL_PROJECT_NAME} | Successfully Blacklisted",
        description=f"> **{user_name}** (`{user_id}`) has been Blacklisted\n> **Reason:** `{reason}`",
        color=discord.Color.green(),
    )
    embed.set_footer(text=GLOBAL_FOOTER_TEXT)
    await ctx.reply(embed=embed, delete_after=1.5)


@bot.command()
async def unblacklist(ctx, user_id: int):
    settings = load_settings()
    vouch_mod_role_id = settings.get("vouch_mod_role_id")

    blacklist_channel_id = settings.get("blacklist_channel_id")

    if vouch_mod_role_id not in [role.id for role in ctx.author.roles]:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Permission Error",
            description="> You do not have the required role to use this command.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=1.5)
        return

    blacklist_data = load_blacklist()

    if str(user_id) not in blacklist_data:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Error",
            description="> This user is not marked as a scammer!",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=1.5)
        return

    user_name = blacklist_data[str(user_id)]["name"]
    reason = blacklist_data[str(user_id)]["reason"]

    del blacklist_data[str(user_id)]
    save_blacklist(blacklist_data)

    blacklist_channel = bot.get_channel(blacklist_channel_id)
    if blacklist_channel:
        async for message in blacklist_channel.history(limit=200):
            if (
                message.content
                == f"{len(blacklist_data) + 1}. @{user_name} : {user_id} | {reason}"
            ):
                await message.edit(content=f"~~{message.content}~~")
                break

    embed = discord.Embed(
        title=f"{GLOBAL_PROJECT_NAME} | Successfully Unblacklisted",
        description=f"> **{user_name}** (`{user_id}`) has been removed from the Blacklist",
        color=discord.Color.green(),
    )
    embed.set_footer(text=GLOBAL_FOOTER_TEXT)
    await ctx.reply(embed=embed, delete_after=1.5)


@bot.command(name="restart")
async def restart(ctx):
    allowed_role_id = settings.get("allowed_role_id")

    if allowed_role_id not in [role.id for role in ctx.author.roles]:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Permission Error",
            description=f"> You do not have the required role to use this command.",
            colour=0xF5F3F2,
        )
        embed.set_thumbnail(url=GLOBAL_THUMBNAIL_URL)
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        return await ctx.reply(embed=embed, delete_after=1.5)

    def make_bar(percent):
        blocks = int(percent / 10)
        return "█" * blocks + "░" * (10 - blocks)

    embed = discord.Embed(
        title=f"{GLOBAL_PROJECT_NAME} | Bot Restarting",
        description=f"> The bot is restarting.\n> Please wait while it restarts.\n\n{make_bar(25)} 25%",
        color=discord.Color.orange(),
    )
    embed.set_thumbnail(url=GLOBAL_THUMBNAIL_URL)
    embed.set_footer(text=GLOBAL_FOOTER_TEXT)

    msg = await ctx.reply(embed=embed)

    for p in (50, 75, 100):
        await asyncio.sleep(0.7)
        embed.description = f"> The bot is restarting.\n> Please wait while it restarts.\n\n{make_bar(p)} {p}%"
        await msg.edit(embed=embed)

    with open("database/restart.json", "w") as f:
        json.dump({"channel_id": ctx.channel.id, "message_id": msg.id}, f)

    os.execv(sys.executable, [sys.executable] + sys.argv)


@bot.command()
async def rmvouch(ctx, vouch_id: str):
    settings = load_settings()
    vouch_mod_role_id = settings.get("vouch_mod_role_id")

    if vouch_mod_role_id not in [role.id for role in ctx.author.roles]:
        await ctx.send("You do not have permission to use this command.")
        return

    vouches = load_json("database/vouches.json")

    vouch_removed = False
    for user_id, vouch_list in vouches.items():
        for vouch in vouch_list:
            print(f"Checking vouch: {vouch}")

            if "id" in vouch and vouch["id"] == vouch_id:
                vouch_list.remove(vouch)
                vouch_removed = True
                break
        if vouch_removed:
            break

    if vouch_removed:
        save_json("database/vouches.json", vouches)
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Vouch Removed",
            description=f"> Vouch with ID `{vouch_id}` has been successfully removed from the database.",
            color=discord.Color.green(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=3)
    else:
        await ctx.send(f"Vouch with ID {vouch_id} not found in the vouches database.")


@bot.command(name="exportvouches")
async def export_vouches(ctx, user: discord.User = None):
    user = ctx.author
    user_id = str(user.id)

    vouches = load_json(VOUCHES_FILE)

    if user_id not in vouches or not vouches[user_id]:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | No Vouches Found",
            description="> You have no vouches to export.",
            colour=0xF5F3F2,
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=3)
        return

    user_vouches = {user_id: vouches[user_id]}

    vouch_data_json = json.dumps(user_vouches, indent=4)

    vouch_file = io.StringIO(vouch_data_json)
    vouch_file.seek(0)

    try:
        await user.send(file=discord.File(vouch_file, f"{user.id}-vouches.json"))
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Vouches Exported",
            description="> I sent you your vouches in DMs!",
            colour=0xF5F3F2,
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=3)
    except discord.Forbidden:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Error",
            description="> Could not send you your vouches.\n> Please make sure your DMs are open.",
            colour=0xF5F3F2,
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=3)


ALLOWED_ROLE_ID = int(settings.get("allowed_role_id", 0))


@bot.tree.command(
    name="transfer", description="Transfer vouches from one user to another"
)
async def transfer_vouches(
    interaction: discord.Interaction, from_user: discord.User, to_user: discord.User
):
    if ALLOWED_ROLE_ID not in [role.id for role in interaction.user.roles]:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Permission Error",
            description="> You do not have the required role to perform this action.",
            colour=0xF5F3F2,
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    vouches = load_json(VOUCHES_FILE)

    from_user_id = str(from_user.id)
    to_user_id = str(to_user.id)

    if from_user_id not in vouches or not vouches[from_user_id]:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | No Vouches Found",
            description="> The user you are trying to transfer vouches from has no vouches to transfer.",
            colour=0xF5F3F2,
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if to_user_id not in vouches:
        vouches[to_user_id] = []

    vouches[to_user_id].extend(vouches[from_user_id])

    vouches[from_user_id] = []

    with open(VOUCHES_FILE, "w") as f:
        json.dump(vouches, f, indent=4)

    embed = discord.Embed(
        title=f"{GLOBAL_PROJECT_NAME} | Vouches Transferred",
        description=f"> Successfully transferred vouches from {from_user.mention} to {to_user.mention}!",
        colour=0xF5F3F2,
    )
    embed.set_footer(text=GLOBAL_FOOTER_TEXT)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.command()
async def stats(ctx):
    uptime = time.time() - start_time
    days, rem = divmod(uptime, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)

    embed = discord.Embed(
        title=f"{GLOBAL_PROJECT_NAME} | Bot Statistics & Information", color=0xF5F3F2
    )
    embed.set_thumbnail(
        url=bot.user.avatar.url if bot.user.avatar else GLOBAL_THUMBNAIL_URL
    )

    embed.add_field(
        name="<:009:1504608010452992020> Bot Information",
        value=(
            f"**Tag:** `{bot.user.name}#{bot.user.discriminator}`\n"
            f"**ID:** `{bot.user.id}`\n"
            f"**Mention:** {bot.user.mention}"
        ),
        inline=False,
    )

    embed.add_field(
        name="<:008:1504607976529592335> Bot Overview",
        value=(
            f"**Servers:** `{len(bot.guilds)}`\n"
            f"**Users:** `{sum(guild.member_count for guild in bot.guilds)}`"
        ),
        inline=False,
    )

    embed.add_field(
        name="<:010:1504608041109291178> Performance",
        value=(
            f"**Ping:** `{round(bot.latency * 1000)}ms`\n"
            f"**Uptime:** `{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s`\n"
            f"**CPU Cores:** `{psutil.cpu_count(logical=True)}`\n"
            f"**RAM Usage:** `{psutil.virtual_memory().used / (1024 ** 3):.2f}GB` / `{psutil.virtual_memory().total / (1024 ** 3):.2f}GB`\n"
            f"**Discord.py Version:** `{discord.__version__}`"
        ),
        inline=False,
    )

    embed.set_footer(text=GLOBAL_FOOTER_TEXT)

    view = discord.ui.View()
    view.add_item(
        discord.ui.Button(
            label="Invite Bot",
            style=discord.ButtonStyle.link,
            url="https://discord.com/oauth2/authorize?client_id=1401358039478698064&permissions=8&integration_type=0&scope=bot",
        )
    )

    await ctx.reply(embed=embed, view=view)


@bot.event
async def on_message(message):
    if message.author.bot and message.author.id != bot.user.id:
        return

    if message.channel.id in ANNOUNCEMENT_CHANNELS:
        try:
            await message.publish()
            print(
                f"✅ Published message in {message.channel.name} (ID: {message.channel.id})"
            )
        except discord.Forbidden:
            print(
                f"❌ Bot lacks permission to publish messages in {message.channel.name}"
            )
        except discord.HTTPException:
            print(f"❌ Failed to publish message in {message.channel.name}")

    await bot.process_commands(message)


class VouchPaginator(discord.ui.View):
    def __init__(self, ctx, user: discord.User, vouches, per_page=20):
        super().__init__()
        self.ctx = ctx
        self.user = user
        self.user_id = str(user.id)
        self.username = user.name
        self.vouches = list(reversed(vouches))
        self.per_page = per_page
        self.page = 0
        self.max_pages = (len(vouches) - 1) // per_page + 1
        self.update_buttons()

    def _format_vouch_type(self, vouch_type):
        """Convert '+' or '-' to readable text."""
        if vouch_type == "+":
            return "Positive"
        elif vouch_type == "-":
            return "Negative"
        return "Unknown"

    def update_buttons(self):
        self.clear_items()
        if self.page > 0:
            self.add_item(self.PreviousPageButton(self))
        if self.page < self.max_pages - 1:
            self.add_item(self.NextPageButton(self))

    async def update_message(self, interaction: discord.Interaction):
        embed = self.create_embed()
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    def create_embed(self):
        start = self.page * self.per_page
        end = start + self.per_page
        vouch_list = self.vouches[start:end]

        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | All vouches for `{self.username}`",
            color=0xF5F3F2,
        )

        for idx, vouch in enumerate(vouch_list, start=start + 1):
            index_str = f"{idx:02d}" if idx < 10 else str(idx)

            vouch_type_raw = vouch.get("type", "")
            vouch_type_text = self._format_vouch_type(vouch_type_raw)
            vouch_message = vouch.get("vouch_message", "No message provided")

            embed.add_field(
                name="",
                value=f"`{index_str}` | **`{vouch_message}`** | **`{vouch_type_text}`**",
                inline=False,
            )

        embed.set_footer(
            text=f"Page {self.page + 1}/{self.max_pages} | {GLOBAL_FOOTER_TEXT}"
        )
        return embed

    class NextPageButton(discord.ui.Button):
        def __init__(self, paginator):
            super().__init__(label="➡️", style=discord.ButtonStyle.secondary)
            self.paginator = paginator

        async def callback(self, interaction: discord.Interaction):
            self.paginator.page += 1
            await self.paginator.update_message(interaction)

    class PreviousPageButton(discord.ui.Button):
        def __init__(self, paginator):
            super().__init__(label="⬅️", style=discord.ButtonStyle.secondary)
            self.paginator = paginator

        async def callback(self, interaction: discord.Interaction):
            self.paginator.page -= 1
            await self.paginator.update_message(interaction)


@bot.command()
async def allvouches(ctx, user: discord.User = None):
    try:
        with open("database/vouches.json", "r") as f:
            vouches_data = json.load(f)
    except FileNotFoundError:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | System Error",
            description="> Vouches database not found!\n> Please contact an administrator.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=2)
        print(f"[AuthiX] [Database] Vouches.json Data file not found!")
        return

    target_user = user if user else ctx.author
    user_id = str(target_user.id)

    if user_id not in vouches_data or not vouches_data[user_id]:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | No Vouches Found",
            description=f"> Could not find any vouches for {target_user.mention}",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=2)
        return

    vouches = vouches_data[user_id]
    view = VouchPaginator(ctx, target_user, vouches)
    embed = view.create_embed()
    await ctx.reply(embed=embed, view=view, delete_after=300)


def generate_token():
    random_part = "".join(random.choices(string.ascii_letters + string.digits, k=24))
    return f"AuthiX{random_part}"


def save_token(user_id, token):
    path = "database/tokens.json"
    if not os.path.exists("database"):
        os.makedirs("database")

    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append({"user": str(user_id), "token": token})

    with open(path, "w") as f:
        json.dump(data, f, indent=4)


@bot.command()
async def token(ctx):
    await ctx.message.add_reaction("✅")
    await asyncio.sleep(3)

    path = "database/tokens.json"

    if os.path.exists(path):
        with open(path, "r") as f:
            try:
                tokens = json.load(f)
                if not isinstance(tokens, list):
                    tokens = []
            except json.JSONDecodeError:
                tokens = []
    else:
        tokens = []

    user_token = None
    for entry in tokens:
        if entry["user"] == str(ctx.author.id):
            user_token = entry["token"]
            break

    if user_token is None:
        user_token = generate_token()

        tokens.append({"user": str(ctx.author.id), "token": user_token})

        with open(path, "w") as f:
            json.dump(tokens, f, indent=4)

    try:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Token System",
            description=f"> Here is your token.\n> Store it safely and do not share it with anyone!\n\n```{user_token}```",
            colour=0xF5F3F2,
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.author.send(embed=embed)
    except discord.Forbidden:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Error",
            description="> I could not DM you.\n> Please enable Direct Messages from server members.",
            colour=0xF5F3F2,
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=2)


@bot.tree.command(name="tokeninfo", description="Get user ID from a token.")
@app_commands.describe(token="The token to look up")
async def tokeninfo(interaction: discord.Interaction, token: str):
    path = "database/tokens.json"

    if not os.path.exists(path):
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | System Error",
            description="> Token database not found!\n> Please contact an administrator.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    try:
        with open(path, "r") as f:
            tokens = json.load(f)
    except json.JSONDecodeError:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | System Error",
            description="> Token database is corrupted!\n> Please contact an administrator.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    for entry in tokens:
        if entry["token"] == token:
            embed = discord.Embed(
                title=f"{GLOBAL_PROJECT_NAME} | Token Lookup",
                description=f"**Token:** `{entry['token']}`\n"
                f"**User:** <@{entry['user']}> **-** `({entry['user']})`",
                colour=0xF5F3F2,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

    embed = discord.Embed(
        title=f"{GLOBAL_PROJECT_NAME} | Token Lookup",
        description="> No user found for the provided token.",
        color=discord.Color.red(),
    )
    embed.set_footer(text=GLOBAL_FOOTER_TEXT)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(
    name="clearmydms", description="Clear all messages sent by the bot in your DMs."
)
async def clearmydms(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    try:
        dm_channel = await interaction.user.create_dm()
        deleted_count = 0
        start_time = time.time()

        async for message in dm_channel.history(limit=None, oldest_first=True):
            if message.author == bot.user:
                try:
                    await message.delete()
                    deleted_count += 1

                    elapsed_time = time.time() - start_time
                    if elapsed_time < 1:
                        await asyncio.sleep(0.5)
                    else:
                        await asyncio.sleep(0.25)

                except discord.HTTPException as e:
                    if e.code == 429:
                        retry_after = e.retry_after
                        print(f"Rate limited, retrying after {retry_after}s")
                        await asyncio.sleep(retry_after)

        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | DMs Cleared",
            description=f"> Successfully cleared all messages I've sent you.",
            colour=0xF5F3F2,
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await interaction.followup.send(embed=embed, ephemeral=True)

    except Exception as e:
        print(f"Error in /clearmydms: {e}")
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Error",
            description=f"> Couldn't clear DMs due to an error.",
            colour=0xF5F3F2,
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await interaction.followup.send(embed=embed, ephemeral=True)


start_time = time.time()


def format_uptime(seconds):
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    return f"{int(days)}d {int(hours)}h {int(minutes)}m"


@bot.command()
async def uptime(ctx):
    now = time.time()
    uptime_seconds = int(now - start_time)
    uptime_formatted = format_uptime(uptime_seconds)
    restart_timestamp = int(start_time)

    embed = discord.Embed(title=f"{GLOBAL_PROJECT_NAME} | Bot Uptime", color=0xF5F3F2)
    embed.add_field(
        name="<:009:1504608010452992020> Bot Uptime",
        value=f"`{uptime_formatted}`",
        inline=False,
    )
    embed.add_field(
        name="<:010:1504608041109291178> Last Restart",
        value=f"<t:{restart_timestamp}:R>",
        inline=False,
    )

    embed.set_footer(text=GLOBAL_FOOTER_TEXT)
    embed.set_thumbnail(url=GLOBAL_THUMBNAIL_URL)
    await ctx.reply(embed=embed)


@bot.command(name="blacklistcount")
async def blacklist_count(ctx):
    file_path = "database/blacklist.json"

    if not os.path.exists(file_path):
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | System Error",
            description="> Blacklist database not found!\n> Please contact an administrator.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=3)
        return

    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        count = len(data)

        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Blacklist Count",
            description=f"> There are currently **{count}** blacklisted users.",
            color=0xF5F3F2,
        )
        embed.set_footer(text=f"Created by @paidbycrypto. | AuthiX | discord.gg/AuthiX")
        embed.set_thumbnail(url=GLOBAL_THUMBNAIL_URL)
        await ctx.reply(embed=embed)

    except json.JSONDecodeError:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | System Error",
            description="> Error reading the blacklist database!\n> Please contact an administrator.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=3)


@bot.command(name="markedcount")
async def marked_count(ctx):
    file_path = "database/marked.json"

    if not os.path.exists(file_path):
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | System Error",
            description="> Marked database not found!\n> Please contact an administrator.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=3)
        return

    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        count = len(data)

        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Marked Count",
            description=f"> There are currently **{count}** marked users.",
            color=0xF5F3F2,
        )
        embed.set_footer(text=f"Created by @paidbycrypto. | AuthiX | discord.gg/AuthiX")
        embed.set_thumbnail(url=GLOBAL_THUMBNAIL_URL)
        await ctx.reply(embed=embed)

    except json.JSONDecodeError:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | System Error",
            description="> Error reading the marked database!\n> Please contact an administrator.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=3)


@bot.command(name="dwccount")
async def dwc_count(ctx):
    file_path = "database/dwc.json"

    if not os.path.exists(file_path):
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | System Error",
            description="> DWC database not found!\n> Please contact an administrator.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=3)
        return

    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        count = len(data)

        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | DWC Count",
            description=f"> There are currently **{count}** DWC´d users.",
            color=0xF5F3F2,
        )
        embed.set_footer(text=f"Created by @paidbycrypto. | AuthiX | discord.gg/AuthiX")
        embed.set_thumbnail(url=GLOBAL_THUMBNAIL_URL)
        await ctx.reply(embed=embed)

    except json.JSONDecodeError:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | System Error",
            description="> Error reading the DWC database!\n> Please contact an administrator.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=3)


@tasks.loop(hours=1)
async def refresh_vouch_data():
    try:
        with open("database/vouches.json", "r") as f:
            data = json.load(f)

        now = datetime.now(timezone.utc)
        twenty_four_hours_ago = now.timestamp() - (24 * 60 * 60)

        vouch_counts = {}

        for user_id, vouches in data.items():
            recent_vouches = [
                v
                for v in vouches
                if extract_unix_timestamp(v["timestamp"]) > twenty_four_hours_ago
            ]
            count = len(recent_vouches)
            if count > 0:
                vouch_counts[user_id] = count

        bot.vouch_counts = vouch_counts

        print(
            f"[AuthiX] [System] Leaderboard refreshed. {len(vouch_counts)} users have vouches in the last 24 hours."
        )

    except Exception as e:
        print(f"[AuthiX] [System] Error refreshing vouch data: {e}")


@bot.command()
async def hot(ctx):
    try:
        if not hasattr(bot, "vouch_counts"):
            await refresh_vouch_data()

        vouch_counts = bot.vouch_counts
        if not vouch_counts:
            embed = discord.Embed(
                title=f"{GLOBAL_PROJECT_NAME} | Error",
                description="> No vouches in the last 24 Hours.",
                color=discord.Color.red(),
            )
            embed.set_footer(text=GLOBAL_FOOTER_TEXT)
            await ctx.reply(embed=embed, delete_after=2)
            return

        top_users = sorted(vouch_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        leaderboard_text = ""
        for rank, (user_id, vouch_count) in enumerate(top_users, start=1):
            try:
                user = await bot.fetch_user(int(user_id))
                username = user.name
            except:
                username = f"Unknown User ({user_id})"

            leaderboard_text += (
                f"`{rank:02d}` | **`{username}`** | Vouch Count - `{vouch_count}`\n"
            )

        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Top 5 Vouched Users In The Last 24 Hours",
            description=leaderboard_text,
            color=0xF5F3F2,
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)

        await ctx.reply(embed=embed)

    except Exception as e:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | Error",
            description="> An error occurred while loading the vouch data.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=3)


def extract_unix_timestamp(discord_timestamp: str) -> float:
    try:
        if discord_timestamp.startswith("<t:") and ":" in discord_timestamp:
            return float(discord_timestamp.split(":")[1].split(">")[0])
    except:
        return 0.0
    return 0.0


@bot.command(name="myvouchers")
async def myvouchers(ctx):
    user_id = str(ctx.author.id)

    try:
        with open("database/vouches.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | System Error",
            description="> Vouches database could not be decoded!\n> Please contact an administrator.",
            color=discord.Color.red(),
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed, delete_after=2)
        return

    vouches = data.get(user_id, [])
    if not vouches:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | No Vouchers Found",
            description="> You have no vouchers yet.",
            colour=0xF5F3F2,
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed)
        return

    vouch_map = defaultdict(int)
    for v in vouches:
        if v.get("vouch_message") == "Imported Vouch":
            continue

        vouched_by = v.get("vouched_by")
        if vouched_by is None:
            continue
        vouch_map[str(vouched_by)] += 1

    if not vouch_map:
        embed = discord.Embed(
            title=f"{GLOBAL_PROJECT_NAME} | No Vouchers Found",
            description="> You have no vouchers yet.",
            colour=0xF5F3F2,
        )
        embed.set_footer(text=GLOBAL_FOOTER_TEXT)
        await ctx.reply(embed=embed)
        return

    sorted_vouches = sorted(vouch_map.items(), key=lambda item: item[1], reverse=True)[
        :10
    ]

    lines = []
    for idx, (key, count) in enumerate(sorted_vouches, start=1):
        index_str = str(idx).zfill(2)
        if key.isdigit():
            try:
                user = await bot.fetch_user(int(key))
                name = f"{user.name}"
                uid = str(user.id)
            except Exception:
                name = "Unknown User"
                uid = key
        else:
            name = key
            uid = "N/A"

        lines.append(
            f"`{index_str}` | `{name}` | `{uid}` | `{count}` vouch{'es' if count != 1 else ''}"
        )

    embed = discord.Embed(
        title=f"{GLOBAL_PROJECT_NAME} | Top 10 Users Who Vouched For You",
        description="\n".join(lines) if lines else "> No valid vouches found.",
        colour=0xF5F3F2,
    )
    embed.set_footer(text=GLOBAL_FOOTER_TEXT)
    await asyncio.sleep(2.5)
    await ctx.reply(embed=embed)


def load_profiles():
    try:
        with open("database/profiles.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_profiles(profiles):
    with open("database/profiles.json", "w") as f:
        json.dump(profiles, f, indent=4)


def check_and_add_user_badge():
    profiles = load_profiles()

    for user_id, user_data in profiles.items():
        badges = user_data.get("badges", [])

        if "User" not in badges:
            badges.append("User")
            user_data["badges"] = badges

    save_profiles(profiles)
    print("User badge check complete and updates saved.")

    Timer(10800, check_and_add_user_badge).start()


main_guild_id = int(settings["main_guild_id"])
moderator_role_id = int(settings["moderator_team_role_id"])


def load_profiles():
    with open("database/profiles.json", "r", encoding="utf-8") as f:
        return json.load(f)


def save_profiles(profiles):
    with open("database/profiles.json", "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=4)


async def assign_moderator_badge():
    guild = bot.get_guild(main_guild_id)
    if guild is None:
        print("Guild not found.")
        return

    profiles = load_profiles()
    role = guild.get_role(moderator_role_id)
    if role is None:
        print("Moderator role not found.")
        return

    for member in role.members:
        user_id = str(member.id)
        if user_id in profiles:
            user_profile = profiles[user_id]
            badges = user_profile.get("badges", [])
            if badges is None:
                badges = []
            if "AuthiX Team" not in badges:
                badges.append("AuthiX Team")
                user_profile["badges"] = badges
                print(f"Added AuthiX Team badge to {member}")
        else:
            profiles[user_id] = {
                user_id: {
                    "positive": 0,
                    "negative": 0,
                    "imported": 0,
                    "overall": 0,
                    "shop": None,
                    "forum": None,
                    "products": None,
                    "color": None,
                    "badges": None,
                },
                "badges": ["AuthiX Team"],
            }
            print(f"Created new profile for {member} with AuthiX Team badge")

    save_profiles(profiles)
    print("Finished assigning AuthiX Team badges.")


@bot.tree.command(
    name="restore-marked", description="Send all marked users to the selected channel"
)
@app_commands.describe(channel_id="ID of the target channel")
async def restore_marked(interaction: discord.Interaction, channel_id: str):
    member = interaction.user
    allowed_role_id = settings.get("allowed_role_id")
    if not isinstance(member, discord.Member):
        member = await interaction.guild.fetch_member(interaction.user.id)

    if not any(role.id == allowed_role_id for role in member.roles):
        await interaction.response.send_message(
            "You don't have permission to use this command.", ephemeral=True
        )
        return

    try:
        channel = await bot.fetch_channel(int(channel_id))
        if not isinstance(channel, discord.TextChannel):
            raise ValueError("Channel is not a text channel.")
    except Exception as e:
        await interaction.response.send_message(
            f"Invalid channel ID: {e}", ephemeral=True
        )
        return

    try:
        with open("database/marked.json", "r") as f:
            marked_data = json.load(f)
    except Exception as e:
        await interaction.response.send_message(
            f"Failed to load marked.json: {e}", ephemeral=True
        )
        return

    if not marked_data:
        await interaction.response.send_message(
            "No marked users found.", ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"Sending {len(marked_data)} marked users to <#{channel.id}>...", ephemeral=True
    )

    for i, (user_id, info) in enumerate(marked_data.items(), start=1):
        message = f"{i}. @{info.get('name')} : {user_id} | {info.get('reason', 'Unknown Reason')}"
        await asyncio.sleep(0.5)
        await channel.send(message)


@bot.tree.command(
    name="restore-dwcd", description="Send all DWC´d users to the selected channel"
)
@app_commands.describe(channel_id="ID of the target channel")
async def restore_marked(interaction: discord.Interaction, channel_id: str):
    member = interaction.user
    allowed_role_id = settings.get("allowed_role_id")
    if not isinstance(member, discord.Member):
        member = await interaction.guild.fetch_member(interaction.user.id)

    if not any(role.id == allowed_role_id for role in member.roles):
        await interaction.response.send_message(
            "You don't have permission to use this command.", ephemeral=True
        )
        return

    try:
        channel = await bot.fetch_channel(int(channel_id))
        if not isinstance(channel, discord.TextChannel):
            raise ValueError("Channel is not a text channel.")
    except Exception as e:
        await interaction.response.send_message(
            f"Invalid channel ID: {e}", ephemeral=True
        )
        return

    try:
        with open("database/dwc.json", "r") as f:
            dwcd_data = json.load(f)
    except Exception as e:
        await interaction.response.send_message(
            f"Failed to load dwc.json: {e}", ephemeral=True
        )
        return

    if not dwcd_data:
        await interaction.response.send_message("No DWC´d users found.", ephemeral=True)
        return

    await interaction.response.send_message(
        f"Sending {len(dwcd_data)} DWC´d users to <#{channel.id}>...", ephemeral=True
    )

    for i, (user_id, info) in enumerate(dwcd_data.items(), start=1):
        message = f"{i}. @{info.get('name')} : {user_id} | {info.get('reason', 'Unknown Reason')}"
        await asyncio.sleep(0.5)
        await channel.send(message)


@bot.tree.command(
    name="restore-blacklisted",
    description="Send all Blacklisted users to the selected channel",
)
@app_commands.describe(channel_id="ID of the target channel")
async def restore_marked(interaction: discord.Interaction, channel_id: str):
    member = interaction.user
    allowed_role_id = settings.get("allowed_role_id")
    if not isinstance(member, discord.Member):
        member = await interaction.guild.fetch_member(interaction.user.id)

    if not any(role.id == allowed_role_id for role in member.roles):
        await interaction.response.send_message(
            "You don't have permission to use this command.", ephemeral=True
        )
        return

    try:
        channel = await bot.fetch_channel(int(channel_id))
        if not isinstance(channel, discord.TextChannel):
            raise ValueError("Channel is not a text channel.")
    except Exception as e:
        await interaction.response.send_message(
            f"Invalid channel ID: {e}", ephemeral=True
        )
        return

    try:
        with open("database/blacklist.json", "r") as f:
            blacklisted_data = json.load(f)
    except Exception as e:
        await interaction.response.send_message(
            f"Failed to load blacklist.json: {e}", ephemeral=True
        )
        return

    if not blacklisted_data:
        await interaction.response.send_message(
            "No Blacklisted users found.", ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"Sending {len(blacklisted_data)} Blacklisted users to <#{channel.id}>...",
        ephemeral=True,
    )

    for i, (user_id, info) in enumerate(blacklisted_data.items(), start=1):
        message = f"{i}. @{info.get('name')} : {user_id} | {info.get('reason', 'Unknown Reason')}"
        await asyncio.sleep(0.5)
        await channel.send(message)


@bot.tree.command(
    name="bug-report", description="Submit a bug report with optional image."
)
async def bug_report(
    interaction: discord.Interaction,
    title: str,
    description: str,
    image: discord.Attachment = None,
):

    response_embed = discord.Embed(
        title=f"{GLOBAL_PROJECT_NAME} | Bug Report Submitted!",
        description="> Thank you for helping us!",
        colour=0xF5F3F2,
    )
    response_embed.set_footer(text=GLOBAL_FOOTER_TEXT)

    await interaction.response.send_message(embed=response_embed, ephemeral=True)

    embed = discord.Embed(
        title=f"{GLOBAL_PROJECT_NAME} | New Bug Report!",
        description=f"Title: {title}"
        f"\nDescription: {description}"
        f"\nReported by: {interaction.user} ({interaction.user.id})",
        color=discord.Color.red(),
    )
    embed.set_footer(text=GLOBAL_FOOTER_TEXT)

    files = []

    if image and image.content_type and image.content_type.startswith("image/"):
        image_bytes = await image.read()
        file = discord.File(io.BytesIO(image_bytes), filename=image.filename)
        embed.set_image(url=f"attachment://{image.filename}")
        files.append(file)

    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(BUG_REPORT_WEBHOOK_URL, session=session)
        await webhook.send(
            embed=embed,
            username="Bug Reporter",
            avatar_url=bot.user.display_avatar.url,
            files=files,
        )


@bot.event
async def on_guild_join(guild):
    webhook = SyncWebhook.from_url(GUILD_LOG_WEBHOOK)

    embed = discord.Embed(
        title=f"Joined a new guild!",
        description=f"**Server Name:** ```{guild.name}```\n"
        f"**Server ID:** `{guild.id}`\n"
        f"**Member Count:** `{guild.member_count}`\n"
        f"**Owner:** {guild.owner.mention} **-** `({guild.owner_id})`",
        color=discord.Color.green(),
    )
    embed.set_thumbnail(url=GLOBAL_THUMBNAIL_URL)
    embed.set_footer(text=GLOBAL_FOOTER_TEXT)

    webhook.send(embed=embed)


@bot.event
async def on_guild_remove(guild):
    webhook = SyncWebhook.from_url(GUILD_LOG_WEBHOOK)

    embed = discord.Embed(
        title=f"Removed from a guild!",
        description=f"**Server Name:** ```{guild.name}```\n"
        f"**Server ID:** `{guild.id}`\n"
        f"**Member Count:** `{guild.member_count}`\n"
        f"**Owner:** {guild.owner.mention} **-** `({guild.owner_id})`",
        color=discord.Color.red(),
    )
    embed.set_thumbnail(url=GLOBAL_THUMBNAIL_URL)
    embed.set_footer(text=GLOBAL_FOOTER_TEXT)

    webhook.send(embed=embed)


@bot.event
async def on_ready():
    restart_file = "database/restart.json"
    if os.path.exists(restart_file):
        try:
            with open(restart_file, "r") as f:
                data = json.load(f)

            if data:
                channel = bot.get_channel(data["channel_id"])
                if channel:
                    message = await channel.fetch_message(data["message_id"])

                    embed = discord.Embed(
                        title=f"{GLOBAL_PROJECT_NAME} | Bot Restarted",
                        description="> The bot has been successfully restarted.",
                        color=discord.Color.green(),
                    )
                    embed.set_thumbnail(url=GLOBAL_THUMBNAIL_URL)
                    embed.set_footer(text=GLOBAL_FOOTER_TEXT)

                    await message.edit(embed=embed)

                with open(restart_file, "w") as f:
                    f.write("{}")

        except Exception as e:
            print(f"[AuthiX] [Restart] Failed to edit restart message: {e}")

    await bot.tree.sync()
    print(f"[AuthiX] [Discord API] Logged in as {bot.user}")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening, name=MAIN_GUILD_INVITE_URL
        )
    )
    print(f"[AuthiX] [System] Changed the bot presence")
    await asyncio.sleep(1)
    os.system("cls" if os.name == "nt" else "clear")
    print(f" _____     _   _   _ __ __ ")
    print(f"|  _  |_ _| |_| |_|_|  |  |")
    print(f"|     | | |  _|   | |-   -|")
    print(f"|__|__|___|_| |_|_|_|__|__|")
    print(f"")
    print(f"[AuthiX] [System] Bot Successfully Started!")
    await asyncio.sleep(2)
    os.system("cls" if os.name == "nt" else "clear")
    print(f" _____     _   _   _ __ __ ")
    print(f"|  _  |_ _| |_| |_|_|  |  |")
    print(f"|     | | |  _|   | |-   -|")
    print(f"|__|__|___|_| |_|_|_|__|__|")
    print(f"")

    await bot.loop.create_task(periodic_badge_check())
    await refresh_vouch_data.start()
    await check_and_add_user_badge()
    await assign_moderator_badge()


bot.run(settings["token"])
