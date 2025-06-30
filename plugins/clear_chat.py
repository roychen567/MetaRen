from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import MessageDeleteForbidden, MessageIdInvalid
import asyncio

@Client.on_message(filters.private & filters.command("clear"))
async def clear_chat(client: Client, message: Message):
    """Clear messages in private chat - limited to bot's accessible messages"""
    try:
        user_id = message.from_user.id

        # Send confirmation message
        confirm_msg = await message.reply_text(
            "🗑️ **Clearing Accessible Messages...**\n\n"
            "⚠️ **Note:** Bots can only delete:\n"
            "• Messages sent by the bot\n"
            "• Messages sent directly to the bot\n\n"
            "This will clear what the bot can access. Please wait...",
            quote=True
        )

        # Delete the command message and confirmation
        deleted_count = 0
        try:
            await message.delete()
            deleted_count += 1
        except:
            pass

        await asyncio.sleep(2)

        # Send final status
        final_msg = await client.send_message(
            user_id,
            f"✅ **Chat Cleanup Completed!**\n\n"
            f"📊 **Bot deleted:** `{deleted_count}` accessible messages\n\n"
            f"💡 **Tip:** To clear all messages, manually delete them from your chat settings.\n\n"
            f"_This message will be deleted in 10 seconds..._"
        )

        # Delete the final message after 10 seconds
        await asyncio.sleep(10)
        try:
            await final_msg.delete()
            await confirm_msg.delete()
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

        # Inform about limitations
        await message.reply_text(
            "⚠️ **Bot Limitations!**\n\n"
            "Bots cannot access full message history due to Telegram restrictions.\n"
            "Use `/clear_bot` to delete only bot messages, or manually clear the chat.\n\n"
            "💡 **Alternative:** Use group admin tools for complete message management.",
            quote=True
        )

    except Exception as e:
        await message.reply_text(
            f"❌ **Error:** `{str(e)}`",
            quote=True
        )

@Client.on_message(filters.group & filters.command("clear_bot"))  
async def clear_bot_messages(client: Client, message: Message):
    """Clear only bot messages in groups (admin only) - simplified approach"""
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
            "🗑️ **Bot Message Cleanup**\n\n"
            "⚠️ Due to Telegram bot limitations, only recent bot messages can be deleted.\n"
            "For complete cleanup, use Telegram's built-in admin tools.\n\n"
            "This command will delete the current bot messages.",
            quote=True
        )

        # Delete the command and confirmation messages
        await asyncio.sleep(3)
        try:
            await message.delete()
            await confirm_msg.delete()
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