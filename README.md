# Simple Queues

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

**Simple Queues** is a Discord bot for managing queueing systems and session calls for your server. Built with `discord.py`, this bot allows you to set up queue channels, automatically create session calls, and manage queueing logic with ease.

## Features
- **Queueing System**: Users can join a queue voice channel. When the queue reaches a set size, a session call is automatically created and users are moved.
- **Session Calls**: Temporary voice channels created when enough users are queued. Permissions are automatically managed.
- **Moderation Role**: Assign a role with special permissions to manage the queueing system.
- **Logging**: All important actions (setup, reset, queue join/leave, session creation, etc.) are logged to a dedicated channel.
- **Pause/Resume**: Administrators can pause or resume the queueing system.
- **Reset**: Reset the queueing system and optionally delete all created channels/categories.
- **Edit All Settings**: Use a single command to edit any or all queueing system settings, with all parameters optional.
- **Robust Error Handling**: Improved error handling and async database access for reliability.

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

   ⚠️ **Important**: Never commit your `.env` file or bot token to source control.
4. Run the bot:

   ```sh
   python main.py
   ```

## Usage

### Commands

| Command                                               | Description                                                                        |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `/setup <moderation-role> <amount-to-queue> [paused]` | Set up the Simple Queues system. Creates all required channels and categories.     |
| `/reset-settings [delete-channels]`                   | Reset the Simple Queues system. Optionally delete all created channels.            |
| `/pause`                                              | Pause the Simple Queues system (users cannot join the queue channel).              |
| `/resume`                                             | Resume the Simple Queues system.                                                   |
| `/queue-info`                                         | Display information on the Simple Queues system.                                   |
| `/change-q-amount <amount-to-queue>`                  | Change the required number of users to trigger a session.                          |
| `/edit-settings [all settings optional]`              | Edit any or all settings in one command. Only provided parameters will be updated. |

### How It Works

* When users join the queue voice channel, they are added to the queue.
* When the queue reaches the configured size, a session call channel is created and users are moved there.
* All actions are logged in the log channel.
* The bot uses an SQLite database (`queueing_system.db`) to store all settings per guild.

## Configuration

Settings are stored in the database and can be managed via the provided commands. All settings can be edited at once using `/edit-settings`, with all parameters optional. The following are tracked:

* `admin_role_id`: Role with admin permissions for Simple Queues
* `queue_category_id`, `queue_channel_id`: Category and channel for the queue
* `session_calls_category_id`: Category for session calls
* `log_channel_id`: Channel for logging
* `sessions_channel_id`: Channel for session logs
* `amount_to_queue`: Number of users required to trigger a session call
* `paused`: Whether the queueing system is paused

## File Structure

* `main.py` — Bot entry point, loads cogs and initializes the database
* `cogs/queueing.py` — Main cog for queueing logic and commands
* `settings/utils.py` — Async database utilities for settings
* `settings/bot.py` — Bot configuration (token, intents, prefix)

## License

MIT

## Terms of Service

Visit the Terms of Service [here](https://sheepie.dev/queue-tos.html)

## Privacy Policy

Visit the Privacy Policy [here](https://sheepie.dev/queue-privacy.html)

## Support / Invite

* **Invite the Bot**: [Invite Link](https://discord.com/oauth2/authorize?client_id=1391930404725854289)
* **GitHub**: [Simple Queues Repository](https://github.com/sheepie20/Simple-Queues)
* **Contact**: [sheepiegamer20@gmail.com](mailto:sheepiegamer20@gmail.com)

## Acknowledgements

Inspiration from [Ranked Bedwars](https://discord.gg/rankedbedwars)' queueing system