import os
import discord
import asyncio
import logging
import random
from keep_alive import keep_alive
import google.protobuf.json_format as json_format

# --- MONKEYPATCH FOR PROTOBUF ---
# This prevents crashes with newer versions of Protobuf used by discord.py-self
original_m2d = json_format.MessageToDict
def patched_m2d(message, **kwargs):
    if 'including_default_value_fields' in kwargs:
        kwargs['always_print_fields_with_no_presence'] = kwargs.pop('including_default_value_fields')
    return original_m2d(message, **kwargs)
json_format.MessageToDict = patched_m2d

# --- FORCE MOBILE IDENTITY ---
# Makes the account appear as an iPhone to reduce detection risk
discord.client.ConnectionState.identify_properties = lambda self: {
    '$os': 'iOS',
    '$browser': 'Discord iOS',
    '$device': 'iPhone'
}

logging.basicConfig(level=logging.INFO)

class FOSSSelfBot(discord.Client):
    def __init__(self, target_cid):
        super().__init__(chunk_guilds_at_startup=False)
        self.target_channel_id = target_cid
        self.is_reconnecting = False

    async def on_ready(self):
        print(f'SYSTEM: Logged in as {self.user} (ID: {self.user.id})')
        
        # Random delay to look more human-like
        await asyncio.sleep(random.uniform(1, 3))
        
        try:
            await self.change_presence(status=discord.Status.invisible, afk=True)
            print(f"SYSTEM: Presence set to Invisible for {self.user}")
        except Exception as e:
            print(f"Status Error for {self.user}: {e}")

        # Start the persistent heartbeat monitor
        self.loop.create_task(self.voice_heartbeat())

    async def attempt_connect(self, channel):
        """Handles the actual connection logic."""
        try:
            self.is_reconnecting = True
            print(f"[{self.user}] Clearing ghost sessions and connecting to {channel.name}...")
            
            # Disconnect from any existing voice state first
            await channel.guild.change_voice_state(channel=None)
            await asyncio.sleep(2)

            await channel.connect(timeout=20.0, reconnect=True)
            print(f"[{self.user}] Successfully connected to Voice!")
        except Exception as e:
            print(f"[{self.user}] Connection failed: {e}")
        finally:
            self.is_reconnecting = False

    async def voice_heartbeat(self):
        """Background loop that ensures the bot stays in the voice channel forever."""
        await self.wait_until_ready()
        while not self.is_closed():
            # Check if we are currently connected to any voice channel
            if not self.voice_clients and not self.is_reconnecting:
                channel = self.get_channel(self.target_channel_id)
                if channel:
                    print(f"[{self.user}] Heartbeat: Voice connection missing. Rejoining...")
                    await self.attempt_connect(channel)
                else:
                    print(f"[{self.user}] Heartbeat Error: Channel ID {self.target_channel_id} not found.")
            
            # Check every 30 seconds
            await asyncio.sleep(30)

# --- ASYNC RUNNER ---
async def start_multibot():
    # Fetch tokens from Environment Variables
    accounts = [
        {"token": os.environ.get("TOKEN_1"), "channel": 1185566603052597248},
        {"token": os.environ.get("TOKEN_2"), "channel": 1185566603052597248}
    ]

    # Initialize the Flask server to keep Render instance awake
    keep_alive()

    tasks = []
    for acc in accounts:
        token = acc["token"]
        if token:
            client = FOSSSelfBot(acc["channel"])
            # Use client.start instead of run to allow multiple accounts
            tasks.append(client.start(token))
        else:
            print("Warning: A token is missing in Environment Variables.")

    if tasks:
        print("SYSTEM: Starting all accounts...")
        await asyncio.gather(*tasks)
    else:
        print("Error: No valid tokens found. Script exiting.")

# --- EXECUTION ---
if __name__ == "__main__":
    try:
        asyncio.run(start_multibot())
    except KeyboardInterrupt:
        print("System: Shutting down manually.")
    except Exception as e:
        # Prevents the entire script from crashing silently
        print(f"System: Fatal error: {e}")
