# 4. START COMMAND (Retrieve Files)
@app.on_message(filters.command("start"))
async def start_command(client, message):
    if len(message.command) > 1:
        payload = message.command[1]
        try:
            # SCENARIO A: Single File
            if payload.startswith("single_"):
                msg_id = int(payload.split("_")[1])
                
                # --- FIX: Pehle original message fetch karo caption nikalne ke liye ---
                db_msg = await client.get_messages(DB_CHANNEL_ID, msg_id)
                original_caption = db_msg.caption if db_msg.caption else ""
                
                # Dono ko merge karo (Original + Warning)
                final_caption = f"{original_caption}\n\n⚠️ **Deleting in {DELETE_TIMER//60} mins!**"
                
                sent_msg = await client.copy_message(
                    message.chat.id, 
                    DB_CHANNEL_ID, 
                    msg_id, 
                    caption=final_caption # Ab dono caption saath aayenge
                )
                
                await asyncio.sleep(DELETE_TIMER)
                await sent_msg.delete()

            # SCENARIO B: Batch of Files
            elif payload.startswith("batch_"):
                parts = payload.split("_")
                start_id = int(parts[1])
                end_id = int(parts[2])
                
                sent_messages = []
                # Status message
                info_msg = await message.reply_text(f"⬇️ **Sending batch...** (Deleting in {DELETE_TIMER//60} mins)")
                
                for i in range(start_id, end_id + 1):
                    try:
                        # Batch mein har file ka apna original caption apne aap aayega
                        msg = await client.copy_message(message.chat.id, DB_CHANNEL_ID, i)
                        sent_messages.append(msg)
                        await asyncio.sleep(0.7) # Flood waala error na aaye isliye thoda delay
                    except:
                        pass 
                
                await asyncio.sleep(DELETE_TIMER)
                for msg in sent_messages:
                    try: await msg.delete()
                    except: pass
                
                try: await info_msg.delete()
                except: pass
                await message.reply_text("🗑️ **Batch deleted for security.**")

        except Exception as e:
            await message.reply_text("❌ Error: Link invalid or files removed.")
            print(f"Error logic: {e}")
            
    else:
        # Normal welcome message (same as before)
        await message.reply_text("👋 **Welcome!** Send me a file to generate a link.")
