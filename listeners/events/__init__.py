from slack_bolt import App
from .app_home_opened import app_home_opened_callback
from .app_mentioned import app_mentioned_callback
from .app_messaged import app_messaged_callback


def register(app: App):
    app.event("app_home_opened")(app_home_opened_callback)
    app.event("app_mention")(app_mentioned_callback)
    # Only listen to direct messages (DMs), not all messages
    app.event({"type": "message", "channel_type": "im"})(app_messaged_callback)
