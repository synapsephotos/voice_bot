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
        print(f'SYSTEM: Logged in as {self.user} (ID: {self.user.id})')
        
        try:
            await self.change_presence(status=discord.Status.invisible, afk=True)
            print(f"SYSTEM: Presence set to Invisible for {self.user}")
        except Exception as e:
            print(f"Status Error for {self.user}: {e}")

        channel = self.get_channel(self.target_channel_id)
        if channel:
            await self.attempt_connect(channel)
        else:
            print(f"Error: Could not find channel {self.target_channel_id} for {self.user}")

    async def attempt_connect(self, channel):
        try:
            print(f"[{self.user}] Clearing ghost sessions...")
            await channel.guild.change_voice_state(channel=None)
            await asyncio.sleep(2)

            print(f"[{self.user}] Connecting to {channel.name}...")
            await channel.connect(timeout=20.0, reconnect=True)
            print(f"[{self.user}] Successfully connected to Voice!")
        except Exception as e:
            print(f"[{self.user}] Connection failed: {e}")

# --- ASYNC RUNNER ---
async def start_multibot():
    # Configuration: Add your tokens and target channels here
    # You can point them to the same channel or different ones
    accounts = [
        {"token": os.environ.get("TOKEN_1"), "channel": 1185566603052597248},
        {"token": os.environ.get("TOKEN_2"), "channel": 1185566603052597248}
    ]

    # Initialize the flask server for uptime
    keep_alive()

    clients = []
    tasks = []

    for acc in accounts:
        token = acc["token"]
        if token:
            client = FOSSSelfBot(acc["channel"])
            clients.append(client)
            # Create a task for each client's start method
            tasks.append(client.start(token))
        else:
            print("Warning: One of the tokens is missing in Environment Variables.")

    if tasks:
        # Run all clients concurrently
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
        print(f"System: Fatal error: {e}")
