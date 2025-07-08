# Make a bare-bones cog.
import discord
from discord.ext import commands
from settings import bot as settings
from settings import utils
from discord import app_commands
import random
from datetime import datetime, timezone


class QueueingCog(commands.Cog):
    """A cog for managing queueing systems."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queue = {}
        self.session_calls = []

    @commands.hybrid_command(name='setup', description='Setup the queueing system.')
    @commands.has_permissions(administrator=True)
    @app_commands.describe(amount_to_queue="The amount of users to queue before a session is created.")
    @app_commands.rename(amount_to_queue="amount-to-queue")
    @app_commands.describe(moderation_role="The role that can manage the queueing system.")
    @app_commands.rename(moderation_role="moderation-role")
    @app_commands.describe(paused="Whether the queueing system should start paused.")
    async def setup(self, ctx: commands.Context, moderation_role: discord.Role, amount_to_queue: int, paused: bool = False):
        """Setup the queueing system."""
        await ctx.defer()

        if await utils.get_queueing_settings(ctx.guild.id):
            await ctx.send("Queueing system is already set up.")
            return

        queue_category = await ctx.guild.create_category(
            'Queue', 
            reason='Queueing system setup'
        )
        
        queue_channel = await ctx.guild.create_voice_channel(
            'Queue', category=queue_category,
            reason='Queueing system setup'
        )
        
        session_calls = await ctx.guild.create_category(
            'Session Calls', 
            reason='Queueing system setup'
        )
        
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            moderation_role: discord.PermissionOverwrite(read_messages=True, connect=True),
            ctx.author: discord.PermissionOverwrite(read_messages=True, connect=True)
        }

        log_channel = await ctx.guild.create_text_channel(
            'queue-logs', 
            category=queue_category,
            overwrites=overwrites, 
            reason='Queueing system setup'
        )
        
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
            moderation_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        sessions_channel = await ctx.guild.create_text_channel(
            'sessions', 
            category=session_calls,
            reason='Queueing system setup',
            overwrites=overwrites
        )

        settings = { 
            'admin_role_id': moderation_role.id,
            'queue_category_id': queue_category.id,
            'queue_channel_id': queue_channel.id,
            'session_calls_category_id': session_calls.id,
            'log_channel_id': log_channel.id,
            'sessions_channel_id': sessions_channel.id,
            'amount_to_queue': amount_to_queue,
            'paused': paused
        }

        await utils.set_queueing_settings(
            ctx.guild.id, settings
        )
        await ctx.send(
            f"Queueing system setup complete!"
        )

        # Logging
        log_message = (
            f"Queueing system setup by {ctx.author.mention} ({ctx.author.id})\n"
            f"Moderation Role: {moderation_role.mention} ({moderation_role.id})\n"
            f"Amount to queue: {amount_to_queue}\n"
            f"Paused: {paused}\n"
            f"Queue Category: {queue_category.mention} ({queue_category.id})\n"
            f"Queue Channel: {queue_channel.mention} ({queue_channel.id})\n"
            f"Session Calls Category: {session_calls.mention} ({session_calls.id})\n"
            f"Log Channel: {log_channel.mention} ({log_channel.id})\n"
            f"Sessions Channel: {sessions_channel.mention} ({sessions_channel.id})"
        )
        await log_channel.send(log_message)

    @commands.hybrid_command(name='reset-settings', description='Reset the queueing system settings.')
    @commands.has_permissions(administrator=True)
    @app_commands.describe(delete_channels="Whether to delete the queueing channels.")
    async def reset_settings(self, ctx: commands.Context, delete_channels: bool = False):
        """Reset the queueing system settings."""
        await ctx.defer()
        guild_settings = await utils.get_queueing_settings(ctx.guild.id)
        if not guild_settings:
            await ctx.send("Queueing system is not set up.")
            return

        log_channel = ctx.guild.get_channel(guild_settings['log_channel_id'])
        if not delete_channels and log_channel:
            log_message = (
                f"Queueing system reset by {ctx.author.mention} ({ctx.author.id})\n"
                f"Channels and categories were not deleted."
            )
            await log_channel.send(log_message)

        if delete_channels:
            queue_category = ctx.guild.get_channel(guild_settings['queue_category_id'])
            if queue_category:
                await queue_category.delete(reason='Queueing system reset')
            queue_channel = ctx.guild.get_channel(guild_settings['queue_channel_id'])
            if queue_channel:
                await queue_channel.delete(reason='Queueing system reset')
            session_calls_category = ctx.guild.get_channel(guild_settings['session_calls_category_id'])
            if session_calls_category:
                # Delete all voice channels under the Session Calls category
                for channel in session_calls_category.channels:
                    if isinstance(channel, discord.VoiceChannel):
                        await channel.delete(reason='Queueing system reset (Session Calls cleanup)')
                await session_calls_category.delete(reason='Queueing system reset')
            if log_channel:
                await log_channel.delete(reason='Queueing system reset')
            sessions_channel = ctx.guild.get_channel(guild_settings['sessions_channel_id'])
            if sessions_channel:
                await sessions_channel.delete(reason='Queueing system reset')
        await utils.delete_queueing_settings(ctx.guild.id)
        try:
            await ctx.send("Queueing system settings have been reset.")
        except:
            pass

    @commands.hybrid_command(name='pause', description='Pause the queueing system.')
    @commands.has_permissions(administrator=True)
    async def pause(self, ctx: commands.Context):
        """Pause the queueing system."""
        await ctx.defer()
        guild_settings = await utils.get_queueing_settings(ctx.guild.id)
        if not guild_settings:
            await ctx.send("Queueing system is not set up.")
            return
        if guild_settings.get('paused'):
            await ctx.send("Queueing system is already paused.")
            return
        await utils.set_paused_status(ctx.guild.id, True)
        await ctx.send("Queueing system has been paused.")

        # Logging
        log_channel = ctx.guild.get_channel(guild_settings['log_channel_id'])
        if log_channel:
            log_message = (
                f"Queueing system paused by {ctx.author.mention} ({ctx.author.id})"
            )
            await log_channel.send(log_message)

    @commands.hybrid_command(name='resume', description='Resume the queueing system.')
    @commands.has_permissions(administrator=True)
    async def resume(self, ctx: commands.Context):
        """Resume the queueing system."""
        await ctx.defer()
        guild_settings = await utils.get_queueing_settings(ctx.guild.id)
        if not guild_settings:
            await ctx.send("Queueing system is not set up.")
            return
        if not guild_settings.get('paused'):
            await ctx.send("Queueing system is not paused.")
            return
        await utils.set_paused_status(ctx.guild.id, False)
        await ctx.send("Queueing system has been resumed.")

        # Logging
        log_channel = ctx.guild.get_channel(guild_settings['log_channel_id'])
        if log_channel:
            log_message = (
                f"Queueing system resumed by {ctx.author.mention} ({ctx.author.id})"
            )
            await log_channel.send(log_message)

    @commands.hybrid_command(name='queue-info', description='Get information about the queueing system.')
    @commands.has_permissions(administrator=True)
    async def queue_info(self, ctx: commands.Context):
        """Get information about the queueing system."""
        await ctx.defer()
        guild_settings = await utils.get_queueing_settings(ctx.guild.id)
        if not guild_settings:
            await ctx.send("Queueing system is not set up.")
            return

        info_embed = discord.Embed(
            title="Queueing System Information",
            color=random.randint(0, 0xFFFFFF)
        )
        info_embed.add_field(name="Paused", value="True" if str(guild_settings.get('paused')) == "1" else "False", inline=False)
        info_embed.add_field(name="Amount to Queue", value=str(guild_settings.get('amount_to_queue')), inline=False)
        info_embed.add_field(name="Queue Channel", value=f"<#{guild_settings['queue_channel_id']}>", inline=False)
        info_embed.add_field(name="Session Calls Category", value=f"<#{guild_settings['session_calls_category_id']}>", inline=False)
        info_embed.add_field(name="Log Channel", value=f"<#{guild_settings['log_channel_id']}>", inline=False)
        info_embed.add_field(name="Sessions Channel", value=f"<#{guild_settings['sessions_channel_id']}>", inline=False)

        await ctx.send(embed=info_embed)

    @commands.hybrid_command(name='change-q-amount', description='Change the amount of users to queue before a session is created.')
    @commands.has_permissions(administrator=True)
    @app_commands.describe(amount_to_queue="The new amount of users to queue before a session is created.")
    @app_commands.rename(amount_to_queue="amount-to-queue")
    async def change_q_amount(self, ctx: commands.Context, amount_to_queue: int):
        """Change the amount of users to queue before a session is created."""
        await ctx.defer()
        guild_settings = await utils.get_queueing_settings(ctx.guild.id)
        if not guild_settings:
            await ctx.send("Queueing system is not set up.")
            return

        # Update the amount to queue
        await utils.set_amount_to_queue(ctx.guild.id, amount_to_queue)
        await ctx.send(f"Amount to queue has been changed to {amount_to_queue}.")

        # Logging
        log_channel = ctx.guild.get_channel(guild_settings['log_channel_id'])
        if log_channel:
            log_message = (
                f"Amount to queue changed by {ctx.author.mention} ({ctx.author.id}) to {amount_to_queue}."
            )
            await log_channel.send(log_message)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """
        Listener for voice state updates to manage queueing and session calls.

        Handles:
        - Preventing users from joining the queue channel when the system is paused.
        - Adding users to the queue when they join the queue channel, tracking their position and join time.
        - Removing users from the queue when they leave the queue channel, updating positions for remaining users.
        - Automatically creating a session call voice channel and moving the required number of users when the queue threshold is reached.
        - Notifying users of their queue position and when they are moved to a session call.
        - Logging all relevant events (joins, leaves, session creation, errors) to the configured log channel.
        - Posting session start and end details as embeds in the sessions channel.
        - Monitoring active session call channels and deleting them when empty, logging the event and posting a session summary.
        """

        # Get the queueing system settings for this guild
        guild_settings = await utils.get_queueing_settings(member.guild.id)

        # If not set up or paused, prevent joining the queue channel
        if not guild_settings or guild_settings.get('paused'):
            if after.channel and after.channel.id == guild_settings.get('queue_channel_id'):
                # Move user out and notify them
                await member.move_to(None, reason="Queueing system is paused.")
                await member.send("The queueing system is currently paused. You cannot join the queue channel.")
                # Log the attempt
                log_channel = member.guild.get_channel(guild_settings.get('log_channel_id')) if guild_settings else None
                if log_channel:
                    log_message = (
                        f"[Queue Paused] {member.name}#{member.discriminator} ({member.id}) tried to join the queue channel."
                    )
                    await log_channel.send(log_message)
            return
        
        queue_channel_id = guild_settings.get('queue_channel_id')
        log_channel = member.guild.get_channel(guild_settings['log_channel_id'])

        # Handle member joining the queue channel
        if after.channel and after.channel.id == queue_channel_id:
            # Add member to the queue with their join time and position
            self.queue[member.id] = {
                'member': member,
                'position': len(self.queue) + 1,  # Position in the queue
                'joined_at': discord.utils.utcnow()
            }
            # Notify the member of their position
            await member.send(f"You have joined the queue. Your position is {self.queue[member.id]['position']}.")
            # Log the join event
            if log_channel:
                log_message = (
                    f"[Queue Join] {member.name}#{member.discriminator} ({member.id}) joined the queue. "
                    f"Position: {self.queue[member.id]['position']}"
                )
                await log_channel.send(log_message)
        # Handle member leaving the queue channel
        elif before.channel and before.channel.id == queue_channel_id:
            if member.id in self.queue:
                # Remove member from the queue
                del self.queue[member.id]
                # Update positions of remaining members and notify them
                for idx, (member_id, data) in enumerate(self.queue.items(), start=1):
                    old_position = data['position']
                    data['position'] = idx
                    if data['position'] != old_position:
                        try:
                            await data['member'].send(
                                f"Your position in the queue has changed to {data['position']}."
                            )
                        except Exception:
                            pass
                # Notify the member they have left
                await member.send("You have left the queue.")
                # Log the leave event
                if log_channel:
                    log_message = (
                        f"[Queue Leave] {member.name}#{member.discriminator} ({member.id}) left the queue."
                    )
                    await log_channel.send(log_message)

        # If enough members are queued, create a session call
        if len(self.queue) >= guild_settings.get('amount_to_queue', 0):
            session_calls_category_id = guild_settings.get('session_calls_category_id')
            session_calls_category = member.guild.get_channel(session_calls_category_id)

            if session_calls_category:
                # Select the first N members to move (N = amount_to_queue, here hardcoded as 2)
                members_to_move = list(self.queue.values())[:2]
                member_ids = [data['member'].id for data in members_to_move]

                # Generate a unique session name/id
                ids = 0
                for member_id in member_ids:
                    ids += int(member_id)
                name = utils.number_to_id(((hash(tuple(sorted(member_ids))) & 0xFFFF) << 8) | (int(datetime.now(timezone.utc).timestamp()) & 0xFF))

                # Create the session call voice channel
                session_call_channel = await member.guild.create_voice_channel(
                    f"Session Call - {name}",
                    category=session_calls_category,
                    reason="Creating session call due to queue limit reached"
                )
                # Set permissions for the session call channel
                overwrites = {
                    member.guild.default_role: discord.PermissionOverwrite(read_messages=False, connect=False),
                    member.guild.get_role(guild_settings['admin_role_id']): discord.PermissionOverwrite(read_messages=True, connect=True),
                    session_call_channel.guild.me: discord.PermissionOverwrite(read_messages=True, connect=True)
                }
                # Grant connect/read permissions to each member in the session
                for data in members_to_move:
                    overwrites[data['member']] = discord.PermissionOverwrite(read_messages=True, connect=True)
                await session_call_channel.edit(overwrites=overwrites)

                # Store session info for later tracking/logging
                session_info = {
                    'channel_id': session_call_channel.id,
                    'members': [data['member'] for data in members_to_move],
                    'started_at': discord.utils.utcnow(),
                    'thread_id': None  # Will be set after thread creation
                }
                self.session_calls.append(session_info)

                # Move the selected members to the session call and notify them
                for data in members_to_move:
                    try:
                        await data['member'].move_to(session_call_channel, reason="Moving to session call due to queue limit reached")
                        await data['member'].send(f"You have been moved to a session call: {session_call_channel.mention}")
                        # Remove from queue
                        del self.queue[data['member'].id]
                    except Exception as e:
                        if log_channel:
                            await log_channel.send(f"Error moving {data['member'].mention} to session call: {str(e)}")
                # Log the session call creation
                if log_channel:
                    log_message = (
                        f"[Session Call Created] {len(members_to_move)} members moved to a new session call: "
                        f"{session_call_channel.mention}."
                    )
                    await log_channel.send(log_message)

                # Post an embed in the sessions channel with session details
                sessions_channel = member.guild.get_channel(guild_settings.get('sessions_channel_id'))
                thread = None
                if sessions_channel:
                    member_mentions = ', '.join(m.mention for m in session_info['members'])
                    session_start_embed = discord.Embed(
                        title="Session Started",
                        description=f"{session_call_channel.name}",
                        color=random.randint(0, 0xFFFFFF)
                    )
                    session_start_embed.add_field(name="Members", value=member_mentions, inline=False)
                    session_start_embed.add_field(name="Started at", value=f"<t:{int(session_info['started_at'].timestamp())}:F>", inline=False)
                    await sessions_channel.send(f"{member_mentions}",embed=session_start_embed)

                    message = await sessions_channel.send(".")

                    thread = await message.create_thread(
                        name=f"Session Call - {name}",
                        auto_archive_duration=60,
                        reason="Creating thread for session call discussion"
                    )
                    await message.delete()

                    await thread.send(embed=session_start_embed)

                    # Notify the members in the thread
                    await thread.send(
                        f"Session call created! You can discuss here: {thread.mention}\n"
                        f"Members: {member_mentions}"
                    )
                # Save thread id for later deletion
                if thread:
                    session_info['thread_id'] = thread.id
        
        # Monitor all active session call channels for emptiness
        sessions_channel = member.guild.get_channel(guild_settings.get('sessions_channel_id'))
        for session_info in self.session_calls[:]:
            session_call_channel = member.guild.get_channel(session_info['channel_id'])
            # If the session call channel is empty, end the session
            if session_call_channel and len(session_call_channel.members) == 0:
                ended_at = discord.utils.utcnow()
                duration = ended_at - session_info['started_at']
                member_mentions = ', '.join(m.mention for m in session_info['members'])
                # Create an embed with session end details
                session_end_embed = discord.Embed(
                    title="Session Ended",
                    description=f"{session_call_channel.name}",
                    color=random.randint(0, 0xFFFFFF)
                )
                session_end_embed.add_field(name="Duration", value=str(duration), inline=False)
                session_end_embed.add_field(name="Members", value=member_mentions, inline=False)
                session_end_embed.add_field(name="Started at", value=f"<t:{int(session_info['started_at'].timestamp())}:F>", inline=True)
                session_end_embed.add_field(name="Ended at", value=f"<t:{int(ended_at.timestamp())}:F>", inline=True)
                # Post the embed in the sessions channel
                if sessions_channel:
                    await sessions_channel.send(f"{member_mentions}",embed=session_end_embed)
                # Delete the session call channel
                await session_call_channel.delete(reason="Session call is empty.")
                # Delete the associated thread if it exists
                thread_id = session_info.get('thread_id')
                if thread_id:
                    thread = member.guild.get_thread(thread_id)
                    if thread:
                        try:
                            await thread.delete(reason="Session call ended and channel deleted.")
                        except Exception:
                            pass
                # Remove session from tracking
                self.session_calls.remove(session_info)
                # Log the deletion
                if log_channel:
                    log_message = (
                        f"[Session Call Deleted] {session_call_channel.name} was deleted because it was empty."
                    )
                    await log_channel.send(log_message)
                



async def setup(bot: commands.Bot):
    """Load the QueueingCog."""
    await bot.add_cog(QueueingCog(bot))
