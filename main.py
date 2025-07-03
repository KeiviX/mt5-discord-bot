import discord
import MetaTrader5 as mt5
import json
import asyncio
from datetime import datetime, timedelta

# Load configuration
with open('config.json') as f:
    config = json.load(f)

# Discord client
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# MT5 connection
def connect_mt5():
    # Ensure MT5_LOGIN is an integer
    try:
        login_id = int(config['MT5_LOGIN'])
    except ValueError:
        print(f"Invalid MT5_LOGIN in config.json: '{config['MT5_LOGIN']}' is not a valid integer.")
        return False

    if not mt5.initialize(login=login_id, password=config['MT5_PASSWORD'], server=config['MT5_SERVER']):
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

    current_orders = {order.ticket: order for order in mt5.orders_get() or []}
    current_positions = {position.ticket: position for position in mt5.positions_get() or []}

    while not client.is_closed():
        try:
            # Fetch current state from MT5
            new_orders = {order.ticket: order for order in mt5.orders_get() or []}
            new_positions = {position.ticket: position for position in mt5.positions_get() or []}

            # Check for new, modified, or deleted orders
            await check_orders(channel, current_orders, new_orders)

            # Check for new, modified, or closed positions
            await check_positions(channel, current_positions, new_positions)

            # Update current state
            current_orders = new_orders
            current_positions = new_positions

        except Exception as e:
            print(f"An error occurred: {e}")

        await asyncio.sleep(2) # Check every 2 seconds

async def check_orders(channel, old_orders, new_orders):
    # New orders
    for ticket, order in new_orders.items():
        if order.symbol == "XAUUSD":
            if ticket not in old_orders:
                # New pending order
                order_type = "Buy Limit" if order.type == 2 else "Sell Limit" if order.type == 3 else "Buy Stop" if order.type == 4 else "Sell Stop" if order.type == 5 else "Unknown"
                color = discord.Color.green() if order.type in [2, 4] else discord.Color.red()
                fields = {
                    "Symbol": order.symbol,
                    "Type": order_type,
                    "Price": order.price_open
                }
                if order.sl > 0 and order.tp > 0:
                    fields["Stop Loss / Take Profit"] = f"SL: {order.sl} / TP: {order.tp}"
                elif order.sl > 0:
                    fields["Stop Loss"] = order.sl
                elif order.tp > 0:
                    fields["Take Profit"] = order.tp
                await send_embed(channel, "New Pending Order", color, fields)
            else:
                # Potentially modified pending order
                old_order = old_orders[ticket]
                if old_order.sl != order.sl or old_order.tp != order.tp:
                    order_type = "Buy Limit" if order.type == 2 else "Sell Limit" if order.type == 3 else "Buy Stop" if order.type == 4 else "Sell Stop" if order.type == 5 else "Unknown"
                    color = discord.Color.blue()
                    fields = {
                        "Symbol": order.symbol,
                        "Type": order_type
                    }
                    if old_order.sl != order.sl:
                        fields["New SL"] = order.sl if order.sl > 0 else "Removed"
                    if old_order.tp != order.tp:
                        fields["New TP"] = order.tp if order.tp > 0 else "Removed"
                    await send_embed(channel, "Pending Order Modified", color, fields)

    # Deleted orders
    for ticket, order in old_orders.items():
        if order.symbol == "XAUUSD" and ticket not in new_orders:
            order_type = "Buy Limit" if order.type == 2 else "Sell Limit" if order.type == 3 else "Buy Stop" if order.type == 4 else "Sell Stop" if order.type == 5 else "Unknown"
            color = discord.Color.red()
            fields = {
                "Symbol": order.symbol,
                "Type": order_type,
                "Price": order.price_open
            }
            await send_embed(channel, "Pending Order Deleted", color, fields)

async def check_positions(channel, old_positions, new_positions):
    # New positions
    for ticket, position in new_positions.items():
        if position.symbol == "XAUUSD" and ticket not in old_positions:
            position_type = "Buy" if position.type == 0 else "Sell"
            color = discord.Color.green() if position.type == 0 else discord.Color.red()
            fields = {
                "Symbol": position.symbol,
                "Type": position_type,
                "Price": position.price_open
            }
            await send_embed(channel, "New Position Opened", color, fields)

    # Modified or closed positions
    for ticket, old_position in old_positions.items():
        if old_position.symbol == "XAUUSD":
            if ticket in new_positions:
                new_position = new_positions[ticket]
                # Check for SL/TP modification
                if old_position.sl != new_position.sl or old_position.tp != new_position.tp:
                    color = discord.Color.blue()
                    fields = {
                        "Symbol": new_position.symbol
                    }
                    point = mt5.symbol_info(new_position.symbol).point

                    if old_position.sl != new_position.sl:
                        sl_pips_from_entry = (new_position.sl - new_position.price_open) / point
                        fields["New SL"] = f"{new_position.sl} ({sl_pips_from_entry:.2f} pips from entry)"
                    if old_position.tp != new_position.tp:
                        tp_pips_from_entry = (new_position.tp - new_position.price_open) / point
                        fields["New TP"] = f"{new_position.tp} ({tp_pips_from_entry:.2f} pips from entry)"
                    await send_embed(channel, "Position SL/TP Modified", color, fields)

                # Check for partial close
                if old_position.volume > new_position.volume:
                    closed_volume = old_position.volume - new_position.volume
                    closed_percentage = (closed_volume / old_position.volume) * 100
                    
                    # Calculate pips for the closed portion (this is tricky and might need refinement)
                    # For simplicity, we'll use the current price for pips calculation on partial close
                    point = mt5.symbol_info(new_position.symbol).point
                    pips = 0
                    if new_position.type == mt5.ORDER_TYPE_BUY: # Closed a buy
                        pips = (new_position.price_current - old_position.price_open) / point
                    else: # Closed a sell
                        pips = (old_position.price_open - new_position.price_current) / point

                    color = discord.Color.orange()
                    fields = {
                        "Symbol": new_position.symbol,
                        "Closed Percentage": f"{closed_percentage:.2f}%",
                        "Pips (approx)": f"{pips:.2f}"
                    }
                    await send_embed(channel, "Position Partially Closed", color, fields)

            else: # Position fully closed
                color = discord.Color.red()
                # To get the pips for a fully closed position, we need to look at history deals
                # This part needs to be robust. For now, a simplified message.
                fields = {
                    "Symbol": old_position.symbol,
                    "Close Price": old_position.price_current # This might not be the exact close price
                }
                await send_embed(channel, "Position Fully Closed", color, fields)

async def send_embed(channel, title, color, fields):
    embed = discord.Embed(title=title, color=color)
    for name, value in fields.items():
        embed.add_field(name=name, value=value, inline=False)
    await channel.send(embed=embed)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    client.loop.create_task(check_trades())

# Run the bot
if __name__ == "__main__":
    client.run(config['DISCORD_BOT_TOKEN'])
