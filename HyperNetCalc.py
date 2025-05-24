import os
import discord
from discord.ext import commands
from discord import Interaction, ui

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def parse_isk(value: str) -> int:
    value = value.strip().lower().replace(',', '')
    multipliers = {'b': 1_000_000_000, 'm': 1_000_000, 'k': 1_000}
    if value[-1] in multipliers:
        return int(float(value[:-1]) * multipliers[value[-1]])
    return int(float(value))

class RebateModal(ui.Modal, title="HyperNet Rebate Info"):
    plex_rebate = ui.TextInput(label="PLEX Rebate (ISK)", required=True, placeholder="e.g. 100m")
    hpt_rebate = ui.TextInput(label="HPT Rebate (ISK)", required=True, placeholder="e.g. 0")

    async def on_submit(self, interaction: Interaction):
        basic_data = interaction.client.cached_basic_data.get(interaction.user.id)
        if not basic_data:
            await interaction.response.send_message("❌ Error: Basic info missing. Try again.", ephemeral=True)
            return
        try:
            list_price = parse_isk(basic_data["list_price"])
            node_count = int(basic_data["node_count"])
            hypercore_price = parse_isk(basic_data["hypercore_price"])
            selfbuy_count = int(basic_data["selfbuy_count"])
            ship_cost = parse_isk(basic_data["ship_cost"])
            plex_rebate = parse_isk(self.plex_rebate.value)
            hpt_rebate = parse_isk(self.hpt_rebate.value)

            total_revenue = list_price * selfbuy_count
            total_cost = (hypercore_price * node_count) + ship_cost - plex_rebate - hpt_rebate
            profit = total_revenue - total_cost

            await interaction.response.send_message(
                f"📊 **HyperNet Profit Calculation**\n\n"
                f"**Revenue:** {total_revenue:,} ISK\n"
                f"**Cost:** {total_cost:,} ISK\n"
                f"**Profit:** {profit:,} ISK",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Error during calculation: {e}", ephemeral=True)

class BasicModal(ui.Modal, title="HyperNet Basic Info"):
    list_price = ui.TextInput(label="Hypernet List Price (ISK)", required=True, placeholder="e.g. 200b")
    node_count = ui.TextInput(label="Node Count", required=True, placeholder="e.g. 8")
    hypercore_price = ui.TextInput(label="HyperCore Price (ISK)", required=True, placeholder="e.g. 1.5m")
    selfbuy_count = ui.TextInput(label="SelfBuy Count", required=True, placeholder="e.g. 3")
    ship_cost = ui.TextInput(label="Ship Cost (ISK)", required=True, placeholder="e.g. 300b")

    async def on_submit(self, interaction: Interaction):
        interaction.client.cached_basic_data[interaction.user.id] = {
            "list_price": self.list_price.value,
            "node_count": self.node_count.value,
            "hypercore_price": self.hypercore_price.value,
            "selfbuy_count": self.selfbuy_count.value,
            "ship_cost": self.ship_cost.value,
        }
        await interaction.response.send_message(
            "✅ Got your basic info. Now please use the `/rebate` command to enter your rebate info.",
            ephemeral=True
        )

@bot.event
async def on_ready():
    bot.cached_basic_data = {}
    guild_id = 690233573852184764 # Replace with your actual guild/server ID as an int
    guild = discord.Object(id=guild_id)
    try:
        synced = await bot.tree.sync(guild=guild)
        print(f"✅ Synced {len(synced)} command(s) to guild {guild.id}")
    except Exception as e:
        print(f"❌ Sync failed: {e}")

    # Debug: List commands registered
    commands_list = await bot.tree.fetch_commands(guild=guild)
    print("Registered slash commands in guild:")
    for cmd in commands_list:
        print(f" - {cmd.name}")

    print(f"🤖 Logged in as {bot.user} (ID: {bot.user.id})")

@bot.tree.command(name="hypernetcalc", description="Calculate HyperNet profits")
async def hypernetcalc(interaction: Interaction):
    await interaction.response.send_modal(BasicModal())

@bot.tree.command(name="rebate", description="Enter rebate info")
async def rebate(interaction: Interaction):
    await interaction.response.send_modal(RebateModal())

bot.run(os.getenv("DISCORD_TOKEN"))
