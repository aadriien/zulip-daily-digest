###############################################################################
##  `parse.py`                                                               ##
##                                                                           ##
##  Purpose: Extracts relevant context from messages in streams              ##
###############################################################################


from src.utils import get_all_channels, get_all_subscribers, fetch_prev_day_messages
from src.summarize import summarize_messages


# Only provide service for those who have opted in
OPT_IN_USERS = [890656, 902241]


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

    return messages_compact


def review_all_channels(client):
    # Maintain mapping of user IDs to their subscribed channel summaries
    users_summaries_digest = {user_id: [] for user_id in OPT_IN_USERS}

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

        # TEST = ["397 Bridge", "pairing", "audio programming", "crosswords"]

        # if stream_name not in TEST:
        #     continue

        if stream_name in CHANNELS_TO_SKIP:
            continue

        messages_full = fetch_prev_day_messages(client, stream_name)

        if messages_full:
            # print(f"\n\nREVIEWING CHANNEL: {stream_name}\n")
            messages_compact = extract_messages_info(messages_full)

            summarized_channel = summarize_messages(messages_compact)
            print(f"\n\nSUMMARY FOR CHANNEL — {stream_name}:")
            print(f"\n{summarized_channel}\n")

            channel_summary_obj = {
                "stream_name": stream_name,
                "summary": summarized_channel
            }

            # Prep for appending summaries onto subscribed users' mappings inventory
            subscribers = get_all_subscribers(client, stream_name)

            # Ensure only focusing on opt-in users (via intersection)
            subscribers_set, opt_in_set = set(subscribers), set(OPT_IN_USERS)
            opt_in_subscribers = list(subscribers_set & opt_in_set)

            print(f"\nOpt-in users for channel: {stream_name} — {opt_in_subscribers}")
            
            for subscriber in opt_in_subscribers:
                users_summaries_digest[subscriber].append(channel_summary_obj)

    return users_summaries_digest



