###############################################################################
##  `utils.py`                                                               ##
##                                                                           ##
##  Purpose: Handles Zulip functionality for processing message streams      ##
###############################################################################


def get_all_subscribers(client, channel_stream_id):
    result = client.get_subscribers(stream=channel_stream_id)

    print(result)
    return result
    

