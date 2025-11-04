###############################################################################
##  `notifier.py`                                                            ##
##                                                                           ##
##  Purpose: Sends DM to user with daily digest text content                 ##
###############################################################################


from src.parse import review_all_channels


def send_dm(client, user_id, text_content):
    # Send DM to user who reached out
    client.send_message({
        "type": "private",
        "to": [user_id],
        "content": text_content
    })


def construct_user_digest(channel_summaries_obj):
    full_digest = ""

    for summary_obj in channel_summaries_obj:
        stream_name, summary = summary_obj["stream_name"], summary_obj["summary"]

        headline_summary = f"#**{stream_name}**\n{summary}\n\n"
        full_digest += headline_summary

    return full_digest


def send_users_digests(client):
    # Get all mappings for opt-in users
    users_summaries_digest = review_all_channels(client)

    for user_id, summaries_objs in users_summaries_digest.items():
        full_digest = construct_user_digest(summaries_objs)
        send_dm(client, user_id, full_digest)


