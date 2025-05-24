import os
import discord
from discord.ext import commands
from discord import app_commands, Interaction, ui

# Intents & bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Helper to parse 200b, 300m, etc.
def parse_isk(value: str) -> float:
    value = value.strip().lower().replace(',', '')
    multipliers = {'b': 1_000_000_000, 'm': 1_000_000, 'k': 1_000}
    if value and value[-1] in multipliers:
        return float(value[:-1]) * multipliers[value[-1]]
    return float(value)

# Format function like PS Format block, to "X.XXb"
def format_isk_b(value: float) -> str:
    return f"{value / 1e9:.2f}b"

# Modal 2 - Rebate info
class RebateModal(ui.Modal, title="HyperNet Rebate Info"):
    rebate_node_count = ui.TextInput(label="Rebate Node Count", required=True, placeholder="e.g. 2")
    rebate_percentage = ui.TextInput(label="Rebate Percentage", required=True, placeholder="e.g. 15")
    hold_ship = ui.TextInput(label="Do you hold the ship? (yes/no)", required=True, placeholder="yes or no")

    async def on_submit(self, interaction: Interaction):
        basic_data = interaction.client.cached_basic_data.get(interaction.user.id)
        if not basic_data:
            await interaction.response.send_message("❌ Error: Basic info missing. Please run /hypernetcalc again.", ephemeral=True)
            return

        try:
            # Parse all inputs
            HypernetList = parse_isk(basic_data["list_price"])
            NumberOfNodes = int(basic_data["node_count"])
            HyperCoreMarketPrice = parse_isk(basic_data["hypercore_price"])
            SelfBuy = int(basic_data["selfbuy_count"])
            ShipCost = parse_isk(basic_data["ship_cost"])

            RebateNodeCount = int(self.rebate_node_count.value)
            RebatePercentage = float(self.rebate_percentage.value)
            HoldInput = self.hold_ship.value.strip().lower()
            Hold = HoldInput == "yes"

            # Constants & calculations from PS
            NodePrice = HypernetList / NumberOfNodes
            SelfBuyCost = SelfBuy * NodePrice
            HyperCoreRatio = 12_753_734
            NumberOfCores = HypernetList / HyperCoreRatio
            HyperCoreCost = NumberOfCores * HyperCoreMarketPrice
            HyperNetFee = HypernetList * 0.05
            RebatePayout = NodePrice * RebateNodeCount * (RebatePercentage / 100)

            # Profit calculations
            TotalWithHoldAndRebate = HypernetList - HyperNetFee - HyperCoreCost - SelfBuyCost - RebatePayout
            TotalWithHoldNoRebate = HypernetList - HyperNetFee - HyperCoreCost - SelfBuyCost
            TotalNoHold = HypernetList - HyperNetFee - HyperCoreCost - SelfBuyCost - ShipCost

            # Compose message based on Hold and rebate presence
            if not Hold:
                message = f"**No hold:** Profit is {format_isk_b(TotalNoHold)}"
            elif RebateNodeCount == 0 or RebatePercentage == 0:
                message = f"**On hold with no rebate:** Profit is {format_isk_b(TotalWithHoldNoRebate)}"
            else:
                message = f"**On hold with rebate:** Profit is {format_isk_b(TotalWithHoldAndRebate)}"

            await interaction.response.send_message(f"📊 **HyperNet Profit Calculation**\n\n{message}", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error during calculation: {e}", ephemeral=True)

# Button to trigger rebate modal
class RebateButton(ui.View):
    def __init__(self):
        super().__init__(timeout=60)  # Optional timeout

    @ui.button(label="Enter Rebate Info", style=discord.ButtonStyle.primary)
    async def rebate_button(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_modal(RebateModal())

# Modal 1 - Basic info
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
