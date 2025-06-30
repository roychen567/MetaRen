
from pyrogram import Client, filters
from datetime import datetime
from pytz import timezone
from pyrogram.raw.all import layer
from config import Config
from aiohttp import web
from route import web_server
import pyromod

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="renamer",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=200,
            plugins={"root": "plugins"},
            sleep_threshold=15,
        )

    async def start(self):
        await super().start()
        me = await self.get_me()
        self.mention = me.mention
        self.username = me.username  
        self.uptime = Config.BOT_UPTIME     
        if Config.WEBHOOK:
            app = web.AppRunner(await web_server())
            await app.setup()       
            await web.TCPSite(app, "0.0.0.0", 8080).start()     
        print(f"{me.first_name} Is Started.....✨️")
        for id in Config.ADMIN:
            try: 
                # First check if we can get the chat
                chat = await self.get_chat(id)
                await self.send_message(id, f"**{me.first_name}  Is Started...**")
                print(f"✅ Successfully sent start message to admin {id}")                                
            except Exception as e:
                print(f"❌ Failed to send start message to admin {id}: {e}")
                print(f"   This usually means the bot hasn't received a message from user {id} yet.")
        
        if Config.LOG_CHANNEL:
            try:
                # First check if we can access the channel
                chat = await self.get_chat(Config.LOG_CHANNEL)
                curr = datetime.now(timezone("Asia/Kolkata"))
                date = curr.strftime('%d %B, %Y')
                time = curr.strftime('%I:%M:%S %p')
                await self.send_message(Config.LOG_CHANNEL, f"**{me.mention} Is Restarted !!**\n\n📅 Date : `{date}`\n⏰ Time : `{time}`\n🌐 Timezone : `Asia/Kolkata`\n\n🉐 Version : `v1.0 (Layer {layer})`")
                print(f"✅ Successfully sent restart message to log channel {Config.LOG_CHANNEL}")                                
            except Exception as e:
                print(f"❌ Failed to send restart message to log channel {Config.LOG_CHANNEL}: {e}")
                print(f"   Make sure the bot is added to the channel and has proper permissions.")

bot = Bot()

if __name__ == "__main__":
    bot.run()
