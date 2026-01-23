import asyncio
from pyrogram import Client, filters, idle
from aiohttp import web

# --- ⚙️ SETTINGS ---
API_ID = 33471771
API_HASH = "20290baf71b8990bc1cfd731084c2c77"
BOT_TOKEN = "8526695522:AAGC639ZiBPoxYRw9qq7xfT7U4aEVNqGbT0"
DB_CHANNEL_ID = -1003674101932

# Timer in seconds (15 mins = 900)
DELETE_TIMER = 900
# -------------------

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Memory variable to store user batches temporarily
# Format: {user_id: [list_of_message_ids]}
user_batches = {}

# 1. COMMAND: /batch (Start recording)
@app.on_message(filters.command("batch") & filters.private)
async def start_batch(client, message):
    user_id = message.from_user.id
    user_batches[user_id] = [] # Create an empty list for this user
    await message.reply_text(
        "📦 **Batch Mode Started!**\n\n"
        "Send me as many files as you want.\n"
        "When you are finished, send **/done** to get your link."
    )

# 2. FILE HANDLER (Smart Logic)
@app.on_message(filters.private & (filters.document | filters.video | filters.audio | filters.photo))
async def save_file(client, message):
    user_id = message.from_user.id
    
    # Forward file to Database Channel
    forwarded_msg = await message.forward(DB_CHANNEL_ID)
    msg_id = forwarded_msg.id

    # CHECK: Is user in Batch Mode?
    if user_id in user_batches:
        # Yes: Just add to list, don't reply yet
        user_batches[user_id].append(msg_id)
    else:
        # No: Standard mode (Single file link)
        file_link = f"https://t.me/{client.me.username}?start=single_{msg_id}"
        await message.reply_text(f"✅ **File Saved!**\nLink: {file_link}", quote=True)

# 3. COMMAND: /done (Finish recording)
@app.on_message(filters.command("done") & filters.private)
async def finish_batch(client, message):
    user_id = message.from_user.id
    
    if user_id not in user_batches or len(user_batches[user_id]) == 0:
        await message.reply_text("❌ You haven't sent any files yet! Send /batch first.")
        return

    # Get the list of Message IDs
    msg_ids = user_batches[user_id]
    first_id = msg_ids[0]
    last_id = msg_ids[-1]
    count = len(msg_ids)

    # Create a link with the RANGE of IDs (e.g., batch_100_105)
    # This assumes files are uploaded sequentially (which they usually are)
    link = f"https://t.me/{client.me.username}?start=batch_{first_id}_{last_id}"
    
    await message.reply_text(
        f"✅ **Batch Created!**\n"
        f"📂 Contains: {count} files\n\n"
        f"🔗 **Your Link:**\n{link}"
    )
    
    # Clear memory
    del user_batches[user_id]

# 4. START COMMAND (Retrieve Files)
@app.on_message(filters.command("start"))
async def start_command(client, message):
    if len(message.command) > 1:
        payload = message.command[1]
        
        try:
            # SCENARIO A: Single File (single_123)
            if payload.startswith("single_"):
                msg_id = int(payload.split("_")[1])
                sent_msg = await client.copy_message(
                    message.chat.id, DB_CHANNEL_ID, msg_id, 
                    caption=f"⚠️ **Deleting in {DELETE_TIMER//60} mins!**"
                )
                await asyncio.sleep(DELETE_TIMER)
                await sent_msg.delete()

            # SCENARIO B: Batch of Files (batch_100_105)
            elif payload.startswith("batch_"):
                parts = payload.split("_")
                start_id = int(parts[1])
                end_id = int(parts[2])
                
                sent_messages = []
                
                await message.reply_text(f"⬇️ **Sending files...** (Deleting in {DELETE_TIMER//60} mins)")
                
                # Loop through all IDs in the range
                for i in range(start_id, end_id + 1):
                    try:
                        msg = await client.copy_message(message.chat.id, DB_CHANNEL_ID, i)
                        sent_messages.append(msg)
                        await asyncio.sleep(0.5) # Wait 0.5s to avoid flood limits
                    except:
                        pass # Skip if a message was deleted from channel
                
                # Wait for Timer
                await asyncio.sleep(DELETE_TIMER)
                
                # Delete all
                for msg in sent_messages:
                    try:
                        await msg.delete()
                    except:
                        pass
                await message.reply_text("🗑️ **Batch deleted for security.**")

            # SCENARIO C: Old Links (Just numbers)
            else:
                # Handle old links from previous bot version
                msg_id = int(payload)
                sent_msg = await client.copy_message(
                    message.chat.id, DB_CHANNEL_ID, msg_id,
                    caption="⚠️ **Deleting in 15 mins!**"
                )
                await asyncio.sleep(DELETE_TIMER)
                await sent_msg.delete()

        except Exception as e:
            await message.reply_text("❌ Error: Link invalid or files removed.")
            print(e)
            
    else:
        await message.reply_text(
            "👋 **Welcome!**\n\n"
            "**Modes:**\n"
            "1️⃣ Send a file -> Get a link immediately.\n"
            "2️⃣ Send **/batch** -> Upload many files -> Send **/done** to get 1 link."
        )

# --- WEB SERVER ---
async def web_server():
    async def handle(request):
        return web.Response(text="Bot is Running!")
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

# --- MAIN ---
async def main():
    print("Bot Starting...")
    await web_server()
    await app.start()
    
    try:
        await app.get_chat(DB_CHANNEL_ID)
        print("Channel Connected!")
    except:
        print("Channel connection failed (try manual admin fix).")

    print("Bot Online!")
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
