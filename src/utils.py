###############################################################################
##  `utils.py`                                                               ##
##                                                                           ##
##  Purpose: Handles Zulip functionality for processing message streams      ##
###############################################################################


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


def get_all_subscribers(client, channel_stream_id):
    result = client.get_subscribers(stream=channel_stream_id)

    print(result)
    return result["subscribers"]
    



