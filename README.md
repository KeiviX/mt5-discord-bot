# MT5 Discord Bot

This bot connects to your MetaTrader 5 (MT5) account and sends real-time trading notifications to a Discord channel.

## Features

*   **New Pending Orders:** Notifies when a new limit or stop order is placed.
*   **Deleted Pending Orders:** Notifies when a pending order is deleted.
*   **New Positions:** Notifies when a new market position is opened.
*   **SL/TP Modifications:** Notifies when Stop Loss or Take Profit levels are modified on an open position, showing pips from entry.
*   **Position Closures:** Notifies when a position is partially or fully closed, including the percentage of the position closed and pips gained/lost.

## Setup

### Prerequisites

*   Python 3.8+
*   MetaTrader 5 terminal installed and running.
*   A Discord account and a Discord server where you want the notifications to be sent.
*   A MetaTrader 5 trading account with valid login credentials.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/KeiviX/mt5-discord-bot.git
    cd mt5-discord-bot
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

1.  **Create `config.json`:**
    Create a file named `config.json` in the root directory of the cloned repository. This file will store your sensitive credentials and **should not be committed to version control**. A `.gitignore` file has been provided to help with this.

    The `config.json` file should have the following structure:

    ```json
    {
        "DISCORD_BOT_TOKEN": "YOUR_DISCORD_BOT_TOKEN",
        "DISCORD_CHANNEL_ID": "YOUR_DISCORD_CHANNEL_ID",
        "MT5_LOGIN": "YOUR_MT5_LOGIN_ID",
        "MT5_PASSWORD": "YOUR_MT5_PASSWORD",
        "MT5_SERVER": "YOUR_MT5_SERVER_NAME"
    }
    ```

    *   **`DISCORD_BOT_TOKEN`**: Your Discord bot token. You can get this by creating a new application on the [Discord Developer Portal](https://discord.com/developers/applications).
    *   **`DISCORD_CHANNEL_ID`**: The ID of the Discord channel where the bot will send messages. To get this, enable Developer Mode in Discord settings, right-click on the channel, and select "Copy ID".
    *   **`MT5_LOGIN`**: Your MetaTrader 5 account login ID (usually a number).
    *   **`MT5_PASSWORD`**: Your MetaTrader 5 account password.
    *   **`MT5_SERVER`**: The name of your MetaTrader 5 trading server (e.g., "ICMarketsSC-MT5-4").

2.  **Ensure MT5 Terminal is Running:**
    The bot needs the MetaTrader 5 terminal to be running on the same machine for it to connect and retrieve data.

### Running the Bot

To start the bot, run the `main.py` script:

```bash
python main.py
```

The bot will connect to Discord and MT5, and start monitoring for trading activity.
