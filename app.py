from keep_alive import keep_alive
import os
import discord
import asyncio
import logging
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
        super().__init__(chunk_guilds_at_startup=False)
        self.target_channel_id = target_cid

    async def on_ready(self):
        print(f'Logged in as {self.user}')
        await client.change_presence(afk=True)
        
        channel = self.get_channel(self.target_channel_id)
        if channel:
            # Join voice first
            await self.attempt_connect(channel)
            await asyncio.sleep(2)

            # SET AFK STATUS
            # This is the ONLY way to get notifications while the script is active
            await self.ws.send_as_json({
                'op': 3,
                'd': {
                    'since': None,
                    'activities': [],
                    'status': 'invisible', 
                    'afk': True
                }
            })
            print("SYSTEM: Presence set to Invisible + AFK.")

    async def attempt_connect(self, channel):
        try:
            print("Clearing ghost sessions to prevent 4006...")
            # This tells Discord to disconnect you from any 'phantom' voice channels
            await channel.guild.change_voice_state(channel=None)
            await asyncio.sleep(2)

            print(f"Connecting to {channel.name}...")
            await channel.connect(timeout=20.0, reconnect=False)
            print("Successfully connected!")
        except Exception as e:
            print(f"Connection failed: {e}")

# --- CONFIG ---
TOKEN = os.environ.get("Authorization")
CHANNEL_ID = 1185566603052597248

keep_alive()
client = FOSSSelfBot(CHANNEL_ID)
client.run(TOKEN)
