import os
import discord
import asyncio
import logging
from keep_alive import keep_alive
import google.protobuf.json_format as json_format

# --- MONKEYPATCH FOR PROTOBUF ---
original_m2d = json_format.MessageToDict
def patched_m2d(message, **kwargs):
    if 'including_default_value_fields' in kwargs:
        kwargs['always_print_fields_with_no_presence'] = kwargs.pop('including_default_value_fields')
    return original_m2d(message, **kwargs)
json_format.MessageToDict = patched_m2d

# --- FORCE MOBILE IDENTITY ---
discord.client.ConnectionState.identify_properties = lambda self: {
    '$os': 'iOS',
    '$browser': 'Discord iOS',
    '$device': 'iPhone'
}

logging.basicConfig(level=logging.INFO)

class FOSSSelfBot(discord.Client):
    def __init__(self, target_cid):
        # Optimized for Self-Bots to prevent hanging on login
        super().__init__(chunk_guilds_at_startup=False)
        self.target_channel_id = target_cid

    async def on_ready(self):
        # Use self instead of client inside the class
        print(f'SYSTEM: Logged in as {self.user}')
        
        # This prevents a crash if the token doesn't have permissions
        try:
            await self.change_presence(status=discord.Status.invisible, afk=True)
            print("SYSTEM: Presence set to Invisible + AFK.")
        except Exception as e:
            print(f"Status Error: {e}")

        channel = self.get_channel(self.target_channel_id)
        if channel:
            await self.attempt_connect(channel)
        else:
            print(f"Error: Could not find channel {self.target_channel_id}")

    async def attempt_connect(self, channel):
        try:
            print("Clearing ghost sessions...")
            await channel.guild.change_voice_state(channel=None)
            await asyncio.sleep(2)

            print(f"Connecting to {channel.name}...")
            await channel.connect(timeout=20.0, reconnect=True)
            print("Successfully connected to Voice!")
        except Exception as e:
            print(f"Connection failed: {e}")

# --- EXECUTION ---
# Get token from Render Environment Variables
TOKEN = os.environ.get("Authorization")
CHANNEL_ID = 1185566603052597248

if TOKEN:
    # 1. Start the Flask server thread FIRST
    keep_alive()
    
    # 2. Initialize the custom Bot class
    client = FOSSSelfBot(CHANNEL_ID)
    
    # 3. Start the Bot (This blocks the script)
    try:
        client.run(TOKEN)
    except discord.errors.LoginFailure:
        print("Error: Invalid Token. Check your Render Environment Variables.")
else:
    print("Error: No 'Authorization' token found in Environment Variables.")