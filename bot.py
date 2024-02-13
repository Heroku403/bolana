import subprocess
import os
import time
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

# Your Telegram bot token
TOKEN = "6450878640:AAEBFk3mBx1tVLRjqfpySEP9OJIwf3IqfLs"

LINK, FILE_NAME, DURATION = range(3)

def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Welcome! Please send me the m3u8 link you want to record.")
    return LINK

def handle_link(update: Update, context: CallbackContext) -> int:
    context.user_data['link'] = update.message.text
    update.message.reply_text("Please enter the desired file name:")
    return FILE_NAME

def handle_file_name(update: Update, context: CallbackContext) -> int:
    file_name = update.message.text.strip()  # Remove leading/trailing whitespace
    if not file_name.endswith((".mp4", ".mkv")):  # Check if either ".mp4" or ".mkv" extension is already present
        file_name += ".mp4"  # If not, append ".mp4" to the filename
    context.user_data['file_name'] = file_name
    update.message.reply_text("Please enter the duration of the recording in seconds:")
    return DURATION

def handle_duration(update: Update, context: CallbackContext) -> int:
    duration = update.message.text
    context.user_data['duration'] = duration
    update.message.reply_text("Recording will start. Please wait...")
    record_m3u8(update, context)  # Pass both update and context arguments here
    return ConversationHandler.END

def record_m3u8(update: Update, context: CallbackContext):
    link = context.user_data['link']
    file_name = context.user_data['file_name']
    duration = context.user_data['duration']
    
    try:
        duration = int(duration)
    except ValueError:
        update.message.reply_text("Invalid duration specified. Please enter a valid integer for duration.")
        return

    # Send a message indicating that the recording is starting
    start_message = update.message.reply_text("Recording will start. Please wait...")

    # Start ffmpeg process to record m3u8 link
    process = subprocess.Popen(['ffmpeg', '-i', link, '-t', str(duration), '-c', 'copy', file_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    context.user_data['process'] = process

    # Update the message with progress status until the recording is complete
    while True:
        output = process.stderr.readline()
        if process.poll() is not None:
            break
        if output:
            update.message.edit_text(f"Recording in progress: {output.decode('utf-8').strip()}")

    # Check if the file exists
    if os.path.exists(file_name):
        with open(file_name, 'rb') as f:
            # Upload the file to Telegram
            context.bot.send_document(chat_id=update.effective_chat.id, document=f, filename=file_name)

        os.remove(file_name)  # Remove the file after uploading
        start_message.delete()  # Delete the start message
        update.message.reply_text("Recording completed and file uploaded.")
    else:
        update.message.reply_text("Error: Recording failed.")



def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LINK: [MessageHandler(Filters.text & ~Filters.command, handle_link)],
            FILE_NAME: [MessageHandler(Filters.text & ~Filters.command, handle_file_name)],
            DURATION: [MessageHandler(Filters.text & ~Filters.command, handle_duration)]
        },
        fallbacks=[]
    )

    dp.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
