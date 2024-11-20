import os
import logging
import subprocess
from flask import Flask
from yt_dlp import YoutubeDL
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Set up Flask
app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Telegram bot token
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Set this as an environment variable

# Function to download the video using yt-dlp
def download_video(url: str, output_path: str):
    ydl_opts = {"format": "bestaudio/bestvideo", "outtmpl": output_path}
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

# Function to compress the video
def compress_video(input_path: str, output_path: str):
    try:
        # ffmpeg command to compress video
        command = [
            "ffmpeg", "-i", input_path,
            "-vf", "scale=-1:720",
            "-c:v", "libx264",
            "-preset", "slow",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "128k",
            output_path
        ]
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg compression error: {e}")
        raise

# Telegram bot command to handle compression
def compress_command(update: Update, context: CallbackContext):
    url = ' '.join(context.args)
    if not url:
        update.message.reply_text("Please provide a video URL with /l {url}.")
        return

    update.message.reply_text("Downloading and compressing the video...")

    input_path = "downloaded_video.mp4"
    output_path = "compressed_video.mp4"

    try:
        # Download video
        download_video(url, input_path)

        # Compress video
        compress_video(input_path, output_path)

        # Send the compressed video back to the user
        with open(output_path, 'rb') as video_file:
            update.message.reply_video(video=video_file, caption="Here is your compressed video (720p, x264, CRF=18)")
    except Exception as e:
        logger.error(f"Error: {e}")
        update.message.reply_text("An error occurred during processing. Please try again.")
    finally:
        # Clean up files
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)

# Bot setup
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome! Send a video URL with /l {url} to compress it to 720p.")

def main():
    # Initialize the Telegram bot
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("l", compress_command))

    updater.start_polling()
    updater.idle()

# Flask route for health check
@app.route("/")
def index():
    return "Bot is running!"

# Start the bot
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        raise
