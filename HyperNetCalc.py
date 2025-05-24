import discord
import os
from discord import app_commands
from discord.ext import commands

class HypernetModal(discord.ui.Modal, title="HyperNet Profit Calculator"):
    list_price = discord.ui.TextInput(label="Hypernet List Price (e.g. 1.5b)", required=True)
    node_count = discord.ui.TextInput(label="Number of Nodes (e.g. 8, 18, 48, 512)", required=True)
    core_price = discord.ui.TextInput(label="HyperCore Price (e.g. 300k)", required=True)
    selfbuy = discord.ui.TextInput(label="Nodes You Will Buy", required=True)
    rebate_nodes = discord.ui.TextInput(label="Rebate Nodes Offered", required=True)
    rebate_percent = discord.ui.TextInput(label="Rebate %", required=True)
    ship_cost = discord.ui.TextInput(label="Ship Cost (e.g. 150m)", required=True)
    hold = discord.ui.TextInput(label="Hold? (yes or no)", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            def parse_number(value, name):
                value = value.strip().lower()
                import re
                match = re.match(r'^([\d.]+)([bmk]?)$', value)
                if not match:
                    raise ValueError(f"❌ Invalid input format for '{name}': {value}")
                number = float(match.group(1))
                suffix = match.group(2)
                return number * {'b': 1e9, 'm': 1e6, 'k': 1e3}.get(suffix, 1)

            # Convert input
            hl = parse_number(self.list_price.value, "List Price")
            nc = int(self.node_count.value.strip())
            hc = parse_number(self.core_price.value, "Core Price")
            sb = int(self.selfbuy.value.strip())
            rn = int(self.rebate_nodes.value.strip())
            rp = float(self.rebate_percent.value.strip())
            sc = parse_number(self.ship_cost.value, "Ship Cost")
            hold = self.hold.value.strip().lower() == "yes"

            # Math
            node_price = hl / nc
            selfbuy_cost = sb * node_price
            hypercore_ratio = 12753734
            core_count = hl / hypercore_ratio
            core_cost = core_count * hc
            fee = hl * 0.05
            rebate_payout = (node_price * rn) * (rp / 100)

            if not hold:
                profit = hl - fee - core_cost - selfbuy_cost - sc
                label = "❌ No Hold"
            elif rn == 0 or rp == 0:
                profit = hl - fee - core_cost - selfbuy_cost
                label = "✅ Hold, No Rebate"
            else:
                profit = hl - fee - core_cost - selfbuy_cost - rebate_payout
                label = "✅ Hold with Rebate"

            profit_b = f"{profit / 1e9:.2f}b"
            await interaction.response.send_message(
                f"**{label}**: Estimated Profit = `{profit_b}`", ephemeral=True
            )

        except Exception as e:
            await interaction.response.send_message(f"⚠️ Error: {e}", ephemeral=True)


class HyperNetBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.default())

    async def setup_hook(self):
        self.tree.add_command(app_commands.Command(name="hypernetcalc", description="Calculate HyperNet Profit", callback=self.hypernetcalc))

    async def on_ready(self):
        print(f"✅ Logged in as {self.user} (ID: {self.user.id})")
        print("🔁 Syncing command tree...")
        await self.tree.sync()
        print("✅ Synced slash commands.")

    async def hypernetcalc(self, interaction: discord.Interaction):
        await interaction.response.send_modal(HypernetModal())


bot = HyperNetBot()
bot.run(os.getenv("DISCORD_TOKEN"))
