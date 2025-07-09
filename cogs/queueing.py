# Make a bare-bones cog.
import discord
from discord.ext import commands
from settings import bot as settings
from settings import utils
from discord import app_commands
import random
from datetime import datetime, timezone
import asyncio
from discord.ext import tasks
import json
import os


class QueueingCog(commands.Cog):
    """A cog for managing queueing systems."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.guild_loops = {}
        self.bot.loop.create_task(self.start_all_guild_loops())
        self.session_info = {}

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

        # Start the guild loop after setup
        await self.start_guild_loop(ctx.guild)

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
            self.session_info.pop(ctx.guild.id, None)
            await ctx.send("Queueing system settings have been reset.")
        except:
            pass

        # Stop the guild loop after reset
        await self.stop_guild_loop(ctx.guild)

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

        # Get every member in the queue channel and move them out
        queue_channel = ctx.guild.get_channel(guild_settings['queue_channel_id'])
        if queue_channel:
            for member in queue_channel.members:
                try:
                    await member.move_to(None, reason="Queueing system paused.")
                    await member.send("The queueing system has been paused.")
                except Exception as e:
                    if log_channel:
                        await log_channel.send(f"Error moving {member.mention} out of queue channel: {str(e)}")

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
        self.changing = True
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
        guild_settings = await utils.get_queueing_settings(member.guild.id)

        if not guild_settings:
            return

        # Check if the member has joined a voice channel
        if (before.channel is None and after.channel is not None) or (after.channel and after.channel.id == guild_settings['queue_channel_id']):

            # The member has joined a voice channel
            queue_channel = member.guild.get_channel(guild_settings['queue_channel_id']) if guild_settings else None

            if not queue_channel or after.channel.id != queue_channel.id:
                # If the member is not joining the queue channel, do nothing
                return

            # If the queueing system is paused or non-existent, do not allow joining
            # and move the member out of the queue channel
            if not guild_settings or guild_settings.get('paused'):
                await member.move_to(None, reason="Queueing system is paused.")
                await member.send("The queueing system is currently paused. You cannot join the queue channel.")
                return
            
            # Add member to queue dictionary
            if not hasattr(self, "queue"):
                self.queue = {}
            if member.id not in self.queue:
                self.queue[member.id] = {
                    'member': member,
                    'joined_at': discord.utils.utcnow()
                }

            # Save queue to JSON file or delete if empty
            queue_file = f"queues/queue_{member.guild.id}.json"
            if self.queue:
                queue_data = {
                    str(k): {
                        'member_id': v['member'].id,
                        'joined_at': v['joined_at'].isoformat() if hasattr(v['joined_at'], 'isoformat') else str(v['joined_at'])
                    }
                    for k, v in self.queue.items()
                }
                with open(queue_file, "w", encoding="utf-8") as f:
                    json.dump(queue_data, f, indent=2)
                    f.close()

            # Log the join event
            logging_channel = member.guild.get_channel(guild_settings['log_channel_id'])
            if logging_channel:
                log_message = (
                    f"[Queue Join] {member.name}#{member.discriminator} ({member.id}) "
                    f"joined the queue: {after.channel.mention}."
                )
                await logging_channel.send(log_message)

        # Check if the member has left a voice channel
        elif (after.channel is None and before.channel) or before.channel.id == guild_settings['queue_channel_id']:

            queue_channel = member.guild.get_channel(guild_settings['queue_channel_id']) if guild_settings else None

            # If the member is not leaving the queue channel, do nothing
            if not queue_channel or before.channel.id != queue_channel.id:
                return

            # If the queueing system is paused or non-existent, do not do anything
            if not guild_settings or guild_settings.get('paused'):
                return

            # Remove member from queue dictionary
            if hasattr(self, "queue") and member.id in self.queue:
                del self.queue[member.id]

            # Save queue to JSON file
            queue_data = {
                str(k): {
                    'member_id': v['member'].id,
                    'joined_at': v['joined_at'].isoformat() if hasattr(v['joined_at'], 'isoformat') else str(v['joined_at'])
                }
                for k, v in self.queue.items()
            }
            queue_file = f"queues/queue_{member.guild.id}.json"
            with open(queue_file, "w", encoding="utf-8") as f:
                json.dump(queue_data, f, indent=2)
                f.close()

            logging_channel = member.guild.get_channel(guild_settings['log_channel_id'])
            if logging_channel:
                log_message = (
                    f"[Queue Left] {member.name}#{member.discriminator} ({member.id}) "
                    f"left the queue: {before.channel.mention}."
                )
                await logging_channel.send(log_message)

    async def start_all_guild_loops(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            settings = await utils.get_queueing_settings(guild.id)
            if settings and not settings.get("paused"):
                await self.start_guild_loop(guild)

    async def start_guild_loop(self, guild: discord.Guild):
        if guild.id in self.guild_loops:
            return


        async def loop_body():
            try:
                print(f"Loop running for {guild.name}")
                # Main loop
                while True:
                    guild_settings = await utils.get_queueing_settings(guild.id)
                    if not guild_settings:
                        continue  # Skip the loop if settings are deleted
                    paused = guild_settings.get('paused', None)
                    queue_channel = guild.get_channel(guild_settings.get('queue_channel_id', None))
                    amount_to_queue = guild_settings.get('amount_to_queue', None)
                    moderation_role = guild.get_role(guild_settings.get('admin_role_id', None))
                    sessions_channel = guild.get_channel(guild_settings.get('sessions_channel_id', None))
                    sessions_category = guild.get_channel(guild_settings.get('session_calls_category_id', None))

                    # If the queueing system is paused or not set up, skip the loop
                    if not queue_channel or not amount_to_queue or not moderation_role or not sessions_channel or not sessions_category or paused:
                        await asyncio.sleep(2)
                        continue

                    with open(f"queues/queue_{guild.id}.json", "r", encoding="utf-8") as f:
                        try:
                            queue_data = json.load(f)
                        except json.JSONDecodeError:
                            queue_data = {}
                        f.close()

                    amount_in_queue = len(queue_data)

                    if amount_in_queue:
                        if amount_in_queue >= amount_to_queue:
                            # Create a session call
                            session_calls_category = guild.get_channel(guild_settings['session_calls_category_id'])
                            if session_calls_category:
                                # Get the first `amount_to_queue` members from the queue
                                member_ids = list(queue_data.keys())[:amount_to_queue]
                                members_to_move = [guild.get_member(int(member_id)) for member_id in member_ids if guild.get_member(int(member_id))]

                                if members_to_move:
                                    # Create a session call channel
                                    # Make the name of the call based on the members' IDs and current timestamp
                                    ids = 0
                                    for member in members_to_move:
                                        ids += int(member.id)
                                    name = utils.number_to_id(((hash(tuple(sorted([m.id for m in members_to_move]))) & 0xFFFF) << 8) | (int(datetime.now(timezone.utc).timestamp()) & 0xFF))

                                    # Create the session call channel
                                    session_call_channel = await guild.create_voice_channel(
                                        f"Session Call - {name}",
                                        category=session_calls_category,
                                        reason="Creating session call due to queue limit reached"
                                    )
                                    overwrites = {
                                        guild.default_role: discord.PermissionOverwrite(view_channel=True, connect=False),
                                        guild.me: discord.PermissionOverwrite(read_messages=True, connect=True),
                                        moderation_role: discord.PermissionOverwrite(read_messages=True, connect=True)
                                    }
                                    for member in members_to_move:
                                        overwrites[member] = discord.PermissionOverwrite(read_messages=True, connect=True)

                                    # Set permissions for the channel
                                    await session_call_channel.edit(overwrites=overwrites)

                                    # Make a thread in the Sessions channel
                                    thread = await sessions_channel.create_thread(
                                        name=f"Session Chat - {name}",
                                        auto_archive_duration=60,
                                        reason="Creating thread for session call discussion"
                                    )
                                    member_mentions = ', '.join(member.mention for member in members_to_move)
                                    await thread.send(
                                        f"Session call created! You can discuss here: {thread.mention}\n"
                                        f"Members: {member_mentions}"
                                    )

                                    # Move members to the session call channel
                                    for member in members_to_move:
                                        try:
                                            await member.move_to(session_call_channel, reason="Moving to session call due to queue limit reached")
                                            del queue_data[str(member.id)]
                                        except Exception as e:
                                            # Logging error
                                            logging_channel = guild.get_channel(guild_settings['log_channel_id'])
                                            if logging_channel:
                                                await logging_channel.send(f"Error moving {member.mention} to session call: {str(e)}")

                                    self.session_info[name] = {
                                        'channel_id': session_call_channel.id,
                                        'member_ids': [member.id for member in members_to_move],
                                        'started_at': discord.utils.utcnow(),
                                        'thread_id': thread.id
                                    }

                                    session_start_embed = discord.Embed(
                                        title="Session Started",
                                        description=f"{session_call_channel.name}",
                                        color=random.randint(0, 0xFFFFFF)
                                    )
                                    session_start_embed.add_field(name="Members", value=member_mentions, inline=False)
                                    session_start_embed.add_field(name="Started at", value=f"<t:{int(self.session_info[name]['started_at'].timestamp())}:F>", inline=False)
                                    await sessions_channel.send(f"{member_mentions}", embed=session_start_embed)

                                    # Logging for session creation
                                    logging_channel = guild.get_channel(guild_settings['log_channel_id'])
                                    if logging_channel:
                                        log_message = (
                                            f"[Session Call Created] {len(members_to_move)} members moved to a new session call: "
                                            f"{session_call_channel.mention}.\n"
                                            f"Members: {member_mentions}\n"
                                            f"Thread: {thread.mention if thread else 'N/A'}"
                                        )
                                        await logging_channel.send(log_message)
                    else:
                        logging_channel = guild.get_channel(guild_settings['log_channel_id'])
                        for vc in sessions_category.voice_channels:
                            if len(vc.members) == 0:
                                await vc.delete(reason="Session call ended (empty)")
                                if logging_channel:
                                    await logging_channel.send(f"Deleted empty session call channel: {vc.name}")
                                code = vc.name.split(" - ")[1].strip() if " - " in vc.name else vc.name
                                for thread in sessions_channel.threads:
                                    if thread.name == f"Session Chat - {code}":
                                        await thread.delete(reason="Session call thread ended (empty)")
                                        if logging_channel:
                                            await logging_channel.send(f"Deleted empty session call thread: {thread.name}")
                                ended_at = discord.utils.utcnow()
                                session = self.session_info.get(code)
                                if session:
                                    duration = ended_at - session['started_at']
                                    member_mentions = ', '.join(f"<@{m}>" for m in session['member_ids'])
                                    session_end_embed = discord.Embed(
                                        title="Session Ended",
                                        description=f"{vc.name}",
                                        color=random.randint(0, 0xFFFFFF)
                                    )
                                    session_end_embed.add_field(name="Duration", value=str(duration), inline=False)
                                    session_end_embed.add_field(name="Members", value=member_mentions, inline=False)
                                    session_end_embed.add_field(name="Started at", value=f"<t:{int(session['started_at'].timestamp())}:F>", inline=True)
                                    session_end_embed.add_field(name="Ended at", value=f"<t:{int(ended_at.timestamp())}:F>", inline=True)

                                else:
                                    duration = "Unknown"
                                    member_mentions = "Unknown"
                                    session_end_embed = discord.Embed(
                                        title="Session Ended",
                                        description=f"{vc.name}",
                                        color=random.randint(0, 0xFFFFFF)
                                    )
                                    session_end_embed.add_field(name="Duration", value=duration, inline=False)
                                    session_end_embed.add_field(name="Members", value=member_mentions, inline=False)
                                    session_end_embed.add_field(name="Started at", value="Unknown", inline=True)
                                    session_end_embed.add_field(name="Ended at", value=f"<t:{int(ended_at.timestamp())}:F>", inline=True)
                                await sessions_channel.send(f"{member_mentions}", embed=session_end_embed)
                                self.session_info.pop(code, None)
                                await logging_channel.send(f"Session ended: {vc.name} ({vc.id}). Duration: {duration}. Members: {member_mentions}")

                    await asyncio.sleep(2)
            except asyncio.CancelledError:
                print(f"Loop stopped for {guild.name}")

        task = asyncio.create_task(loop_body())
        self.guild_loops[guild.id] = task

    async def stop_guild_loop(self, guild: discord.Guild):
        task = self.guild_loops.get(guild.id)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.guild_loops[guild.id]

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        settings = await utils.get_queueing_settings(guild.id)
        if settings and not settings.get("paused"):
            await self.start_guild_loop(guild)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.stop_guild_loop(guild)




async def setup(bot: commands.Bot):
    """Load the QueueingCog."""
    await bot.add_cog(QueueingCog(bot))
