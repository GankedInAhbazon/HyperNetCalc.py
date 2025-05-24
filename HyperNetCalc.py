import os
import discord
from discord.ext import commands
from discord import app_commands, Interaction, ui

# Intents & bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Helper to parse 200b, 300m, etc.
def parse_isk(value: str) -> int:
    value = value.strip().lower().replace(',', '')
    multipliers = {'b': 1_000_000_000, 'm': 1_000_000, 'k': 1_000}
    if value[-1] in multipliers:
        return int(float(value[:-1]) * multipliers[value[-1]])
    return int(float(value))

# Modal 2 - Rebate info (original labels)
class RebateModal(ui.Modal, title="HyperNet Rebate Info"):
    rebate_node_count = ui.TextInput(label="Rebate Node Count", required=True, placeholder="e.g. 2")
    rebate_percentage = ui.TextInput(label="Rebate Percentage", required=True, placeholder="e.g. 15")

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
            rebate_node_count = int(self.rebate_node_count.value)
            rebate_percentage = float(self.rebate_percentage.value) / 100.0

            rebate_isk = rebate_node_count * rebate_percentage * list_price

            total_revenue = list_price * selfbuy_count
            total_cost = (hypercore_price * node_count) + ship_cost - rebate_isk
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

# Button to trigger rebate modal
class RebateButton(ui.View):
    def __init__(self):
        super().__init__(timeout=60)  # Optional timeout

    @ui.button(label="Enter Rebate Info", style=discord.ButtonStyle.primary)
    async def rebate_button(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_modal(RebateModal())

# Modal 1 - Basic info (original labels)
class BasicModal(ui.Modal, title="HyperNet Basic Info"):
    list_price = ui.TextInput(label="Hypernet List Price (ISK)", required=True, placeholder="e.g. 200b")
    node_count = ui.TextInput(label="Node Count", required=True, placeholder="e.g. 8")
    hypercore_price = ui.TextInput(label="HyperCore Price (ISK)", required=True, placeholder="e.g. 300k")
    selfbuy_count = ui.TextInput(label="SelfBuy Count", required=True, placeholder="e.g. 3")
    ship_cost = ui.TextInput(label="Ship Cost (ISK)", required=True, placeholder="e.g. 300b")

    async def on_submit(self, interaction: Interaction):
        # Cache inputs exactly as is
        interaction.client.cached_basic_data[interaction.user.id] = {
            "list_price": self.list_price.value,
            "node_count": self.node_count.value,
            "hypercore_price": self.hypercore_price.value,
            "selfbuy_count": self.selfbuy_count.value,
            "ship_cost": self.ship_cost.value,
        }

        # Send confirmation message WITH a button to open rebate modal
        await interaction.response.send_message(
            "✅ Got your basic info. Click the button below to enter your rebate info.",
            ephemeral=True,
            view=RebateButton()
        )

# Bot ready event
@bot.event
async def on_ready():
    bot.cached_basic_data = {}
    try:
        GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "0"))  # Set env var or replace manually
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            await bot.tree.sync(guild=guild)
            print(f"✅ Synced commands to guild {GUILD_ID}")
        else:
            synced = await bot.tree.sync()
            print(f"✅ Globally synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Sync failed: {e}")
    print(f"🤖 Logged in as {bot.user} (ID: {bot.user.id})")

# Slash command - HyperNet Calculation start
@bot.tree.command(name="hypernetcalc", description="Calculate HyperNet profits")
async def hypernetcalc(interaction: discord.Interaction):
    await interaction.response.send_modal(BasicModal())

# Slash command - Rebate-only modal (independent)
@bot.tree.command(name="rebate", description="Enter rebate info")
async def rebate(interaction: discord.Interaction):
    await interaction.response.send_modal(RebateModal())

# Run bot
bot.run(os.getenv("DISCORD_TOKEN"))
