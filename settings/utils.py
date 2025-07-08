"""
Utility functions for managing queueing system settings in the database.
All functions are asynchronous and use aiosqlite for non-blocking DB access.
"""
import aiosqlite

async def init_db() -> None:
    """
    Initialize the SQLite database for the queueing system.
    Creates the 'queueing_settings' table if it does not already exist. This table stores all configuration
    settings for each guild (server), including role and channel IDs required for the queueing system.
    This function should be called before any other database operations.
    """
    async with aiosqlite.connect("queueing_system.db") as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS queueing_settings (
                guild_id INTEGER PRIMARY KEY,
                admin_role_id INTEGER NOT NULL,
                queue_category_id INTEGER NOT NULL,
                queue_channel_id INTEGER NOT NULL,
                session_calls_category_id INTEGER NOT NULL,
                log_channel_id INTEGER NOT NULL,
                sessions_channel_id INTEGER NOT NULL,
                amount_to_queue INTEGER NOT NULL DEFAULT 0,
                paused BOOLEAN NOT NULL DEFAULT 0
            )
        ''')
        await db.commit()

async def get_queueing_settings(guild_id: int) -> dict | None:
    """
    Retrieve all queueing settings for a specific guild.

    Args:
        guild_id (int): The Discord guild (server) ID.

    Returns:
        dict: A dictionary containing all settings for the guild, with keys:
            'guild_id', 'admin_role_id', 'queue_category_id', 'queue_channel_id', 'session_calls_category_id', 
            'log_channel_id', 'sessions_channel_id', 'amount_to_queue', 'paused'.
        None: If no settings are found for the given guild_id.
    """
    async with aiosqlite.connect("queueing_system.db") as db:
        async with db.execute('SELECT * FROM queueing_settings WHERE guild_id = ?', (guild_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    'guild_id': row[0],
                    'admin_role_id': row[1],
                    'queue_category_id': row[2],
                    'queue_channel_id': row[3],
                    'session_calls_category_id': row[4],
                    'log_channel_id': row[5],
                    'sessions_channel_id': row[6],
                    'amount_to_queue': row[7],
                    'paused': row[8]
                }
    return None


async def set_queueing_settings(guild_id: int, settings: dict) -> None:
    """
    Insert or update all queueing settings for a specific guild.

    Args:
        guild_id (int): The Discord guild (server) ID.
        settings (dict): A dictionary containing all required settings for the guild. Must include:
            'admin_role_id', 'queue_category_id', 'queue_channel_id', 'session_calls_category_id', 
            'log_channel_id', 'sessions_channel_id', 'amount_to_queue', 'paused'.

    This function will create a new row or replace the existing row for the guild.
    """
    async with aiosqlite.connect("queueing_system.db") as db:
        await db.execute('''
            INSERT OR REPLACE INTO queueing_settings (
                guild_id, admin_role_id, queue_category_id, queue_channel_id,session_calls_category_id, 
                log_channel_id, sessions_channel_id, amount_to_queue, paused
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            guild_id,
            settings.get('admin_role_id', None),
            settings.get('queue_category_id', None),
            settings.get('queue_channel_id', None),
            settings.get('session_calls_category_id', None),
            settings.get('log_channel_id', None),
            settings.get('sessions_channel_id', None),
            settings.get('amount_to_queue', 0),
            settings.get('paused', False),
        ))
        await db.commit()

async def delete_queueing_settings(guild_id: int) -> None:
    """
    Delete all queueing settings for a specific guild.

    Args:
        guild_id (int): The Discord guild (server) ID.

    This will remove the guild's settings from the database entirely.
    """
    async with aiosqlite.connect("queueing_system.db") as db:
        await db.execute('DELETE FROM queueing_settings WHERE guild_id = ?', (guild_id,))
        await db.commit()
    
async def get_admin_role_id(guild_id: int) -> int | None:
    """
    Get the admin role ID for a specific guild.

    Args:
        guild_id (int): The Discord guild (server) ID.

    Returns:
        int: The admin role ID if set, or None if not found.
    """
    async with aiosqlite.connect("queueing_system.db") as db:
        async with db.execute('SELECT admin_role_id FROM queueing_settings WHERE guild_id = ?', (guild_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]
    return None

async def get_queue_channel_id(guild_id: int) -> int | None:
    """
    Get the queue channel ID for a specific guild.

    Args:
        guild_id (int): The Discord guild (server) ID.

    Returns:
        int: The queue channel ID if set, or None if not found.
    """
    async with aiosqlite.connect("queueing_system.db") as db:
        async with db.execute('SELECT queue_channel_id FROM queueing_settings WHERE guild_id = ?', (guild_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]
    return None

async def get_session_calls_category_id(guild_id: int) -> int | None:
    """
    Get the session calls category ID for a specific guild.

    Args:
        guild_id (int): The Discord guild (server) ID.

    Returns:
        int: The session calls category ID if set, or None if not found.
    """
    async with aiosqlite.connect("queueing_system.db") as db:
        async with db.execute('SELECT session_calls_category_id FROM queueing_settings WHERE guild_id = ?', (guild_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]
    return None

async def get_log_channel_id(guild_id: int) -> int | None:
    """
    Get the log channel ID for a specific guild.

    Args:
        guild_id (int): The Discord guild (server) ID.

    Returns:
        int: The log channel ID if set, or None if not found.
    """
    async with aiosqlite.connect("queueing_system.db") as db:
        async with db.execute('SELECT log_channel_id FROM queueing_settings WHERE guild_id = ?', (guild_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]
    return None

async def get_sessions_channel_id(guild_id: int) -> int | None:
    """
    Get the sessions channel ID for a specific guild.

    Args:
        guild_id (int): The Discord guild (server) ID.

    Returns:
        int: The sessions channel ID if set, or None if not found.
    """
    async with aiosqlite.connect("queueing_system.db") as db:
        async with db.execute('SELECT sessions_channel_id FROM queueing_settings WHERE guild_id = ?', (guild_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]
    return None

async def get_amount_to_queue(guild_id: int) -> int:
    """
    Get the amount to queue for a specific guild.

    Args:
        guild_id (int): The Discord guild (server) ID.

    Returns:
        int: The amount to queue if set, or 0 if not found.
    """
    async with aiosqlite.connect("queueing_system.db") as db:
        async with db.execute('SELECT amount_to_queue FROM queueing_settings WHERE guild_id = ?', (guild_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]
    return 0

async def get_paused_status(guild_id: int) -> bool:
    """
    Get the paused status of the queueing system for a specific guild.

    Args:
        guild_id (int): The Discord guild (server) ID.

    Returns:
        bool: True if the queueing system is paused, False otherwise.
    """
    async with aiosqlite.connect("queueing_system.db") as db:
        async with db.execute('SELECT paused FROM queueing_settings WHERE guild_id = ?', (guild_id,)) as cursor:
            row = await cursor.fetchone()
            if row is not None:
                return bool(row[0])
    return False

async def set_admin_role_id(guild_id: int, role_id: int) -> bool:
    """
    Set the admin role ID for a specific guild.

    Args:
        guild_id (int): The Discord guild (server) ID.
        role_id (int): The Discord role ID to set as admin.

    Returns:
        bool: True if a row was updated, False otherwise (e.g., if the guild_id does not exist).
    """
    async with aiosqlite.connect("queueing_system.db") as db:
        cursor = await db.execute('UPDATE queueing_settings SET admin_role_id = ? WHERE guild_id = ?', (role_id, guild_id))
        await db.commit()
        return cursor.rowcount > 0

async def set_queue_channel_id(guild_id: int, channel_id: int) -> bool:
    """
    Set the queue channel ID for a specific guild.

    Args:
        guild_id (int): The Discord guild (server) ID.
        channel_id (int): The Discord channel ID to set as the queue channel.

    Returns:
        bool: True if a row was updated, False otherwise (e.g., if the guild_id does not exist).
    """
    async with aiosqlite.connect("queueing_system.db") as db:
        cursor = await db.execute('UPDATE queueing_settings SET queue_channel_id = ? WHERE guild_id = ?', (channel_id, guild_id))
        await db.commit()
        return cursor.rowcount > 0

async def set_session_calls_category_id(guild_id: int, category_id: int) -> bool:
    """
    Set the session calls category ID for a specific guild.

    Args:
        guild_id (int): The Discord guild (server) ID.
        category_id (int): The Discord category ID to set for session calls.

    Returns:
        bool: True if a row was updated, False otherwise (e.g., if the guild_id does not exist).
    """
    async with aiosqlite.connect("queueing_system.db") as db:
        cursor = await db.execute('UPDATE queueing_settings SET session_calls_category_id = ? WHERE guild_id = ?', (category_id, guild_id))
        await db.commit()
        return cursor.rowcount > 0

async def set_log_channel_id(guild_id: int, channel_id: int) -> bool:
    """
    Set the log channel ID for a specific guild.

    Args:
        guild_id (int): The Discord guild (server) ID.
        channel_id (int): The Discord channel ID to set as the log channel.

    Returns:
        bool: True if a row was updated, False otherwise (e.g., if the guild_id does not exist).
    """
    async with aiosqlite.connect("queueing_system.db") as db:
        cursor = await db.execute('UPDATE queueing_settings SET log_channel_id = ? WHERE guild_id = ?', (channel_id, guild_id))
        await db.commit()
        return cursor.rowcount > 0

async def set_sessions_channel_id(guild_id: int, channel_id: int) -> bool:
    """
    Set the sessions channel ID for a specific guild.

    Args:
        guild_id (int): The Discord guild (server) ID.
        channel_id (int): The Discord channel ID to set as the sessions channel.

    Returns:
        bool: True if a row was updated, False otherwise (e.g., if the guild_id does not exist).
    """
    async with aiosqlite.connect("queueing_system.db") as db:
        cursor = await db.execute('UPDATE queueing_settings SET sessions_channel_id = ? WHERE guild_id = ?', (channel_id, guild_id))
        await db.commit()
        return cursor.rowcount > 0

async def set_amount_to_queue(guild_id: int, amount: int) -> bool:
    """
    Set the amount to queue for a specific guild.

    Args:
        guild_id (int): The Discord guild (server) ID.
        amount (int): The amount to queue.

    Returns:
        bool: True if a row was updated, False otherwise (e.g., if the guild_id does not exist).
    """
    async with aiosqlite.connect("queueing_system.db") as db:
        cursor = await db.execute('UPDATE queueing_settings SET amount_to_queue = ? WHERE guild_id = ?', (amount, guild_id))
        await db.commit()
        return cursor.rowcount > 0

async def set_paused_status(guild_id: int, paused: bool) -> bool:
    """
    Set the paused status of the queueing system for a specific guild.

    Args:
        guild_id (int): The Discord guild (server) ID.
        paused (bool): True to pause the queueing system, False to resume.

    Returns:
        bool: True if a row was updated, False otherwise (e.g., if the guild_id does not exist).
    """
    async with aiosqlite.connect("queueing_system.db") as db:
        cursor = await db.execute('UPDATE queueing_settings SET paused = ? WHERE guild_id = ?', (paused, guild_id))
        await db.commit()
        return cursor.rowcount > 0
    


# I did not write these 2 functions, AI did. I'm not smart enough to write this.
# They might as well be magic to me.
# They are used to convert numbers to a custom ID format and vice versa.
import string

CHARSET = string.ascii_letters + string.digits
BASE = len(CHARSET)


def number_to_id(n: int) -> str:
    def feistel_encrypt(x, rounds=4, key=0xBEEF):
        L = (x >> 12) & 0xFFF
        R = x & 0xFFF
        for _ in range(rounds):
            L, R = R, L ^ ((R * 193 + key) & 0xFFF)
        return (L << 12) | R

    def base62_encode(num):
        s = ''
        while num > 0:
            num, rem = divmod(num, BASE)
            s = CHARSET[rem] + s
        return s.rjust(5, CHARSET[0])

    return base62_encode(feistel_encrypt(n))

def id_to_number(s: str) -> int:
    def base62_decode(s):
        num = 0
        for c in s:
            num = num * BASE + CHARSET.index(c)
        return num

    def feistel_decrypt(x, rounds=4, key=0xBEEF):
        L = (x >> 12) & 0xFFF
        R = x & 0xFFF
        for _ in range(rounds):
            L, R = R ^ ((L * 193 + key) & 0xFFF), L
        return (L << 12) | R

    return feistel_decrypt(base62_decode(s))
