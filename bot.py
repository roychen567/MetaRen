
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
            max_concurrent_transmissions=10,  # Increased for better performance
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
                await self.send_message(id, f"**{me.first_name}  Is Started...**")                                
            except Exception as e:
                print(f"Failed to send start message to admin {id}: {e}")
        
        if Config.LOG_CHANNEL:
            try:
                curr = datetime.now(timezone("Asia/Kolkata"))
                date = curr.strftime('%d %B, %Y')
                time = curr.strftime('%I:%M:%S %p')
                await self.send_message(Config.LOG_CHANNEL, f"**{me.mention} Is Restarted !!**\n\n📅 Date : `{date}`\n⏰ Time : `{time}`\n🌐 Timezone : `Asia/Kolkata`\n\n🉐 Version : `v1.0 (Layer {layer})`")                                
            except Exception as e:
                print(f"Failed to send restart message to log channel: {e}")

bot = Bot()

if __name__ == "__main__":
    bot.run()
