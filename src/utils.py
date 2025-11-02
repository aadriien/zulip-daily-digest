###############################################################################
##  `utils.py`                                                               ##
##                                                                           ##
##  Purpose: Handles Zulip functionality for processing message streams      ##
###############################################################################


import time


def get_all_channels(client):
    result = client.get_streams()
    all_streams_objs = result["streams"]

    # Extract only name & ID from channel metadata
    streams_name_id = [
        {
            "stream_name": stream_obj["name"],
            "stream_id": stream_obj["stream_id"]
        }
        for stream_obj in all_streams_objs
    ]

    print(streams_name_id)
    return streams_name_id


def get_all_subscribers(client, channel_stream_name):
    result = client.get_subscribers(stream=channel_stream_name)

    print(result)
    return result["subscribers"]
    


def fetch_latest_messages(client, channel_stream, count = 200):
    # Fetch list of most recent messages from specified channel / topic
    result = client.get_messages({
        "anchor": "newest",
        "num_before": count,
        "num_after": 0,
        "narrow": [
            {"operator": "channel", "operand": channel_stream},
        ],
        "apply_markdown": False
    })

    # Stored as array of message objects
    return result.get("messages", [])


def fetch_messages_between_time(client, channel_stream, start_time, end_time):
    # Leverage helper function to retrieve latest messages
    latest_arr = fetch_latest_messages(client, channel_stream, count=200)

    if latest_arr:
        # Extract those within UTC time range
        messages = [
            message for message in latest_arr
            if start_time <= message["timestamp"] <= end_time
        ]


        for m in messages:
            print(
                time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(m["timestamp"])),
                "-", m["sender_full_name"],
                ":", m["content"]
            )

        return messages
    
    return None


def fetch_prev_day_messages(client, channel_stream):
    # All Unix timestamps in UTC seconds (e.g. 1527921326) according to Zulip
    now = int(time.time()) 
    past_24_hours = now - 86400

    print(f"\n\nNOW TIME: {now} — PAST TIME: {past_24_hours}")
    print(f"NOW TIME: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(now))} — PAST TIME: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(past_24_hours))}\n\n")

    messages = fetch_messages_between_time(
        client, 
        channel_stream, 
        start_time=past_24_hours, end_time=now
    )

    if messages:
        print(messages)
        return messages
    
    return None



