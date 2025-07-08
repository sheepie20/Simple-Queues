# Discord Queueing System Bot

A Discord bot for managing queueing systems, and session calls, for your server. Built with `discord.py`, this bot allows you to set up queue channels, automatically create session calls, and manage queueing logic with ease.

## Features
- **Queueing System**: Users can join a queue voice channel. When the queue reaches a set size, a session call is automatically created and users are moved.
- **Session Calls**: Session call voice channels are created dynamically and permissions are managed automatically.
- **Moderation Role**: Assign a role with special permissions to manage the queueing system.
- **Logging**: All important actions (setup, reset, queue join/leave, session creation, etc.) are logged to a dedicated channel.
- **Pause/Resume**: Administrators can pause or resume the queueing system.
- **Reset**: Reset the queueing system and optionally delete all created channels/categories.

## Setup

### Prerequisites
- Python 3.10+
- `discord.py` (2.0+)
- `aiosqlite`
- `.env` file with your Discord bot token (`DISCORD_TOKEN`)

### Installation
1. Clone this repository.
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory and add your bot token:
   ```env
   DISCORD_TOKEN=your-bot-token-here
   ```
4. Run the bot:
   ```sh
   python main.py
   ```

## Usage

### Commands
- `/setup <moderation-role> <amount-to-queue> [paused]` — Set up the queueing system. Creates all required channels and categories.
- `/reset-settings [delete-channels]` — Reset the queueing system. Optionally delete all created channels.
- `/pause` — Pause the queueing system (users cannot join the queue channel).
- `/resume` — Resume the queueing system.
- `/queue-info` — Display information on the queueing system.
- `/change-q-amount <amount-to-queue>` — Changes the required amount of users to queue a session.

### How It Works
- When users join the queue voice channel, they are added to the queue.
- When the queue reaches the configured size, a session call channel is created and users are moved there.
- All actions are logged in the log channel.
- The bot uses an SQLite database (`queueing_system.db`) to store all settings per guild.

## Configuration

Settings are stored in the database and can be managed via the provided commands. The following are tracked:
- `admin_role_id`: Role with admin permissions for the queueing system
- `queue_category_id`, `queue_channel_id`: Category and channel for the queue
- `session_calls_category_id`: Category for session calls
- `log_channel_id`: Channel for logging
- `sessions_channel_id`: Channel for session logs
- `amount_to_queue`: Number of users required to trigger a session call
- `paused`: Whether the queueing system is paused

## File Structure
- `main.py` — Bot entry point, loads cogs and initializes the database
- `cogs/queueing.py` — Main cog for queueing logic and commands
- `settings/utils.py` — Async database utilities for settings
- `settings/bot.py` — Bot configuration (token, intents, prefix)

## License
MIT

## Acknowledgements

Inspiration from [Ranked Bedwars](https://discord.gg/rankedbedwars)' queueing system