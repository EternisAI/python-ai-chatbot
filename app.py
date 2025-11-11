import os
import logging

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from listeners import register_listeners

# Initialization
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Starting Slack Bot Application...")
logger.info(f"SLACK_BOT_TOKEN present: {bool(os.environ.get('SLACK_BOT_TOKEN'))}")
logger.info(f"SLACK_APP_TOKEN present: {bool(os.environ.get('SLACK_APP_TOKEN'))}")
logger.info(f"OPENAI_API_KEY present: {bool(os.environ.get('OPENAI_API_KEY'))}")

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# Register Listeners
logger.info("Registering listeners...")
register_listeners(app)
logger.info("Listeners registered successfully!")

# Start Bolt app
if __name__ == "__main__":
    logger.info("Starting Socket Mode Handler...")
    SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN")).start()
    logger.info("Bot is now running!")
