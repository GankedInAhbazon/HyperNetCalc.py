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
    multipliers = {'b': 1e9, 'm': 1e6, 'k': 1e3}
    if value[-1] in multipliers:
        return float(value[:-1]) * multipliers[value[-1]]
    return float(value)

# Modal 2 - Rebate & hold info
class RebateModal(ui.Modal, title="Rebate & Hold Info"):
    rebate_nodes = ui.TextInput(label="Rebate Node Count", required=True, placeholder="e.g. 4")
    rebate_percent = ui.TextInput(label="Rebate Percentage", required=True, placeholder="e.g. 50")
    hold_ship = ui.TextInput(label="Hold the Ship? (yes/no)", required=True, placeholder="yes or no")

    async def on_submit(self, interaction: Interaction):
        basic_data = interaction.client.cached_basic_data.get(interaction.user.id)
        if not basic_data:
            await interaction.response.send_message("❌ Error: Basic info missing. Try again.", ephemeral=True)
            return

        try:
            # Parse all inputs
            list_price = parse_isk(basic_data["list_price"])
            node_count = int(basic_data["node_count"])
            hypercore_price = parse_isk(basic_data["hypercore_price"])
            selfbuy_count = int(basic_data["selfbuy_count"])
            ship_cost = parse_isk(basic_data["ship_cost"])
            rebate_nodes = int(self.rebate_nodes.value)
            rebate_percent = float(self.rebate_percent.value)
            hold = self.hold_ship.value.strip().lower() == "yes"

            node_price = list_price / node_count
            selfbuy_cost = selfbuy_count * node_price
            hypercore_ratio = 12753734
            num_cores = list_price / hypercore_ratio
            hypercore_cost = num_cores * hypercore_price
            hypernet_fee = list_price * 0.05
            rebate_payout = (node_price * rebate_nodes) * (rebate_percent / 100)

            if not hold:
                profit = list_price - hypernet_fee - hypercore_cost - selfbuy_cost - ship_cost
                label = "No Hold"
            elif rebate_nodes == 0 or rebate_percent == 0:
                profit = list_price - hypernet_fee - hypercore_cost - selfbuy_cost
                label = "Hold - No Rebate"
            else:
                profit = list_price - hypernet_fee - hypercore_cost - selfbuy_cost - rebate_payout
                label = "Hold + Rebate"

            await interaction.response.send_message(
                f"📊 **{label} Profit Calculation**\n\n"
                f"**Revenue:** {list_price:,.2f} ISK\n"
                f"**Costs:**\n"
                f"• HyperCore Cost: {hypercore_cost:,.2f} ISK\n"
                f"• SelfBuy Cost: {selfbuy_cost:,.2f} ISK\n"
                f"• Rebate Payout: {rebate_payout:,.2f} ISK\n"
                f"• Ship Cost: {ship_cost:,.2f} ISK\n"
                f"• HyperNet Fee: {hypernet_fee:,.2f} ISK\n\n"
                f"💰 **Profit:** {profit:,.2f} ISK",
                ephemeral=True
            )

        except Exception as e:
            await interaction.response.send_message(f"❌ Error during calculation: {e}", ephemeral=True)

# Modal 1 - Basic info
class BasicModal(ui.Modal, title="HyperNet Basic Info"):
    list_price = ui.TextInput(label="Hypernet List Price (ISK)", required=True, placeholder="e.g. 200b")
    node_count = ui.TextInput(label="Node Count", required=True, placeholder="e.g. 8")
    hypercore_price = ui.TextInput(label="HyperCore Price (ISK)", required=True, placeholder="e.g. 305k")
    selfbuy_count = ui.TextInput(label="SelfBuy Count", required=True, placeholder="e.g. 3")
    ship_cost = ui.TextInput(label="Ship Cost (ISK)", required=True, placeholder="e.g. 300b")

    async def on_submit(self, interaction: Interaction):
        # Cache input
        interaction.client.cached_basic_data[interaction.user.id] = {
            "list_price": self.list_price.value,
            "node_count": self.node_count.value,
            "hypercore_price": self.hypercore_price.value,
            "selfbuy_count": self.selfbuy_count.value,
            "ship_cost": self.ship_cost.value,
        }

        # FIXED: Defer first, then send follow-up modal
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send_modal(RebateModal())

# Bot ready
@bot.event
async def on_ready():
    bot.cached_basic_data = {}
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Sync failed: {e}")
    print(f"🤖 Logged in as {bot.user} (ID: {bot.user.id})")

# Slash command
@bot.tree.command(name="hypernetcalc", description="Calculate HyperNet profits")
async def hypernetcalc(interaction: discord.Interaction):
    await interaction.response.send_modal(BasicModal())

# Run bot
bot.run(os.getenv("DISCORD_TOKEN"))
