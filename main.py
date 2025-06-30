import discord
import MetaTrader5 as mt5
import json
import asyncio

# Load configuration
with open('config.json') as f:
    config = json.load(f)

# Discord client
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# MT5 connection
def connect_mt5():
    if not mt5.initialize(login=config['MT5_LOGIN'], password=config['MT5_PASSWORD'], server=config['MT5_SERVER']):
        print(f"initialize() failed, error code = {mt5.last_error()}")
        return False
    return True

async def check_trades():
    await client.wait_until_ready()
    channel = client.get_channel(int(config['DISCORD_CHANNEL_ID']))
    if not channel:
        print(f"Could not find channel with ID {config['DISCORD_CHANNEL_ID']}")
        return

    if not connect_mt5():
        return

    print("Connected to MT5 and Discord. Monitoring for trades...")

    last_trade_time = None

    while not client.is_closed():
        try:
            trades = mt5.history_deals_get(0, 10) # Get last 10 deals

            if trades is None:
                print(f"Failed to get trades, error code = {mt5.last_error()}")
                await asyncio.sleep(10)
                continue

            if trades:
                latest_trade = trades[-1]
                if last_trade_time is None or latest_trade.time > last_trade_time:
                    last_trade_time = latest_trade.time
                    # Format and send the message
                    message = f"New Trade Execution:\nSymbol: {latest_trade.symbol}\nType: {'Buy' if latest_trade.entry == 0 else 'Sell'}\nVolume: {latest_trade.volume}\nPrice: {latest_trade.price}\nProfit: {latest_trade.profit}"
                    await channel.send(message)

        except Exception as e:
            print(f"An error occurred: {e}")

        await asyncio.sleep(10) # Check every 10 seconds

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    client.loop.create_task(check_trades())

# Run the bot
if __name__ == "__main__":
    client.run(config['DISCORD_BOT_TOKEN'])
