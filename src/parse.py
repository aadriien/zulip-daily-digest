###############################################################################
##  `parse.py`                                                               ##
##                                                                           ##
##  Purpose: Extracts relevant context from messages in streams              ##
###############################################################################


from src.utils import get_all_channels, fetch_prev_day_messages


def extract_messages_info(messages_full):
    RELEVANT_FIELDS = [
        "id",
        "content", 
        "subject", 
        "sender_full_name"
    ]

    messages_compact = []
    for message in messages_full:
        new_msg_obj = {}

        for field in RELEVANT_FIELDS:
            if field in message:
                new_msg_obj[field] = message[field]

        messages_compact.append(new_msg_obj)

    for m in messages_compact:
        print(f"\n{m}")

    return messages_compact


def review_all_channels(client):
    channels = get_all_channels(client)

    for channel_obj in channels:
        stream_name, stream_id = channel_obj["stream_name"], channel_obj["stream_id"]
        messages_full = fetch_prev_day_messages(client, stream_name)

        if messages_full:
            print(f"\n\nREVIEWING CHANNEL: {stream_name}\n")
            messages_compact = extract_messages_info(messages_full)



