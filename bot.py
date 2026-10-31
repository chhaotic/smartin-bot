import logging
import os
import random
import re
import sys
from threading import Thread

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask

# --- SERVERUL WEB PENTRU UPTIME ---
app = Flask("")


@app.route("/")
def home():
    return "Smartin is Alive! 🤖"


def run_web_server():
    # Replit folosește portul 8080 pentru servere web
    app.run(host="0.0.0.0", port=8080)


def keep_alive():
    t = Thread(target=run_web_server)
    t.start()


# --- LOGICĂ BOT ---
LINK_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)
WARNING_DELETE_DELAY_SECONDS = 8

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("discord_bot")


class DiscordBot(commands.Bot):

    def __init__(self, guild_id: int | None = None) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
        )
        self.guild_id = guild_id
        # Salvare relații în memorie
        self.marriages = {}
        self.children = {}

    async def setup_hook(self) -> None:
        if self.guild_id is not None:
            guild = discord.Object(id=self.guild_id)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            logger.info("Synced %d commands to dev server", len(synced))
            return

        synced = await self.tree.sync()
        logger.info("Synced %d global commands", len(synced))

    async def on_message(self, message: discord.Message) -> None:
        if message.guild is None or message.author.bot:
            return
        if not LINK_PATTERN.search(message.content):
            return
        if not isinstance(message.author, discord.Member):
            return
        if message.author.guild_permissions.administrator:
            return

        try:
            await message.delete()
            await message.channel.send(
                f"{message.author.mention}, links aren't allowed here.",
                delete_after=WARNING_DELETE_DELAY_SECONDS,
            )
        except Exception:
            pass


# --- BUTOANE INTERACTIVE PENTRU CĂSĂTORIE ȘI ADOPȚIE ---
class RelationshipView(discord.ui.View):

    def __init__(self, target_user: discord.User, callback_func):
        super().__init__(timeout=60)
        self.target_user = target_user
        self.callback_func = callback_func

    async def interaction_check(
        self, interaction: discord.Interaction
    ) -> bool:
        if interaction.user.id != self.target_user.id:
            await interaction.response.send_message(
                "This proposal is not for you! 🛑", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="Accept", style=discord.ButtonStyle.success, emoji="✅"
    )
    async def accept(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.callback_func(interaction, True)
        self.stop()

    @discord.ui.button(
        label="Decline", style=discord.ButtonStyle.danger, emoji="❌"
    )
    async def decline(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.callback_func(interaction, False)
        self.stop()


def create_bot(guild_id: int | None = None) -> DiscordBot:
    bot = DiscordBot(guild_id=guild_id)

    @bot.tree.command(name="ping")
    @app_commands.allowed_contexts(
        guild=True, dms=True, private_channels=True
    )
    @app_commands.allowed_installs(guild=True, user=True)
    async def ping(interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            f"Pong! Latency: {round(bot.latency * 1000)} ms"
        )

    @bot.tree.command(name="hello")
    @app_commands.allowed_contexts(
        guild=True, dms=True, private_channels=True
    )
    @app_commands.allowed_installs(guild=True, user=True)
    async def hello(interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            f"Hello, {interaction.user.mention}! 👋"
        )

    @bot.tree.command(name="kiss")
    @app_commands.allowed_contexts(
        guild=True, dms=True, private_channels=True
    )
    @app_commands.allowed_installs(guild=True, user=True)
    async def kiss(
        interaction: discord.Interaction, user: discord.User
    ) -> None:
        await interaction.response.send_message(
            f"{interaction.user.mention} gives a big kiss to {user.mention}! 💋"
        )

    @bot.tree.command(name="hug")
    @app_commands.allowed_contexts(
        guild=True, dms=True, private_channels=True
    )
    @app_commands.allowed_installs(guild=True, user=True)
    async def hug(
        interaction: discord.Interaction, user: discord.User
    ) -> None:
        await interaction.response.send_message(
            f"{interaction.user.mention} hugs {user.mention} tightly! 🤗"
        )

    @bot.tree.command(name="highfive")
    @app_commands.allowed_contexts(
        guild=True, dms=True, private_channels=True
    )
    @app_commands.allowed_installs(guild=True, user=True)
    async def highfive(
        interaction: discord.Interaction, user: discord.User
    ) -> None:
        await interaction.response.send_message(
            f"{interaction.user.mention} gives a high five to {user.mention}! ✋"
        )

    @bot.tree.command(name="slap")
    @app_commands.allowed_contexts(
        guild=True, dms=True, private_channels=True
    )
    @app_commands.allowed_installs(guild=True, user=True)
    async def slap(
        interaction: discord.Interaction, user: discord.User
    ) -> None:
        await interaction.response.send_message(
            f"{interaction.user.mention} slaps {user.mention}! 🫱💥"
        )

    @bot.tree.command(name="marry")
    @app_commands.allowed_contexts(
        guild=True, dms=True, private_channels=True
    )
    @app_commands.allowed_installs(guild=True, user=True)
    async def marry(
        interaction: discord.Interaction, user: discord.User
    ) -> None:
        if interaction.user.id == user.id:
            await interaction.response.send_message(
                "You can't marry yourself! 🤔", ephemeral=True
            )
            return

        async def marry_callback(inter, accepted):
            if accepted:
                bot.marriages[interaction.user.id] = user.id
                bot.marriages[user.id] = interaction.user.id
                await inter.response.edit_message(
                    content=f"🎉 {interaction.user.mention} and {user.mention} are now married! 💍❤️",
                    view=None,
                )
            else:
                await inter.response.edit_message(
                    content=f"💔 {user.mention} declined the marriage proposal.",
                    view=None,
                )

        view = RelationshipView(user, marry_callback)
        await interaction.response.send_message(
            f"💍 {interaction.user.mention} has proposed to {user.mention}! Do you accept?",
            view=view,
        )

    @bot.tree.command(name="adopt")
    @app_commands.allowed_contexts(
        guild=True, dms=True, private_channels=True
    )
    @app_commands.allowed_installs(guild=True, user=True)
    async def adopt(
        interaction: discord.Interaction, user: discord.User
    ) -> None:
        if interaction.user.id == user.id:
            await interaction.response.send_message(
                "You can't adopt yourself! 🤔", ephemeral=True
            )
            return

        async def adopt_callback(inter, accepted):
            if accepted:
                if interaction.user.id not in bot.children:
                    bot.children[interaction.user.id] = []
                bot.children[interaction.user.id].append(user.id)
                await inter.response.edit_message(
                    content=f"👶🍼 {interaction.user.mention} has successfully adopted {user.mention}! 🎉",
                    view=None,
                )
            else:
                await inter.response.edit_message(
                    content=f"🛑 {user.mention} declined the adoption request.",
                    view=None,
                )

        view = RelationshipView(user, adopt_callback)
        await interaction.response.send_message(
            f"👪 {interaction.user.mention} wants to adopt {user.mention}! Do you accept?",
            view=view,
        )

    @bot.tree.command(name="family_tree")
    @app_commands.allowed_contexts(
        guild=True, dms=True, private_channels=True
    )
    @app_commands.allowed_installs(guild=True, user=True)
    async def family_tree(interaction: discord.Interaction) -> None:
        author_id = interaction.user.id
        spouse_id = bot.marriages.get(author_id)
        children_ids = bot.children.get(author_id, [])

        if not spouse_id and not children_ids:
            await interaction.response.send_message(
                "🌳 You don't have a family tree yet! Use `/marry` or `/adopt` to start one."
            )
            return

        msg = f"🌳 **{interaction.user.name}'s Family Tree** 🌳\n"
        if spouse_id:
            msg += f"💍 **Spouse:** <@{spouse_id}>\n"
        if children_ids:
            msg += "👶 **Children:**\n"
            for c_id in children_ids:
                msg += f"  - <@{c_id}>\n"

        await interaction.response.send_message(msg)

    return bot


def main() -> None:
    load_dotenv()
    token = os.getenv("DISCORD_BOT_TOKEN")
    guild_id_value = os.getenv("DISCORD_GUILD_ID")

    guild_id = int(guild_id_value) if guild_id_value else None
    bot = create_bot(guild_id=guild_id)

    # PORNEȘTE SERVERUL FLASK ÎNAINTE DE BOT
    keep_alive()

    bot.run(token)

