# Utility functions for handling Slack message operations

# Slack's message limit is 4,000 characters, use 3,900 to be safe
MAX_MESSAGE_LENGTH = 3900


def split_message(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> list[str]:
    """
    Split a message into chunks that fit within Slack's message limit.
    Tries to split on newlines first, then falls back to character limit.
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    remaining = text

    while remaining:
        if len(remaining) <= max_length:
            chunks.append(remaining)
            break

        # Try to find a good split point (newline) within the limit
        split_point = remaining.rfind("\n", 0, max_length)

        # If no newline found, try to split on space
        if split_point == -1 or split_point < max_length // 2:
            split_point = remaining.rfind(" ", 0, max_length)

        # If still no good point, just split at max length
        if split_point == -1 or split_point < max_length // 2:
            split_point = max_length

        chunks.append(remaining[:split_point])
        remaining = remaining[split_point:].lstrip()

    return chunks


def send_long_message(
    client, channel_id: str, thread_ts: str, waiting_message_ts: str, text: str
):
    """
    Send a potentially long message, splitting into multiple messages if needed.
    Updates the waiting message with the first chunk, then posts additional
    messages as replies in the thread.
    """
    chunks = split_message(text)

    # Update the waiting message with the first chunk
    client.chat_update(channel=channel_id, ts=waiting_message_ts, text=chunks[0])

    # Post remaining chunks as separate messages in the thread
    for chunk in chunks[1:]:
        client.chat_postMessage(channel=channel_id, thread_ts=thread_ts, text=chunk)
