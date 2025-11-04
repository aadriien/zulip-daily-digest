###############################################################################
##  `parse.py`                                                               ##
##                                                                           ##
##  Purpose: Extracts relevant context from messages in streams              ##
###############################################################################


from src.utils import get_all_channels, fetch_prev_day_messages
from src.summarize import summarize_messages


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

    # for m in messages_compact:
    #     print(f"\n{m}")

    return messages_compact


def review_all_channels(client):
    channels = get_all_channels(client)

    for channel_obj in channels:
        stream_name, stream_id = channel_obj["stream_name"], channel_obj["stream_id"]

        # For the time being, skip a few channels, e.g. checkins & alumni checkins
        CHANNELS_TO_SKIP = [
            "checkins", 
            "alumni checkins", 
            "checkins - in person", 
            "rsvps"
        ]
        if stream_name in CHANNELS_TO_SKIP:
            continue

        messages_full = fetch_prev_day_messages(client, stream_name)

        if messages_full:
            # print(f"\n\nREVIEWING CHANNEL: {stream_name}\n")
            messages_compact = extract_messages_info(messages_full)

            summarized = summarize_messages(messages_compact)
            print(f"\n\nSUMMARY FOR CHANNEL — {stream_name}:")
            print(f"\n{summarized}\n")




# GENERAL APPROACH:

# generate summaries for all channels
# for each channel, get list of subscribed users
# append specific channel summary to each subscribed user's mapping list
# after iterating over channels, focus on individual users
# take each user's list from earlier to construct full summaries
# send out notification DM to them




