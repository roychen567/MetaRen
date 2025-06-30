
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import MessageDeleteForbidden, MessageIdInvalid
import asyncio

@Client.on_message(filters.private & filters.command("clear"))
async def clear_chat(client: Client, message: Message):
    """Clear all messages in private chat between user and bot"""
    try:
        user_id = message.from_user.id
        
        # Send confirmation message
        confirm_msg = await message.reply_text(
            "🗑️ **Clearing Chat History...**\n\n"
            "This will delete all messages in this chat. Please wait...",
            quote=True
        )
        
        # Get chat history and delete messages
        deleted_count = 0
        failed_count = 0
        
        async for msg in client.get_chat_history(user_id, limit=10000):
            try:
                await msg.delete()
                deleted_count += 1
                
                # Add small delay to avoid rate limiting
                if deleted_count % 10 == 0:
                    await asyncio.sleep(0.5)
                    
            except (MessageDeleteForbidden, MessageIdInvalid):
                failed_count += 1
                continue
            except Exception as e:
                failed_count += 1
                print(f"Error deleting message: {e}")
                continue
        
        # Send final confirmation (this will also be deleted shortly)
        final_msg = await client.send_message(
            user_id,
            f"✅ **Chat Cleared Successfully!**\n\n"
            f"📊 **Statistics:**\n"
            f"• Messages Deleted: `{deleted_count}`\n"
            f"• Failed to Delete: `{failed_count}`\n\n"
            f"_This message will be deleted in 5 seconds..._"
        )
        
        # Delete the final message after 5 seconds
        await asyncio.sleep(5)
        try:
            await final_msg.delete()
        except:
            pass
            
    except Exception as e:
        await message.reply_text(
            f"❌ **Error clearing chat:**\n`{str(e)}`\n\n"
            "Please try again or contact support if the issue persists."
        )

@Client.on_message(filters.group & filters.command("clear"))
async def clear_chat_group(client: Client, message: Message):
    """Handle clear command in groups (admin only)"""
    try:
        # Check if user is admin
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        member = await client.get_chat_member(chat_id, user_id)
        
        if member.status not in ["creator", "administrator"]:
            await message.reply_text(
                "❌ **Access Denied!**\n\n"
                "Only administrators can use this command in groups.",
                quote=True
            )
            return
        
        # Confirm action for groups
        await message.reply_text(
            "⚠️ **Warning!**\n\n"
            "The `/clear` command is designed for private chats only.\n"
            "For group management, please use dedicated admin commands.\n\n"
            "If you want to clear bot messages only, use `/clear_bot` instead.",
            quote=True
        )
        
    except Exception as e:
        await message.reply_text(
            f"❌ **Error:** `{str(e)}`",
            quote=True
        )

@Client.on_message(filters.group & filters.command("clear_bot"))  
async def clear_bot_messages(client: Client, message: Message):
    """Clear only bot messages in groups (admin only)"""
    try:
        # Check if user is admin
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        member = await client.get_chat_member(chat_id, user_id)
        
        if member.status not in ["creator", "administrator"]:
            await message.reply_text(
                "❌ **Access Denied!**\n\n"
                "Only administrators can use this command.",
                quote=True
            )
            return
        
        confirm_msg = await message.reply_text(
            "🗑️ **Clearing Bot Messages...**\n\n"
            "Deleting all messages sent by this bot in the group...",
            quote=True
        )
        
        bot_user = await client.get_me()
        deleted_count = 0
        
        async for msg in client.get_chat_history(chat_id, limit=1000):
            try:
                if msg.from_user and msg.from_user.id == bot_user.id:
                    await msg.delete()
                    deleted_count += 1
                    
                    if deleted_count % 5 == 0:
                        await asyncio.sleep(0.5)
                        
            except Exception:
                continue
        
        await confirm_msg.edit_text(
            f"✅ **Bot Messages Cleared!**\n\n"
            f"📊 Deleted `{deleted_count}` bot messages from this group."
        )
        
        # Delete confirmation after 10 seconds
        await asyncio.sleep(10)
        try:
            await confirm_msg.delete()
            await message.delete()
        except:
            pass
            
    except Exception as e:
        await message.reply_text(
            f"❌ **Error:** `{str(e)}`",
            quote=True
        )

# MB Developer 
# Don't Remove Credit 🥺
# Developer @MB_Owner
