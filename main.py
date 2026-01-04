# ==================================================================================================
#  PLATINUM ENTERPRISE DISCORD BOT — ULTIMATE E-SPORTS SUITE v6.5
# ==================================================================================================
#  Enhanced with: Anti-Raid/Spam, Full Customization, Advanced Tournaments, Audit Logs & More
# ==================================================================================================

import discord
from discord import app_commands
from discord.ext import tasks, commands
import json
import datetime
import asyncio
import os
import io
import random
import math
import re
import time
from typing import Optional, List, Dict, Union, Any, Literal
from collections import defaultdict

# ==================================================================================================
#  SECTION 1: EDITABLE BRANDING & GLOBAL CONSTANTS
# ==================================================================================================

BOT_TOKEN_HOLDER = os.getenv("DISCORD_TOKEN", "YOUR_TOKEN_HERE")
DATABASE_FILENAME = "data.json"

# Visual Branding
COLOR_PLATINUM_MAIN = 0x00AEEF
COLOR_PLATINUM_SUCCESS = 0x2ECC71
COLOR_PLATINUM_ERROR = 0xE74C3C
COLOR_PLATINUM_WARNING = 0xF1C40F
COLOR_PLATINUM_LOGS = 0x34495E
COLOR_PLATINUM_INFO = 0x3498DB

# Bot Status
DEFAULT_STATUS_TEXT = "E-Sports Tournament Ops"
DEFAULT_STATUS_TYPE = discord.ActivityType.competing

# Messaging
FOOTER_TEXT_CREDIT = "Platinum Enterprise v6.5 | Ultimate E-Sports Suite"
NO_PERM_MESSAGE = "❌ ERROR: You do not have the required Permission Tier to execute this command."

# Anti-Raid/Spam tracking
spam_tracker = defaultdict(list)
raid_tracker = defaultdict(list)

# ==================================================================================================
#  SECTION 2: DATABASE ENGINE
# ==================================================================================================

class PlatinumCoreDB:
    """Handles all persistent data interactions."""
    
    @staticmethod
    def initialize_filesystem():
        """Creates database if it doesn't exist."""
        if not os.path.exists(DATABASE_FILENAME):
            print(f"[SYSTEM] Creating new database: {DATABASE_FILENAME}")
            
            initial_schema = {
                "branding": {
                    "bot_name": "Platinum Enterprise",
                    "embed_color": "#00AEEF",
                    "footer_text": "Platinum Enterprise v6.5",
                    "status_text": "E-Sports Tournament Ops",
                    "status_type": "competing"
                },
                "app_config": {},
                "ticket_panels": {},
                "ticket_customization": {
                    "claim_button_emoji": "🙋‍♂️",
                    "claim_button_text": "Claim Ticket",
                    "close_button_emoji": "🔒",
                    "close_button_text": "Close Ticket",
                    "welcome_message": "Welcome {user}! A staff member will assist you shortly.",
                    "claim_message": "✅ {staff} is now handling this ticket.",
                    "close_confirmation": "⚠️ This will permanently delete the channel. Are you sure?"
                },
                "modal_customization": {
                    "staff_app_questions": [
                        {"label": "Why do you want to join?", "required": True},
                        {"label": "Previous experience?", "required": True},
                        {"label": "Age?", "required": True}
                    ]
                },
                "logs_channel": None,
                "audit_log_channel": None,
                "transcript_channel": None,
                "blacklist": [],
                "staff_stats": {},
                "system_stats": {
                    "total_apps": 0,
                    "total_tickets": 0,
                    "transcripts_sent": 0,
                    "version": "6.5",
                    "maintenance_mode": False,
                    "last_reboot": str(datetime.date.today())
                },
                "xp_system": {
                    "user_xp": {},
                    "xp_per_message": 5,
                    "xp_per_reaction": 2,
                    "xp_per_min_vc": 10,
                    "level_roles": {"10": None, "25": None, "50": None, "100": None}
                },
                "ticket_reopen": {
                    "enabled": True,
                    "grace_period_minutes": 10,
                    "reopenable_channels": {}
                },
                "cooldowns": {},
                "guild_blacklist": {},
                "moderation": {},
                "xp": {},
                "staff_recruitment": {},
                "permissions_tiers": {
                    "system_admins": [],
                    "senior_mods": [],
                    "regular_mods": [],
                    "trial_mods": [],
                    "app_reviewers": [],
                    "tournament_managers": []
                },
                "xp_engine": {
                    "global_enabled": True,
                    "level_up_messages": True,
                    "min_gain": 15,
                    "max_gain": 30,
                    "cooldown_seconds": 60,
                    "user_data": {}
                },
                "recruitment_system": {
                    "pending_channel": None,
                    "accepted_channel": None,
                    "denied_channel": None,
                    "referral_channel": None,
                    "stats": {"total_apps": 0, "total_accepted": 0, "total_denied": 0}
                },
                "ticket_system": {
                    "panels": {},
                    "active_tickets": {},
                    "transcript_history": []
                },
                "tournaments": {
                    "active_tournaments": {},
                    "registration_open": False,
                    "allowed_roles": [],
                    "banned_roles": [],
                    "registered_teams": [],
                    "max_team_size": 5,
                    "min_team_size": 1
                },
                "security_settings": {
                    "anti_spam_enabled": True,
                    "anti_raid_enabled": True,
                    "max_mentions": 5,
                    "max_messages_per_10s": 5,
                    "join_threshold_per_minute": 10,
                    "spam_mute_duration": 300,
                    "auto_ban_raiders": False
                },
                "channels": {
                    "transcripts": None,
                    "mod_logs": None,
                    "join_logs": None
                },
                "auto_mod": {
                    "delete_invite_links": False,
                    "delete_bad_words": False,
                    "bad_words_list": [],
                    "whitelist_channels": []
                }
            }
            
            with open(DATABASE_FILENAME, "w", encoding="utf-8") as f:
                json.dump(initial_schema, data_file, indent=4)
                print("[SYSTEM] Database initialized successfully.")

    @staticmethod
    def load_full_database() -> dict:
        """Loads the entire database."""
        PlatinumCoreDB.initialize_filesystem()
        try:
            with open(DATABASE_FILENAME, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to read database: {e}")
            return {}

    @staticmethod
    def save_database(data_dict: dict):
        """Saves the database."""
        try:
            with open(DATABASE_FILENAME, "w", encoding="utf-8") as f:
                json.dump(data_dict, f, indent=4)
        except Exception as e:
            print(f"[ERROR] Failed to save database: {e}")

# ==================================================================================================
#  SECTION 3: ANTI-SPAM & ANTI-RAID SYSTEM
# ==================================================================================================

class SecurityEngine:
    """Handles anti-spam and anti-raid detection."""
    
    @staticmethod
    async def check_spam(message: discord.Message) -> bool:
        """Detects message spam."""
        db = PlatinumCoreDB.load_full_database()
        if not db["security_settings"]["anti_spam_enabled"]:
            return False
        
        user_id = message.author.id
        current_time = time.time()
        
        # Track messages
        spam_tracker[user_id].append(current_time)
        spam_tracker[user_id] = [t for t in spam_tracker[user_id] if current_time - t < 10]
        
        max_msgs = db["security_settings"]["max_messages_per_10s"]
        
        if len(spam_tracker[user_id]) > max_msgs:
            # Spam detected
            try:
                mute_duration = db["security_settings"]["spam_mute_duration"]
                await message.author.timeout(datetime.timedelta(seconds=mute_duration), reason="Auto-moderation: Spam detected")
                await message.channel.send(f"⚠️ {message.author.mention} has been timed out for spam ({mute_duration}s).", delete_after=5)
                
                # Log to audit
                await SecurityEngine.log_action(message.guild, "SPAM_DETECTION", 
                    f"User {message.author} ({message.author.id}) timed out for spam")
                return True
            except:
                pass
        
        return False
    
    @staticmethod
    async def check_raid(member: discord.Member):
        """Detects potential raids."""
        db = PlatinumCoreDB.load_full_database()
        if not db["security_settings"]["anti_raid_enabled"]:
            return
        
        guild_id = member.guild.id
        current_time = time.time()
        
        raid_tracker[guild_id].append(current_time)
        raid_tracker[guild_id] = [t for t in raid_tracker[guild_id] if current_time - t < 60]
        
        threshold = db["security_settings"]["join_threshold_per_minute"]
        
        if len(raid_tracker[guild_id]) > threshold:
            # Raid detected
            await SecurityEngine.log_action(member.guild, "RAID_DETECTION",
                f"⚠️ **RAID ALERT:** {len(raid_tracker[guild_id])} joins in the last minute!")
            
            if db["security_settings"]["auto_ban_raiders"]:
                try:
                    await member.ban(reason="Auto-moderation: Raid detected")
                except:
                    pass
    
    @staticmethod
    async def log_action(guild: discord.Guild, action_type: str, description: str):
        """Logs security actions to audit log."""
        db = PlatinumCoreDB.load_full_database()
        audit_channel_id = db.get("audit_log_channel")
        
        if audit_channel_id:
            channel = guild.get_channel(int(audit_channel_id))
            if channel:
                embed = discord.Embed(
                    title=f"🛡️ Security Log: {action_type}",
                    description=description,
                    color=COLOR_PLATINUM_WARNING,
                    timestamp=datetime.datetime.now()
                )
                await channel.send(embed=embed)

# ==================================================================================================
#  SECTION 4: XP ENGINE
# ==================================================================================================

class PlatinumXPEngine:
    """XP and leveling system."""
    
    @staticmethod
    def calculate_level_requirement(current_level: int) -> int:
        return (100 * (current_level ** 2)) + (200 * current_level) + 500

    @staticmethod
    async def process_message_xp(member: discord.Member):
        if member.bot:
            return

        db = PlatinumCoreDB.load_full_database()
        xp_config = db.get("xp_engine", {})
        
        if not xp_config.get("global_enabled", False):
            return

        user_id_str = str(member.id)
        current_timestamp = time.time()
        
        if user_id_str not in xp_config["user_data"]:
            xp_config["user_data"][user_id_str] = {
                "xp": 0, "level": 1, "total_xp": 0, "last_xp_time": 0
            }

        user_entry = xp_config["user_data"][user_id_str]
        cooldown_period = xp_config.get("cooldown_seconds", 60)
        time_since_last = current_timestamp - user_entry.get("last_xp_time", 0)
        
        if time_since_last < cooldown_period:
            return

        min_gain = xp_config.get("min_gain", 15)
        max_gain = xp_config.get("max_gain", 30)
        awarded_xp = random.randint(min_gain, max_gain)
        
        user_entry["xp"] += awarded_xp
        user_entry["total_xp"] += awarded_xp
        user_entry["last_xp_time"] = current_timestamp
        
        current_lv = user_entry["level"]
        required_for_next = PlatinumXPEngine.calculate_level_requirement(current_lv)
        
        if user_entry["xp"] >= required_for_next:
            user_entry["level"] += 1
            user_entry["xp"] = 0
            
            if xp_config.get("level_up_messages", True):
                try:
                    await member.send(f"🎊 **LEVEL UP!** You've reached Level {user_entry['level']} in {member.guild.name}!")
                except:
                    pass
        
        db["xp_engine"]["user_data"][user_id_str] = user_entry
        PlatinumCoreDB.save_database(db)

# ==================================================================================================
#  SECTION 5: STAFF APPLICATION SYSTEM
# ==================================================================================================

class StaffApplicationModal(discord.ui.Modal, title="Staff Application"):
    """Dynamic staff application modal."""
    
    def __init__(self):
        super().__init__()
        db = PlatinumCoreDB.load_full_database()
        questions = db.get("modal_customization", {}).get("staff_app_questions", [])
        
        # Add default questions if none configured
        if not questions:
            questions = [
                {"label": "Why do you want to join our team?", "required": True},
                {"label": "Previous moderation experience?", "required": True},
                {"label": "How old are you?", "required": True}
            ]
        
        # Add up to 5 questions (Discord limit)
        for i, q in enumerate(questions[:5]):
            text_input = discord.ui.TextInput(
                label=q["label"],
                style=discord.TextStyle.paragraph,
                required=q.get("required", True),
                max_length=500
            )
            self.add_item(text_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        db = PlatinumCoreDB.load_full_database()
        pending_channel_id = db["recruitment_system"].get("pending_channel")
        
        if not pending_channel_id:
            return await interaction.followup.send("❌ Staff applications are not configured yet.", ephemeral=True)
        
        pending_channel = interaction.guild.get_channel(int(pending_channel_id))
        if not pending_channel:
            return await interaction.followup.send("❌ Application channel not found.", ephemeral=True)
        
        # Build application embed
        app_embed = discord.Embed(
            title="📋 New Staff Application",
            color=COLOR_PLATINUM_INFO,
            timestamp=datetime.datetime.now()
        )
        app_embed.set_thumbnail(url=interaction.user.display_avatar.url)
        app_embed.add_field(name="Applicant", value=f"{interaction.user.mention} ({interaction.user.id})", inline=False)
        
        # Add answers
        for i, item in enumerate(self.children):
            app_embed.add_field(name=f"Q{i+1}: {item.label}", value=item.value or "No answer", inline=False)
        
        # Send to pending channel with review buttons
        msg = await pending_channel.send(embed=app_embed, view=StaffReviewView(interaction.user.id))
        
        # Update stats
        db["recruitment_system"]["stats"]["total_apps"] += 1
        db["system_stats"]["total_apps"] += 1
        PlatinumCoreDB.save_database(db)
        
        await interaction.followup.send("✅ Your application has been submitted! Please wait for a response.", ephemeral=True)

class RoleSelectionModal(discord.ui.Modal, title="Select Role to Grant"):
    """Modal for selecting which role to give accepted applicant."""
    
    role_id = discord.ui.TextInput(
        label="Role ID to Grant",
        placeholder="Paste the Role ID here (right-click role -> Copy ID)",
        required=True,
        min_length=17,
        max_length=20
    )
    
    acceptance_note = discord.ui.TextInput(
        label="Acceptance Message",
        style=discord.TextStyle.paragraph,
        placeholder="e.g., Welcome to the team! We're excited to have you.",
        required=True,
        max_length=500
    )
    
    def __init__(self, applicant_id: int, original_msg: discord.Message):
        super().__init__()
        self.applicant_id = applicant_id
        self.original_msg = original_msg
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        db = PlatinumCoreDB.load_full_database()
        guild = interaction.guild
        applicant = guild.get_member(self.applicant_id)
        
        try:
            role = guild.get_role(int(self.role_id.value))
            if not role:
                return await interaction.followup.send("❌ Invalid Role ID provided.")
        except ValueError:
            return await interaction.followup.send("❌ Role ID must be numeric.")
        
        # Update embed
        accept_embed = self.original_msg.embeds[0].copy()
        accept_embed.color = COLOR_PLATINUM_SUCCESS
        accept_embed.add_field(name="✅ DECISION", value="**ACCEPTED**", inline=False)
        accept_embed.add_field(name="Reviewed By", value=interaction.user.mention, inline=True)
        accept_embed.add_field(name="Role Granted", value=role.mention, inline=True)
        accept_embed.add_field(name="Note", value=self.acceptance_note.value, inline=False)
        
        await self.original_msg.edit(embed=accept_embed, view=None)
        
        # Log to accepted channel
        accepted_channel_id = db["recruitment_system"].get("accepted_channel")
        if accepted_channel_id:
            channel = guild.get_channel(int(accepted_channel_id))
            if channel:
                await channel.send(embed=accept_embed)
        
        # Grant role and notify
        if applicant:
            try:
                await applicant.add_roles(role, reason=f"Accepted by {interaction.user}")
                await applicant.send(
                    f"🎉 **Congratulations!** Your application to {guild.name} has been **ACCEPTED**!\n\n"
                    f"**Role:** {role.name}\n"
                    f"**Message:** {self.acceptance_note.value}"
                )
            except Exception as e:
                await interaction.followup.send(f"⚠️ Processed but couldn't grant role/DM: {e}")
        
        # Update stats
        db["recruitment_system"]["stats"]["total_accepted"] += 1
        PlatinumCoreDB.save_database(db)
        
        await interaction.followup.send(f"✅ Successfully accepted <@{self.applicant_id}>!")

class DenyReasonModal(discord.ui.Modal, title="Denial Reason"):
    """Modal for denying applications with reason."""
    
    reason = discord.ui.TextInput(
        label="Reason for Denial",
        style=discord.TextStyle.paragraph,
        placeholder="Explain why this application was rejected...",
        required=True,
        max_length=500
    )
    
    def __init__(self, applicant_id: int, original_msg: discord.Message):
        super().__init__()
        self.applicant_id = applicant_id
        self.original_msg = original_msg
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        db = PlatinumCoreDB.load_full_database()
        guild = interaction.guild
        applicant = guild.get_member(self.applicant_id)
        
        # Update embed
        deny_embed = self.original_msg.embeds[0].copy()
        deny_embed.color = COLOR_PLATINUM_ERROR
        deny_embed.add_field(name="❌ DECISION", value="**DENIED**", inline=False)
        deny_embed.add_field(name="Reviewed By", value=interaction.user.mention, inline=True)
        deny_embed.add_field(name="Reason", value=self.reason.value, inline=False)
        
        await self.original_msg.edit(embed=deny_embed, view=None)
        
        # Log to denied channel
        denied_channel_id = db["recruitment_system"].get("denied_channel")
        if denied_channel_id:
            channel = guild.get_channel(int(denied_channel_id))
            if channel:
                await channel.send(embed=deny_embed)
        
        # Notify applicant
        if applicant:
            try:
                await applicant.send(
                    f"❌ Your application to {guild.name} has been **DENIED**.\n\n"
                    f"**Reason:** {self.reason.value}\n\n"
                    f"You may reapply in the future if circumstances change."
                )
            except:
                pass
        
        # Update stats
        db["recruitment_system"]["stats"]["total_denied"] += 1
        PlatinumCoreDB.save_database(db)
        
        await interaction.followup.send(f"✅ Application denied with feedback sent to user.")

class StaffReviewView(discord.ui.View):
    """Review buttons for staff applications."""
    
    def __init__(self, applicant_id: int):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id
    
    @discord.ui.button(label="ACCEPT", style=discord.ButtonStyle.success, emoji="✅", custom_id="staff_accept_btn")
    async def accept_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        db = PlatinumCoreDB.load_full_database()
        
        # Check permissions
        user_id = interaction.user.id
        is_reviewer = (
            user_id in db["permissions_tiers"]["app_reviewers"] or
            user_id in db["permissions_tiers"]["system_admins"] or
            user_id == interaction.guild.owner_id
        )
        
        if not is_reviewer:
            return await interaction.response.send_message("❌ You don't have permission to review applications.", ephemeral=True)
        
        await interaction.response.send_modal(RoleSelectionModal(self.applicant_id, interaction.message))
    
    @discord.ui.button(label="DENY", style=discord.ButtonStyle.danger, emoji="❌", custom_id="staff_deny_btn")
    async def deny_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        db = PlatinumCoreDB.load_full_database()
        
        user_id = interaction.user.id
        is_reviewer = (
            user_id in db["permissions_tiers"]["app_reviewers"] or
            user_id in db["permissions_tiers"]["system_admins"] or
            user_id == interaction.guild.owner_id
        )
        
        if not is_reviewer:
            return await interaction.response.send_message("❌ You don't have permission to review applications.", ephemeral=True)
        
        await interaction.response.send_modal(DenyReasonModal(self.applicant_id, interaction.message))

# ==================================================================================================
#  SECTION 6: TICKET SYSTEM
# ==================================================================================================

class PlatinumTicketActions(discord.ui.View):
    """Ticket control panel."""
    
    def __init__(self):
        super().__init__(timeout=None)
        
        db = PlatinumCoreDB.load_full_database()
        custom = db.get("ticket_customization", {})
        
        # Customizable claim button
        self.claim_btn = discord.ui.Button(
            label=custom.get("claim_button_text", "Claim Ticket"),
            style=discord.ButtonStyle.success,
            emoji=custom.get("claim_button_emoji", "🙋‍♂️"),
            custom_id="ticket_claim_persistent"
        )
        self.claim_btn.callback = self.claim_callback
        self.add_item(self.claim_btn)
        
        # Customizable close button
        self.close_btn = discord.ui.Button(
            label=custom.get("close_button_text", "Close Ticket"),
            style=discord.ButtonStyle.danger,
            emoji=custom.get("close_button_emoji", "🔒"),
            custom_id="ticket_close_persistent"
        )
        self.close_btn.callback = self.close_callback
        self.add_item(self.close_btn)
    
    async def claim_callback(self, interaction: discord.Interaction):
        db = PlatinumCoreDB.load_full_database()
        custom = db.get("ticket_customization", {})
        
        # Check permissions
        user_id = interaction.user.id
        is_staff = (
            user_id in db["permissions_tiers"]["regular_mods"] or
            user_id in db["permissions_tiers"]["trial_mods"] or
            user_id in db["permissions_tiers"]["senior_mods"] or
            user_id in db["permissions_tiers"]["system_admins"] or
            user_id == interaction.guild.owner_id
        )
        
        if not is_staff:
            return await interaction.response.send_message("❌ You need staff permissions to claim tickets.", ephemeral=True)
        
        self.claim_btn.label = f"Claimed by {interaction.user.name}"
        self.claim_btn.disabled = True
        self.claim_btn.style = discord.ButtonStyle.secondary
        
        claim_msg = custom.get("claim_message", "✅ {staff} is now handling this ticket.").format(staff=interaction.user.mention)
        
        await interaction.message.edit(view=self)
        await interaction.response.send_message(claim_msg)
    
    async def close_callback(self, interaction: discord.Interaction):
        db = PlatinumCoreDB.load_full_database()
        custom = db.get("ticket_customization", {})
        
        confirm_view = discord.ui.View(timeout=60)
        confirm_btn = discord.ui.Button(label="Confirm Close", style=discord.ButtonStyle.danger, emoji="⚠️")
        
        async def do_close(itn: discord.Interaction):
            await itn.response.send_message("📁 Generating transcript and closing...")
            
            # Generate transcript
            transcript = f"=== TICKET TRANSCRIPT ===\nChannel: {itn.channel.name}\nClosed by: {itn.user}\nDate: {datetime.datetime.now()}\n\n"
            
            async for msg in itn.channel.history(limit=None, oldest_first=True):
                timestamp = msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
                transcript += f"[{timestamp}] {msg.author}: {msg.content}\n"
            
            # Send to transcript channel
            transcript_channel_id = db.get("transcript_channel") or db.get("channels", {}).get("transcripts")
            if transcript_channel_id:
                channel = itn.guild.get_channel(int(transcript_channel_id))
                if channel:
                    file_data = io.BytesIO(transcript.encode("utf-8"))
                    discord_file = discord.File(file_data, filename=f"transcript-{itn.channel.name}.txt")
                    
                    log_embed = discord.Embed(
                        title="📋 Ticket Transcript",
                        description=f"Ticket: {itn.channel.name}\nClosed by: {itn.user.mention}",
                        color=COLOR_PLATINUM_LOGS,
                        timestamp=datetime.datetime.now()
                    )
                    await channel.send(embed=log_embed, file=discord_file)
            
            await asyncio.sleep(3)
            await itn.channel.delete(reason=f"Ticket closed by {itn.user}")
        
        confirm_btn.callback = do_close
        confirm_view.add_item(confirm_btn)
        
        confirmation_text = custom.get("close_confirmation", "⚠️ This will permanently delete the channel. Are you sure?")
        await interaction.response.send_message(confirmation_text, view=confirm_view, ephemeral=True)

class PlatinumDynamicButton(discord.ui.Button):
    """Dynamic ticket button."""
    
    def __init__(self, label: str, emoji: str, style: discord.ButtonStyle, category_id: int):
        super().__init__(
            label=label,
            emoji=emoji,
            style=style,
            custom_id=f"ticket_btn_{label.lower().replace(' ', '_')}"
        )
        self.category_id = category_id
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        category = guild.get_channel(self.category_id)
        
        if not category:
            return await interaction.followup.send("❌ Category not found.")
        
        db = PlatinumCoreDB.load_full_database()
        custom = db.get("ticket_customization", {})
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }
        
        channel_name = f"{self.label.replace(' ', '-').lower()}-{interaction.user.name}"
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites
        )
        
        welcome_text = custom.get("welcome_message", "Welcome {user}! A staff member will assist you shortly.").format(user=interaction.user.mention)
        
        welcome_embed = discord.Embed(
            title=f"🎫 {self.label}",
            description=welcome_text,
            color=COLOR_PLATINUM_MAIN
        )
        
        await ticket_channel.send(embed=welcome_embed, view=PlatinumTicketActions())
        await interaction.followup.send(f"✅ Ticket created: {ticket_channel.mention}")
        
        # Update stats
        db["system_stats"]["total_tickets"] += 1
        PlatinumCoreDB.save_database(db)

class PlatinumPanelView(discord.ui.View):
    """Ticket panel view."""
    
    def __init__(self, button_list: list):
        super().__init__(timeout=None)
        
        for btn in button_list:
            color = btn.get("hex2", "grey").lower()
            cat_id = btn.get("cat", 0)
            
            style = discord.ButtonStyle.secondary
            if color == "blue": style = discord.ButtonStyle.primary
            elif color == "green": style = discord.ButtonStyle.success
            elif color == "red": style = discord.ButtonStyle.danger
            
            self.add_item(PlatinumDynamicButton(
                label=btn.get("label", "Ticket"),
                emoji=btn.get("emoji", "🎫"),
                style=style,
                category_id=int(cat_id)
            ))

# ==================================================================================================
#  SECTION 7: TOURNAMENT SYSTEM
# ==================================================================================================

class TournamentCreateModal(discord.ui.Modal, title="Create Tournament"):
    """Modal for creating tournaments."""
    
    name = discord.ui.TextInput(label="Tournament Name", required=True, max_length=100)
    description = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, required=True)
    max_teams = discord.ui.TextInput(label="Max Teams", placeholder="Leave blank for unlimited", required=False)
    team_size = discord.ui.TextInput(label="Team Size", placeholder="e.g., 5", required=True)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        db = PlatinumCoreDB.load_full_database()
        
        tournament_id = str(int(time.time()))
        
        db["tournaments"]["active_tournaments"][tournament_id] = {
            "name": self.name.value,
            "description": self.description.value,
            "creator": interaction.user.id,
            "max_teams": int(self.max_teams.value) if self.max_teams.value else None,
            "team_size": int(self.team_size.value),
            "registered_teams": [],
            "blacklisted_users": [],
            "whitelisted_roles": [],
            "registration_open": True,
            "created_at": str(datetime.datetime.now())
        }
        
        PlatinumCoreDB.save_database(db)
        
        await interaction.followup.send(
            f"✅ Tournament **{self.name.value}** created!\n"
            f"Tournament ID: `{tournament_id}`\n\n"
            f"Use `/tournament manage id:{tournament_id}` to configure it further."
        )

class TournamentRegistrationModal(discord.ui.Modal, title="Register Team"):
    """Modal for team registration."""
    
    team_name = discord.ui.TextInput(label="Team Name", required=True)
    roster = discord.ui.TextInput(label="Player List", style=discord.TextStyle.paragraph, 
                                  placeholder="Player 1\nPlayer 2\nPlayer 3...", required=True)
    contact = discord.ui.TextInput(label="Contact Info", placeholder="Discord Tag or Email", required=True)
    
    def __init__(self, tournament_id: str):
        super().__init__()
        self.tournament_id = tournament_id
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        db = PlatinumCoreDB.load_full_database()
        tournament = db["tournaments"]["active_tournaments"].get(self.tournament_id)
        
        if not tournament:
            return await interaction.followup.send("❌ Tournament not found.")
        
        if not tournament["registration_open"]:
            return await interaction.followup.send("❌ Registration is closed.")
        
        # Check blacklist
        if interaction.user.id in tournament["blacklisted_users"]:
            return await interaction.followup.send("❌ You are banned from this tournament.")
        
        # Check whitelist
        if tournament["whitelisted_roles"]:
            user_roles = [r.id for r in interaction.user.roles]
            has_access = any(rid in user_roles for rid in tournament["whitelisted_roles"])
            if not has_access:
                return await interaction.followup.send("❌ You don't have the required role to register.")
        
        # Check max teams
        if tournament["max_teams"] and len(tournament["registered_teams"]) >= tournament["max_teams"]:
            return await interaction.followup.send("❌ Tournament is full.")
        
        team_data = {
            "name": self.team_name.value,
            "roster": self.roster.value,
            "contact": self.contact.value,
            "leader": interaction.user.id,
            "registered_at": str(datetime.datetime.now())
        }
        
        tournament["registered_teams"].append(team_data)
        PlatinumCoreDB.save_database(db)
        
        await interaction.followup.send(f"✅ Team **{self.team_name.value}** registered successfully!")

# ==================================================================================================
#  SECTION 8: SETUP COMMANDS
# ==================================================================================================

class SetupCog(commands.Cog):
    """Setup and configuration commands."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="setup_recruitment", description="Configure staff recruitment channels")
    @app_commands.describe(
        pending="Pending applications",
        accepted="Accepted applications", 
        denied="Denied applications",
        referral="Referral tracking"
    )
    async def setup_recruitment(self, interaction: discord.Interaction, 
                               pending: discord.TextChannel, 
                               accepted: discord.TextChannel,
                               denied: discord.TextChannel,
                               referral: discord.TextChannel):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(NO_PERM_MESSAGE, ephemeral=True)
        
        db = PlatinumCoreDB.load_full_database()
        db["recruitment_system"]["pending_channel"] = pending.id
        db["recruitment_system"]["accepted_channel"] = accepted.id
        db["recruitment_system"]["denied_channel"] = denied.id
        db["recruitment_system"]["referral_channel"] = referral.id
        PlatinumCoreDB.save_database(db)
        
        embed = discord.Embed(title="✅ Recruitment Configured", color=COLOR_PLATINUM_SUCCESS)
        embed.add_field(name="Pending", value=pending.mention)
        embed.add_field(name="Accepted", value=accepted.mention)
        embed.add_field(name="Denied", value=denied.mention)
        embed.add_field(name="Referrals", value=referral.mention)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="setup_logs", description="Configure logging channels")
    @app_commands.describe(
        transcripts="Ticket transcripts",
        audit="Audit logs",
        moderation="Moderation logs"
    )
    async def setup_logs(self, interaction: discord.Interaction,
                        transcripts: discord.TextChannel,
                        audit: discord.TextChannel,
                        moderation: discord.TextChannel):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(NO_PERM_MESSAGE, ephemeral=True)
        
        db = PlatinumCoreDB.load_full_database()
        db["transcript_channel"] = transcripts.id
        db["audit_log_channel"] = audit.id
        db["channels"]["mod_logs"] = moderation.id
        PlatinumCoreDB.save_database(db)
        
        await interaction.response.send_message("✅ Logging channels configured!")
    
    @app_commands.command(name="grant_permission", description="Grant permission tier to a user (Owner Only)")
    @app_commands.describe(
        user="User to grant permission to",
        tier="Permission tier to grant"
    )
    @app_commands.choices(tier=[
        app_commands.Choice(name="System Admin", value="system_admins"),
        app_commands.Choice(name="Senior Moderator", value="senior_mods"),
        app_commands.Choice(name="Regular Moderator", value="regular_mods"),
        app_commands.Choice(name="Trial Moderator", value="trial_mods"),
        app_commands.Choice(name="App Reviewer", value="app_reviewers"),
        app_commands.Choice(name="Tournament Manager", value="tournament_managers")
    ])
    async def grant_permission(self, interaction: discord.Interaction, user: discord.Member, tier: str):
        if interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("❌ Owner Only command.", ephemeral=True)
        
        db = PlatinumCoreDB.load_full_database()
        
        if user.id not in db["permissions_tiers"][tier]:
            db["permissions_tiers"][tier].append(user.id)
            PlatinumCoreDB.save_database(db)
            await interaction.response.send_message(f"✅ Granted **{tier.replace('_', ' ').title()}** to {user.mention}")
        else:
            await interaction.response.send_message(f"ℹ️ {user.mention} already has this permission.", ephemeral=True)
    
    @app_commands.command(name="revoke_permission", description="Revoke permission tier from a user (Owner Only)")
    @app_commands.describe(user="User to revoke from", tier="Permission tier")
    @app_commands.choices(tier=[
        app_commands.Choice(name="System Admin", value="system_admins"),
        app_commands.Choice(name="Senior Moderator", value="senior_mods"),
        app_commands.Choice(name="Regular Moderator", value="regular_mods"),
        app_commands.Choice(name="Trial Moderator", value="trial_mods"),
        app_commands.Choice(name="App Reviewer", value="app_reviewers"),
        app_commands.Choice(name="Tournament Manager", value="tournament_managers")
    ])
    async def revoke_permission(self, interaction: discord.Interaction, user: discord.Member, tier: str):
        if interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("❌ Owner Only command.", ephemeral=True)
        
        db = PlatinumCoreDB.load_full_database()
        
        if user.id in db["permissions_tiers"][tier]:
            db["permissions_tiers"][tier].remove(user.id)
            PlatinumCoreDB.save_database(db)
            await interaction.response.send_message(f"✅ Revoked **{tier.replace('_', ' ').title()}** from {user.mention}")
        else:
            await interaction.response.send_message(f"ℹ️ {user.mention} doesn't have this permission.", ephemeral=True)

# ==================================================================================================
#  SECTION 9: MODERATION COMMANDS
# ==================================================================================================

class ModerationCog(commands.Cog):
    """Moderation and utility commands."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="whois", description="View detailed user information")
    async def whois(self, interaction: discord.Interaction, user: discord.Member):
        db = PlatinumCoreDB.load_full_database()
        xp_data = db["xp_engine"]["user_data"].get(str(user.id), {"level": 1, "xp": 0})
        
        embed = discord.Embed(title=f"User Info: {user}", color=COLOR_PLATINUM_INFO)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="ID", value=user.id)
        embed.add_field(name="Created", value=user.created_at.strftime("%Y-%m-%d"))
        embed.add_field(name="Joined", value=user.joined_at.strftime("%Y-%m-%d"))
        embed.add_field(name="Level", value=f"{xp_data['level']} ({xp_data['xp']} XP)")
        embed.add_field(name="Roles", value=" ".join([r.mention for r in user.roles[1:]]) or "None", inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="warn", description="Warn a user")
    @app_commands.describe(user="User to warn", reason="Reason for warning")
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        db = PlatinumCoreDB.load_full_database()
        
        is_mod = (
            interaction.user.id in db["permissions_tiers"]["regular_mods"] or
            interaction.user.id in db["permissions_tiers"]["senior_mods"] or
            interaction.user.id in db["permissions_tiers"]["system_admins"] or
            interaction.user.id == interaction.guild.owner_id
        )
        
        if not is_mod:
            return await interaction.response.send_message(NO_PERM_MESSAGE, ephemeral=True)
        
        try:
            await user.send(f"⚠️ You have been warned in **{interaction.guild.name}**\n**Reason:** {reason}")
        except:
            pass
        
        await SecurityEngine.log_action(interaction.guild, "WARNING", 
            f"**User:** {user.mention} ({user.id})\n**Moderator:** {interaction.user.mention}\n**Reason:** {reason}")
        
        await interaction.response.send_message(f"✅ Warned {user.mention} for: {reason}")
    
    @app_commands.command(name="kick", description="Kick a user")
    @app_commands.describe(user="User to kick", reason="Reason")
    async def kick_user(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        db = PlatinumCoreDB.load_full_database()
        
        is_mod = (
            interaction.user.id in db["permissions_tiers"]["senior_mods"] or
            interaction.user.id in db["permissions_tiers"]["system_admins"] or
            interaction.user.id == interaction.guild.owner_id
        )
        
        if not is_mod:
            return await interaction.response.send_message(NO_PERM_MESSAGE, ephemeral=True)
        
        try:
            await user.send(f"👢 You have been kicked from **{interaction.guild.name}**\n**Reason:** {reason}")
        except:
            pass
        
        await user.kick(reason=f"{interaction.user}: {reason}")
        await SecurityEngine.log_action(interaction.guild, "KICK",
            f"**User:** {user.mention} ({user.id})\n**Moderator:** {interaction.user.mention}\n**Reason:** {reason}")
        
        await interaction.response.send_message(f"✅ Kicked {user.mention}")
    
    @app_commands.command(name="ban", description="Ban a user")
    @app_commands.describe(user="User to ban", reason="Reason", delete_messages="Days of messages to delete (0-7)")
    async def ban_user(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason", delete_messages: int = 0):
        db = PlatinumCoreDB.load_full_database()
        
        is_mod = (
            interaction.user.id in db["permissions_tiers"]["senior_mods"] or
            interaction.user.id in db["permissions_tiers"]["system_admins"] or
            interaction.user.id == interaction.guild.owner_id
        )
        
        if not is_mod:
            return await interaction.response.send_message(NO_PERM_MESSAGE, ephemeral=True)
        
        try:
            await user.send(f"🔨 You have been banned from **{interaction.guild.name}**\n**Reason:** {reason}")
        except:
            pass
        
        await user.ban(reason=f"{interaction.user}: {reason}", delete_message_days=min(delete_messages, 7))
        await SecurityEngine.log_action(interaction.guild, "BAN",
            f"**User:** {user.mention} ({user.id})\n**Moderator:** {interaction.user.mention}\n**Reason:** {reason}")
        
        await interaction.response.send_message(f"✅ Banned {user.mention}")
    
    @app_commands.command(name="timeout", description="Timeout a user")
    @app_commands.describe(user="User to timeout", duration="Duration in minutes", reason="Reason")
    async def timeout_user(self, interaction: discord.Interaction, user: discord.Member, duration: int, reason: str = "No reason"):
        db = PlatinumCoreDB.load_full_database()
        
        is_mod = (
            interaction.user.id in db["permissions_tiers"]["regular_mods"] or
            interaction.user.id in db["permissions_tiers"]["senior_mods"] or
            interaction.user.id in db["permissions_tiers"]["system_admins"] or
            interaction.user.id == interaction.guild.owner_id
        )
        
        if not is_mod:
            return await interaction.response.send_message(NO_PERM_MESSAGE, ephemeral=True)
        
        await user.timeout(datetime.timedelta(minutes=duration), reason=f"{interaction.user}: {reason}")
        await SecurityEngine.log_action(interaction.guild, "TIMEOUT",
            f"**User:** {user.mention} ({user.id})\n**Duration:** {duration} minutes\n**Moderator:** {interaction.user.mention}\n**Reason:** {reason}")
        
        await interaction.response.send_message(f"✅ Timed out {user.mention} for {duration} minutes")
    
    @app_commands.command(name="purge", description="Delete messages")
    @app_commands.describe(amount="Number of messages to delete (max 100)")
    async def purge(self, interaction: discord.Interaction, amount: int):
        db = PlatinumCoreDB.load_full_database()
        
        is_mod = (
            interaction.user.id in db["permissions_tiers"]["regular_mods"] or
            interaction.user.id in db["permissions_tiers"]["senior_mods"] or
            interaction.user.id in db["permissions_tiers"]["system_admins"] or
            interaction.user.id == interaction.guild.owner_id
        )
        
        if not is_mod:
            return await interaction.response.send_message(NO_PERM_MESSAGE, ephemeral=True)
        
        amount = min(amount, 100)
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"✅ Deleted {len(deleted)} messages")
    
    @app_commands.command(name="lockdown", description="Lock or unlock a channel")
    @app_commands.describe(channel="Channel to lock", lock="True to lock, False to unlock")
    async def lockdown(self, interaction: discord.Interaction, channel: discord.TextChannel, lock: bool):
        db = PlatinumCoreDB.load_full_database()
        
        is_mod = (
            interaction.user.id in db["permissions_tiers"]["senior_mods"] or
            interaction.user.id in db["permissions_tiers"]["system_admins"] or
            interaction.user.id == interaction.guild.owner_id
        )
        
        if not is_mod:
            return await interaction.response.send_message(NO_PERM_MESSAGE, ephemeral=True)
        
        overwrites = channel.overwrites_for(interaction.guild.default_role)
        overwrites.send_messages = not lock
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrites)
        
        status = "🔒 Locked" if lock else "🔓 Unlocked"
        await interaction.response.send_message(f"{status} {channel.mention}")
    
    @app_commands.command(name="backup", description="Backup the database (Admin Only)")
    async def backup(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(NO_PERM_MESSAGE, ephemeral=True)
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            with open(DATABASE_FILENAME, "rb") as f:
                file = discord.File(f, filename=f"backup_{datetime.date.today()}.json")
                await interaction.user.send("📦 Database Backup", file=file)
                await interaction.followup.send("✅ Backup sent to your DMs!")
        except Exception as e:
            await interaction.followup.send(f"❌ Backup failed: {e}")

# ==================================================================================================
#  SECTION 10: TOURNAMENT COMMANDS
# ==================================================================================================

class TournamentCog(commands.Cog):
    """Tournament management commands."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="tournament_create", description="Create a new tournament")
    async def create_tournament(self, interaction: discord.Interaction):
        db = PlatinumCoreDB.load_full_database()
        
        is_manager = (
            interaction.user.id in db["permissions_tiers"]["tournament_managers"] or
            interaction.user.id in db["permissions_tiers"]["system_admins"] or
            interaction.user.id == interaction.guild.owner_id
        )
        
        if not is_manager:
            return await interaction.response.send_message("❌ You need Tournament Manager permission.", ephemeral=True)
        
        await interaction.response.send_modal(TournamentCreateModal())
    
    @app_commands.command(name="tournament_blacklist", description="Blacklist a user from a tournament")
    @app_commands.describe(tournament_id="Tournament ID", user="User to blacklist")
    async def blacklist_user(self, interaction: discord.Interaction, tournament_id: str, user: discord.Member):
        db = PlatinumCoreDB.load_full_database()
        
        is_manager = (
            interaction.user.id in db["permissions_tiers"]["tournament_managers"] or
            interaction.user.id in db["permissions_tiers"]["system_admins"] or
            interaction.user.id == interaction.guild.owner_id
        )
        
        if not is_manager:
            return await interaction.response.send_message(NO_PERM_MESSAGE, ephemeral=True)
        
        tournament = db["tournaments"]["active_tournaments"].get(tournament_id)
        if not tournament:
            return await interaction.response.send_message("❌ Tournament not found.", ephemeral=True)
        
        if user.id not in tournament["blacklisted_users"]:
            tournament["blacklisted_users"].append(user.id)
            PlatinumCoreDB.save_database(db)
            await interaction.response.send_message(f"✅ Blacklisted {user.mention} from tournament.")
        else:
            await interaction.response.send_message(f"ℹ️ User already blacklisted.", ephemeral=True)
    
    @app_commands.command(name="tournament_whitelist_role", description="Add required role to tournament")
    @app_commands.describe(tournament_id="Tournament ID", role="Required role")
    async def whitelist_role(self, interaction: discord.Interaction, tournament_id: str, role: discord.Role):
        db = PlatinumCoreDB.load_full_database()
        
        is_manager = (
            interaction.user.id in db["permissions_tiers"]["tournament_managers"] or
            interaction.user.id in db["permissions_tiers"]["system_admins"] or
            interaction.user.id == interaction.guild.owner_id
        )
        
        if not is_manager:
            return await interaction.response.send_message(NO_PERM_MESSAGE, ephemeral=True)
        
        tournament = db["tournaments"]["active_tournaments"].get(tournament_id)
        if not tournament:
            return await interaction.response.send_message("❌ Tournament not found.", ephemeral=True)
        
        if role.id not in tournament["whitelisted_roles"]:
            tournament["whitelisted_roles"].append(role.id)
            PlatinumCoreDB.save_database(db)
            await interaction.response.send_message(f"✅ Added {role.mention} as required role.")
        else:
            await interaction.response.send_message("ℹ️ Role already required.", ephemeral=True)
    
    @app_commands.command(name="tournament_register", description="Register your team for a tournament")
    @app_commands.describe(tournament_id="Tournament ID to join")
    async def register_team(self, interaction: discord.Interaction, tournament_id: str):
        db = PlatinumCoreDB.load_full_database()
        
        tournament = db["tournaments"]["active_tournaments"].get(tournament_id)
        if not tournament:
            return await interaction.response.send_message("❌ Tournament not found.", ephemeral=True)
        
        await interaction.response.send_modal(TournamentRegistrationModal(tournament_id))
    
    @app_commands.command(name="tournament_list", description="List all active tournaments")
    async def list_tournaments(self, interaction: discord.Interaction):
        db = PlatinumCoreDB.load_full_database()
        tournaments = db["tournaments"]["active_tournaments"]
        
        if not tournaments:
            return await interaction.response.send_message("ℹ️ No active tournaments.", ephemeral=True)
        
        embed = discord.Embed(title="🏆 Active Tournaments", color=COLOR_PLATINUM_INFO)
        
        for tid, t in tournaments.items():
            reg_status = "✅ Open" if t["registration_open"] else "❌ Closed"
            embed.add_field(
                name=f"{t['name']} (ID: {tid})",
                value=f"{t['description']}\nTeams: {len(t['registered_teams'])}/{t['max_teams'] or '∞'}\nStatus: {reg_status}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="tournament_close", description="Close tournament registration")
    @app_commands.describe(tournament_id="Tournament ID")
    async def close_registration(self, interaction: discord.Interaction, tournament_id: str):
        db = PlatinumCoreDB.load_full_database()
        
        is_manager = (
            interaction.user.id in db["permissions_tiers"]["tournament_managers"] or
            interaction.user.id in db["permissions_tiers"]["system_admins"] or
            interaction.user.id == interaction.guild.owner_id
        )
        
        if not is_manager:
            return await interaction.response.send_message(NO_PERM_MESSAGE, ephemeral=True)
        
        tournament = db["tournaments"]["active_tournaments"].get(tournament_id)
        if not tournament:
            return await interaction.response.send_message("❌ Tournament not found.", ephemeral=True)
        
        tournament["registration_open"] = False
        PlatinumCoreDB.save_database(db)
        await interaction.response.send_message(f"✅ Closed registration for **{tournament['name']}**")

# ==================================================================================================
#  SECTION 11: CUSTOMIZATION COMMANDS
# ==================================================================================================

class CustomizationCog(commands.Cog):
    """Bot customization commands."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="customize_status", description="Change bot status (Owner Only)")
    @app_commands.describe(text="Status text", activity_type="Activity type")
    @app_commands.choices(activity_type=[
        app_commands.Choice(name="Playing", value="playing"),
        app_commands.Choice(name="Watching", value="watching"),
        app_commands.Choice(name="Listening", value="listening"),
        app_commands.Choice(name="Competing", value="competing")
    ])
    async def customize_status(self, interaction: discord.Interaction, text: str, activity_type: str):
        if interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("❌ Owner Only.", ephemeral=True)
        
        db = PlatinumCoreDB.load_full_database()
        db["branding"]["status_text"] = text
        db["branding"]["status_type"] = activity_type
        PlatinumCoreDB.save_database(db)
        
        activity_map = {
            "playing": discord.ActivityType.playing,
            "watching": discord.ActivityType.watching,
            "listening": discord.ActivityType.listening,
            "competing": discord.ActivityType.competing
        }
        
        activity = discord.Activity(type=activity_map[activity_type], name=text)
        await self.bot.change_presence(activity=activity)
        
        await interaction.response.send_message(f"✅ Status updated to: {activity_type} {text}")
    
    @app_commands.command(name="customize_embed_color", description="Change default embed color (Owner Only)")
    @app_commands.describe(hex_color="Hex color code (e.g., #FF0000)")
    async def customize_color(self, interaction: discord.Interaction, hex_color: str):
        if interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("❌ Owner Only.", ephemeral=True)
        
        db = PlatinumCoreDB.load_full_database()
        db["branding"]["embed_color"] = hex_color
        PlatinumCoreDB.save_database(db)
        
        await interaction.response.send_message(f"✅ Embed color set to {hex_color}")

# ==================================================================================================
#  SECTION 12: SECURITY COMMANDS
# ==================================================================================================

class SecurityCog(commands.Cog):
    """Security configuration commands."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="security_config", description="Configure anti-spam/raid settings (Admin Only)")
    @app_commands.describe(
        anti_spam="Enable/disable anti-spam",
        anti_raid="Enable/disable anti-raid",
        max_messages="Max messages per 10 seconds",
        join_threshold="Max joins per minute before raid alert"
    )
    async def security_config(self, interaction: discord.Interaction, 
                             anti_spam: bool = None,
                             anti_raid: bool = None,
                             max_messages: int = None,
                             join_threshold: int = None):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(NO_PERM_MESSAGE, ephemeral=True)
        
        db = PlatinumCoreDB.load_full_database()
        
        if anti_spam is not None:
            db["security_settings"]["anti_spam_enabled"] = anti_spam
        if anti_raid is not None:
            db["security_settings"]["anti_raid_enabled"] = anti_raid
        if max_messages is not None:
            db["security_settings"]["max_messages_per_10s"] = max_messages
        if join_threshold is not None:
            db["security_settings"]["join_threshold_per_minute"] = join_threshold
        
        PlatinumCoreDB.save_database(db)
        
        settings = db["security_settings"]
        embed = discord.Embed(title="🛡️ Security Settings", color=COLOR_PLATINUM_SUCCESS)
        embed.add_field(name="Anti-Spam", value="✅ Enabled" if settings["anti_spam_enabled"] else "❌ Disabled")
        embed.add_field(name="Anti-Raid", value="✅ Enabled" if settings["anti_raid_enabled"] else "❌ Disabled")
        embed.add_field(name="Max Messages/10s", value=settings["max_messages_per_10s"])
        embed.add_field(name="Join Threshold", value=f"{settings['join_threshold_per_minute']}/min")
        
        await interaction.response.send_message(embed=embed)

# ==================================================================================================
#  SECTION 13: SYSTEM COMMANDS
# ==================================================================================================

class SystemCog(commands.Cog):
    """System management commands."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="sync", description="Sync slash commands (Owner Only)")
    async def sync(self, interaction: discord.Interaction):
        if interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("❌ Owner Only.", ephemeral=True)
        
        await interaction.response.defer(ephemeral=True)
        synced = await self.bot.tree.sync()
        await interaction.followup.send(f"✅ Synced {len(synced)} commands!")
    
    @app_commands.command(name="apply_staff", description="Apply to join the staff team")
    async def apply_staff(self, interaction: discord.Interaction):
        await interaction.response.send_modal(StaffApplicationModal())
    
    @app_commands.command(name="stats", description="View bot statistics")
    async def stats(self, interaction: discord.Interaction):
        db = PlatinumCoreDB.load_full_database()
        stats = db["system_stats"]
        
        embed = discord.Embed(title="📊 Bot Statistics", color=COLOR_PLATINUM_INFO)
        embed.add_field(name="Total Applications", value=stats["total_apps"])
        embed.add_field(name="Total Tickets", value=stats["total_tickets"])
        embed.add_field(name="Transcripts Sent", value=stats["transcripts_sent"])
        embed.add_field(name="Version", value=stats["version"])
        embed.add_field(name="Last Reboot", value=stats["last_reboot"])
        embed.add_field(name="Servers", value=len(self.bot.guilds))
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="reload_panel", description="Reload a ticket panel (Admin Only)")
    @app_commands.describe(message_id="Message ID of the panel")
    async def reload_panel(self, interaction: discord.Interaction, message_id: str):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(NO_PERM_MESSAGE, ephemeral=True)
        
        db = PlatinumCoreDB.load_full_database()
        
        found = False
        panel_data = None
        
        for guild_id in db.get("ticket_panels", {}):
            if message_id in db["ticket_panels"][guild_id]:
                panel_data = db["ticket_panels"][guild_id][message_id]
                found = True
                break
        
        if not found:
            return await interaction.response.send_message("❌ Panel not found.", ephemeral=True)
        
        try:
            msg = None
            for channel in interaction.guild.text_channels:
                try:
                    msg = await channel.fetch_message(int(message_id))
                    if msg:
                        break
                except:
                    continue
            
            if not msg:
                return await interaction.response.send_message("❌ Message not found.", ephemeral=True)
            
            await msg.edit(view=PlatinumPanelView(panel_data.get("buttons", [])))
            await interaction.response.send_message("✅ Panel reloaded!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed: {e}", ephemeral=True)

# ==================================================================================================
#  SECTION 14: BOT CLASS & EVENTS
# ==================================================================================================

class PlatinumBotEngine(commands.Bot):
    """Main bot class."""
    
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents, help_command=None)
    
    async def setup_hook(self):
        print("-" * 50)
        print("[INIT] Starting setup...")
        
        # Add persistent views
        self.add_view(StaffReviewView(0))
        self.add_view(PlatinumTicketActions())
        
        # Load cogs
        await self.add_cog(SetupCog(self))
        await self.add_cog(ModerationCog(self))
        await self.add_cog(TournamentCog(self))
        await self.add_cog(CustomizationCog(self))
        await self.add_cog(SecurityCog(self))
        await self.add_cog(SystemCog(self))
        
        # Auto-sync commands
        try:
            print("[INIT] Auto-syncing commands...")
            synced = await self.tree.sync()
            print(f"[INIT] Synced {len(synced)} commands")
        except Exception as e:
            print(f"[ERROR] Sync failed: {e}")
        
        print("[INIT] Setup complete!")
        print("-" * 50)

bot = PlatinumBotEngine()

@bot.event
async def on_ready():
    """Bot ready event."""
    db = PlatinumCoreDB.load_full_database()
    
    # Reload ticket panels
    if "ticket_panels" in db:
        for guild_id in db["ticket_panels"]:
            for msg_id, data in db["ticket_panels"][guild_id].items():
                if "buttons" in data:
                    bot.add_view(PlatinumPanelView(data["buttons"]))
    
    # Set status
    branding = db.get("branding", {})
    status_text = branding.get("status_text", DEFAULT_STATUS_TEXT)
    status_type = branding.get("status_type", "competing")
    
    activity_map = {
        "playing": discord.ActivityType.playing,
        "watching": discord.ActivityType.watching,
        "listening": discord.ActivityType.listening,
        "competing": discord.ActivityType.competing
    }
    
    activity = discord.Activity(type=activity_map.get(status_type, discord.ActivityType.competing), name=status_text)
    await bot.change_presence(status=discord.Status.online, activity=activity)
    
    print("-" * 50)
    print("PLATINUM ENTERPRISE V6.5 - READY")
    print(f"Logged in as: {bot.user.name}")
    print(f"Guilds: {len(bot.guilds)}")
    print("-" * 50)

@bot.event
async def on_message(message: discord.Message):
    """Message event handler."""
    if message.author.bot:
        return
    
    # Check for spam
    if message.guild:
        if await SecurityEngine.check_spam(message):
            return
        
        # Process XP
        await PlatinumXPEngine.process_message_xp(message.author)
    
    await bot.process_commands(message)

@bot.event
async def on_member_join(member: discord.Member):
    """Member join event."""
    await SecurityEngine.check_raid(member)

# ==================================================================================================
#  SECTION 15: EXECUTION
# ==================================================================================================

if __name__ == "__main__":
    PlatinumCoreDB.initialize_filesystem()
    
    try:
        bot.run(BOT_TOKEN_HOLDER)
    except discord.LoginFailure:
        print("[CRITICAL] Invalid token!")
    except Exception as e:
        print(f"[CRITICAL] Error: {e}")

# ==================================================================================================
#  [EOF] PLATINUM ENTERPRISE v6.5 - COMPLETE
# ==================================================================================================
