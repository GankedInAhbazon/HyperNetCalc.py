import discord
from discord.ext import commands
from discord import app_commands
import os

intents = discord.Intents.default()
intents.message_content = True  # Optional, for logging messages

bot = commands.Bot(command_prefix="!", intents=intents)

# Modal definition
class HypernetModal(discord.ui.Modal, title="HyperNet Profit Calculator"):
    list_price = discord.ui.TextInput(label="List Price (e.g. 1.5b)", required=True)
    node_count = discord.ui.TextInput(label="Node Count (e.g. 512)", required=True)
    core_price = discord.ui.TextInput(label="HyperCore Price (e.g. 300k)", required=True)
    selfbuy = discord.ui.TextInput(label="Selfbuy Nodes (e.g. 10)", required=True)
    hold = discord.ui.TextInput(label="Hold? (yes or no)", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            def parse_number(value, name):
                value = value.strip().lower()
                import re
                match = re.match(r'^([\d.]+)([bmk]?)$', value)
                if not match:
                    raise ValueError(f"❌ Invalid format for '{name}': {value}")
                number = float(match.group(1))
                suffix = match.group(2)
                return number * {'b': 1e9, 'm': 1e6, 'k': 1e3}.get(suffix, 1)

            hl = parse_number(self.list_price.value, "List Price")
            nc = int(self.node_count.value.strip())
            hc = parse_number(self.core_price.value, "HyperCore Price")
            sb = int(self.selfbuy.value.strip())
            hold = self.hold.value.strip().lower() == "yes"

            node_price = hl / nc
            selfbuy_cost = sb * node_price
            core_count = hl / 12753734
            core_cost = core_count * hc
            fee = hl * 0.05

            profit = hl - fee - core_cost - selfbuy_cost
            profit_b = f"{profit / 1e9:.2f}b"
            label = "✅ Hold" if hold else "❌ No Hold"

            await interaction.response.send_message(f"**{label}** Profit: `{profit_b}`", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"⚠️ Error: {e}", ephemeral=True)

# Slash command
@bot.tree.command(name="hypernetcalc", description="Calculate HyperNet profits")
async def hypernetcalc(interaction: discord.Interaction):
    await interaction.response.send_modal(HypernetModal())

# Sync slash commands on startup
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

# Run the bot
bot.run(os.getenv("DISCORD_TOKEN"))
