import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput
import os

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Temporary user input storage
bot.user_inputs = {}

# ----------------- MODAL 1 -----------------
class HypernetBasicModal(Modal, title="HyperNet Basic Info"):
    list_price = TextInput(label="Hypernet List Price (ISK)", required=True, placeholder="e.g. 200000000")
    node_count = TextInput(label="Node Count", required=True, placeholder="e.g. 8")
    hypercore_price = TextInput(label="HyperCore Price (ISK)", required=True, placeholder="e.g. 1500000")
    selfbuy_count = TextInput(label="SelfBuy Count", required=True, placeholder="e.g. 3")
    ship_cost = TextInput(label="Ship Cost (ISK)", required=True, placeholder="e.g. 300000000")

    async def on_submit(self, interaction: discord.Interaction):
        bot.user_inputs[interaction.user.id] = {
            "list_price": int(self.list_price.value),
            "node_count": int(self.node_count.value),
            "hypercore_price": int(self.hypercore_price.value),
            "selfbuy_count": int(self.selfbuy_count.value),
            "ship_cost": int(self.ship_cost.value),
        }
        await interaction.response.send_modal(HypernetRebateModal())

# ----------------- MODAL 2 -----------------
class HypernetRebateModal(Modal, title="Rebate Information"):
    rebate_nodes = TextInput(label="Rebated Nodes", required=True, placeholder="e.g. 4")
    rebate_percent = TextInput(label="Rebate Percentage", required=True, placeholder="e.g. 5 (for 5%)")

    async def on_submit(self, interaction: discord.Interaction):
        user_data = bot.user_inputs.get(interaction.user.id, {})
        if not user_data:
            await interaction.response.send_message("⚠️ Missing data from the first modal.", ephemeral=True)
            return

        user_data["rebate_nodes"] = int(self.rebate_nodes.value)
        user_data["rebate_percent"] = float(self.rebate_percent.value)

        # Perform calculation
        total_cores = user_data["node_count"]
        selfbuy = user_data["selfbuy_count"]
        cost_per_core = user_data["hypercore_price"]
        total_cost = total_cores * cost_per_core + user_data["ship_cost"]
        total_return = selfbuy * user_data["list_price"]
        rebate_amount = (user_data["rebate_nodes"] * user_data["rebate_percent"] / 100) * cost_per_core
        profit = total_return + rebate_amount - total_cost

        result = (
            f"📊 **HyperNet Profit Calculation**\n"
            f"> **List Price:** {user_data['list_price']:,} ISK\n"
            f"> **Nodes:** {total_cores}\n"
            f"> **SelfBuy Count:** {selfbuy}\n"
            f"> **HyperCore Price:** {cost_per_core:,} ISK\n"
            f"> **Ship Cost:** {user_data['ship_cost']:,} ISK\n"
            f"> **Rebate Nodes:** {user_data['rebate_nodes']}\n"
            f"> **Rebate %:** {user_data['rebate_percent']}%\n\n"
            f"💰 **Estimated Profit:** {int(profit):,} ISK"
        )

        await interaction.response.send_message(result, ephemeral=True)

# ----------------- SLASH COMMAND -----------------
@bot.tree.command(name="hypernetcalc", description="Calculate HyperNet profits")
async def hypernetcalc(interaction: discord.Interaction):
    await interaction.response.send_modal(HypernetBasicModal())

# ----------------- READY EVENT -----------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

# ----------------- MAIN -----------------
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("❌ DISCORD_TOKEN environment variable not set.")
    bot.run(token)
