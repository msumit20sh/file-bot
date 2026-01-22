import asyncio
from pyrogram import Client, filters, idle
from pyrogram.types import Message
from aiohttp import web

# --- YOUR CONFIGURATION ---
API_ID = 33471771
API_HASH = "20290baf71b8990bc1cfd731084c2c77"
BOT_TOKEN = "8526695522:AAGC639ZiBPoxYRw9qq7xfT7U4aEVNqGbT0"
DB_CHANNEL_ID = -1003674101932
# --------------------------

# Initialize the Bot
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# 1. Logic to Save Files (Runs when YOU send a file to the bot)
@app.on_message(filters.private & (filters.document | filters.video | filters.audio | filters.photo))
async def save_file(client, message):
    # Forward the file to the Database Channel
    forwarded_msg = await message.forward(DB_CHANNEL_ID)
    
    # Create a link using the Message ID from the channel
    file_link = f"https://t.me/{client.me.username}?start={forwarded_msg.id}"
    
    await message.reply_text(
        f"✅ **File Saved to Archive!**\n\nHere is your link:\n{file_link}",
        quote=True
    )

# 2. Logic to Retrieve Files (Runs when USER clicks a link)
@app.on_message(filters.command("start"))
async def start_command(client, message):
    if len(message.command) > 1:
        try:
            channel_message_id = int(message.command[1])
            
            # Send the file and save the "sent message" into a variable
            sent_msg = await client.copy_message(
                chat_id=message.chat.id,
                from_chat_id=DB_CHANNEL_ID,
                message_id=channel_message_id,
                caption="⚠️ **This file will delete in 60 seconds!** \n\nSave it now if you need it."
            )
            
            # Wait for 60 seconds (1 minute)
            await asyncio.sleep(60)
            
            # Delete the file from the user's chat
            await sent_msg.delete()
            await message.reply_text("🗑️ **File deleted for security.**")
            
        except ValueError:
            await message.reply_text("❌ Invalid link.")
        except Exception as e:
            await message.reply_text("❌ File not found or bot was removed from channel.")
            print(f"Error: {e}")
    else:
        await message.reply_text("👋 Welcome to **The Archive**! Send me any file to store it.")

# --- WEB SERVER TO KEEP BOT ONLINE 24/7 ---
async def web_server():
    async def handle(request):
        return web.Response(text="Bot is Running!")

    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

# Start both the Bot and the Web Server
async def main():
    print("Bot is starting...")
    await web_server()
    await app.start()
    print("Bot is Online!")
    await idle() 
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
 
