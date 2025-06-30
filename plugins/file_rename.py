
import os
import asyncio
import time
import requests
from pyrogram import Client, filters
from pyrogram.errors import PeerIdInvalid, UserIsBlocked, ChatWriteForbidden
from helper.utils import progress_for_pyrogram
from helper.database import jishubotz
from config import Config
from pyromod.exceptions import ListenerTimeout

BASE_DOWNLOAD_PATH = "downloads"

# Your channel ID (replace with your actual channel ID)
CHANNEL_ID = "-1002864726491"

# Dictionary to store active jobs for each user
user_jobs = {}

def create_user_download_path(user_id):
    path = os.path.join(BASE_DOWNLOAD_PATH, str(user_id))
    os.makedirs(path, exist_ok=True)
    return path

async def download_thumbnail(image_url, save_path):
    """Download image from a URL and save it locally."""
    try:
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            return save_path
        else:
            print(f"[ERROR] Failed to download thumbnail: {response.status_code}")
            return None
    except Exception as e:
        print(f"[ERROR] Error downloading thumbnail: {e}")
        return None

async def safe_send_to_channel(client, file_path, caption, original_file_name, thumb_path):
    """Safely send file to channel with error handling."""
    try:
        # Check if we can access the channel
        chat_info = await client.get_chat(CHANNEL_ID)
        await client.send_document(
            chat_id=CHANNEL_ID,
            document=file_path,
            caption=caption,
            file_name=original_file_name,
            thumb=thumb_path if thumb_path else None,
        )
        return True
    except (PeerIdInvalid, ChatWriteForbidden, UserIsBlocked) as e:
        print(f"[ERROR] Cannot send to channel {CHANNEL_ID}: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error sending to channel: {e}")
        return False

async def cleanup_files(*file_paths):
    """Clean up files safely."""
    for file_path in file_paths:
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"[ERROR] Failed to remove file {file_path}: {e}")

async def process_file(client, message, new_filename):
    """Process a single file with the new filename."""
    user_id = message.from_user.id
    user_download_path = create_user_download_path(user_id)
    original_file_name = message.document.file_name if message.document else "uploaded_file"
    
    # Use the new filename provided by user
    file_extension = os.path.splitext(new_filename)[1] or os.path.splitext(original_file_name)[1] or ".bin"
    if not os.path.splitext(new_filename)[1]:
        new_filename += file_extension
    
    file_path = os.path.join(user_download_path, f"temp_{int(time.time())}{file_extension}")
    
    # Fetch caption and process it
    caption = await jishubotz.get_caption(user_id) or "**Here is your file!**"
    caption = caption.replace("{filename}", new_filename)
    file_size = message.document.file_size
    caption = caption.replace("{filesize}", f"{file_size / (1024 * 1024):.2f} MB")
    caption = caption.replace("{fileduration}", "Duration not available")

    # Direct thumbnail URL
    image_url = Config.GLOBAL_THUMBNAIL_URL
    thumbnail_path = os.path.join(user_download_path, f"thumbnail_{int(time.time())}.jpg")
    thumb_path = await download_thumbnail(image_url, thumbnail_path)
    
    # Download the file
    status_message = await message.reply("`Download in progress...`")
    try:
        await client.download_media(
            message=message,
            file_name=file_path,
            progress=progress_for_pyrogram,
            progress_args=("`Download in progress...`", status_message, time.time())
        )
    except asyncio.CancelledError:
        await cleanup_files(file_path, thumbnail_path)
        await status_message.delete()
        raise
    except Exception as e:
        await status_message.edit(f"Error during download: {e}")
        await cleanup_files(file_path, thumbnail_path)
        return

    # Upload to user and channel
    await status_message.edit("`Uploading file...`")
    try:
        # Send file to user
        await client.send_document(
            message.chat.id,
            document=file_path,
            caption=caption,
            file_name=new_filename,
            thumb=thumb_path if thumb_path else None,
            progress=progress_for_pyrogram,
            progress_args=("`Upload in progress...`", status_message, time.time())
        )
        
        # Try to send to channel (optional, won't fail if channel is unavailable)
        await safe_send_to_channel(client, file_path, caption, new_filename, thumb_path)
        
    except asyncio.CancelledError:
        await cleanup_files(file_path, thumbnail_path)
        await status_message.delete()
        raise
    except Exception as e:
        await status_message.edit(f"Error during upload: {e}")
        await cleanup_files(file_path, thumbnail_path)
        return
    finally:
        # Cleanup files
        await cleanup_files(file_path, thumbnail_path)
        try:
            await status_message.delete()
        except:
            pass

    print(f"[DEBUG] File processing completed for user {user_id}")

async def cancel_user_job(user_id):
    """Cancel active job for a user."""
    if user_id in user_jobs:
        job_task = user_jobs[user_id]
        if not job_task.done():
            job_task.cancel()
            try:
                await job_task
            except asyncio.CancelledError:
                pass
        del user_jobs[user_id]

@Client.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def handle_file_rename(client, message):
    """Handle file renaming with manual filename input."""
    user_id = message.from_user.id
    
    # Cancel any existing job for this user
    await cancel_user_job(user_id)
    
    # Ask for new filename
    try:
        filename_request = await message.reply(
            "📝 **Please send the new filename for your file:**\n\n"
            "⏰ You have 2 minutes to reply.\n"
            "💡 Include the file extension if you want to change it.",
            quote=True
        )
        
        try:
            # Wait for filename with 2 minute timeout
            filename_message = await client.ask(
                chat_id=user_id,
                text="",
                filters=filters.text,
                timeout=120  # 2 minutes
            )
            
            new_filename = filename_message.text.strip()
            
            if not new_filename:
                await filename_request.edit("❌ **Invalid filename. Operation cancelled.**")
                await asyncio.sleep(2)
                await filename_request.delete()
                return
            
            # Delete the filename request message
            await filename_request.delete()
            
            # Start processing the file
            job_task = asyncio.create_task(process_file(client, message, new_filename))
            user_jobs[user_id] = job_task
            
            try:
                await job_task
            except asyncio.CancelledError:
                print(f"[DEBUG] Job cancelled for user {user_id}")
            finally:
                # Clean up job reference
                if user_id in user_jobs:
                    del user_jobs[user_id]
                
                # Clean up original message
                try:
                    await message.delete()
                except:
                    pass
                    
        except ListenerTimeout:
            await filename_request.edit("⏰ **Timeout! Operation cancelled.**")
            await asyncio.sleep(2)
            await filename_request.delete()
            # Clean up original message
            try:
                await message.delete()
            except:
                pass
            
    except Exception as e:
        print(f"[ERROR] Error in handle_file_rename: {e}")
        try:
            await message.reply(f"❌ **Error occurred:** {str(e)}")
        except:
            pass
