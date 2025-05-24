import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

def convert_readable_number(value: str, field_name: str) -> float:
    value = value.strip().lower()
    if not value:
        raise ValueError(f"Missing or empty input for '{field_name}'.")

    import re
    match = re.match(r'^([\d.]+)([bmk]?)$', value)
    if not match:
        raise ValueError(f"❌ Invalid numeric input format for '{field_name}': '{value}'")

    number = float(match.group(1))
    suffix = match.group(2)

    if suffix == 'b':
        return number * 1e9
    elif suffix == 'm':
        return number * 1e6
    elif suffix == 'k':
        return number * 1e3
    else:
        return number

def format_billion(amount: float) -> str:
    return f"{amount / 1e9:.2f}b"

@bot.command()
async def hypernet(ctx):
    questions = [
        "Hypernet List Price? (e.g., 1.5b)",
        "How many nodes for this hypernet? 8, 18, 48, or 512?",
        "What is the current price of HyperCores? (e.g., 300k)",
        "How many nodes will you buy?",
        "How many nodes are you offering for a rebate?",
        "At what percentage?",
        "How much did you pay for the ship? (e.g., 150m)",
        "Hold or no hold? (yes/no)"
    ]
    answers = []

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    for question in questions:
        await ctx.send(question)
        try:
            msg = await bot.wait_for('message', check=check, timeout=60.0)
        except asyncio.TimeoutError:
            await ctx.send("❌ Timed out waiting for response.")
            return
        answers.append(msg.content.strip())

    try:
        HypernetList = convert_readable_number(answers[0], "Hypernet List Price")
        NumberOfNodes = float(answers[1])
        HyperCorePrice = convert_readable_number(answers[2], "HyperCore Market Price")
        SelfBuy = float(answers[3])
        Rebate = float(answers[4])
        RBPercentage = float(answers[5])
        ShipCost = convert_readable_number(answers[6], "Ship Cost")
        Hold = answers[7].lower() == "yes"

        NodePrice = HypernetList / NumberOfNodes
        SelfBuyCost = SelfBuy * NodePrice
        HyperCoreRatio = 12753734
        NumberOfCores = HypernetList / HyperCoreRatio
        HyperCoreCost = NumberOfCores * HyperCorePrice
        HyperNetFee = HypernetList * 0.05
        RebatePayout = (NodePrice * Rebate) * (RBPercentage / 100)

        TotalWithHoldAndRebate = HypernetList - HyperNetFee - HyperCoreCost - SelfBuyCost - RebatePayout
        TotalWithHoldNoRebate = HypernetList - HyperNetFee - HyperCoreCost - SelfBuyCost
        TotalNoHold = HypernetList - HyperNetFee - HyperCoreCost - SelfBuyCost - ShipCost

        if not Hold:
            result = f"📦 No hold: Profit is **{format_billion(TotalNoHold)}**"
        elif Rebate == 0 or RBPercentage == 0:
            result = f"📦 On hold with no rebate: Profit is **{format_billion(TotalWithHoldNoRebate)}**"
        else:
            result = f"📦 On hold with rebate: Profit is **{format_billion(TotalWithHoldAndRebate)}**"

        await ctx.send(result)

    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
bot.run('YOUR_BOT_TOKEN')
