###############################################################################
##  `bot.py`                                                                 ##
##                                                                           ##
##  Purpose: Handles all setup & logic for Zulip daily-digest bot            ##
###############################################################################


import click # for args via CLI 

from src.setup import create_client 
from src.utils import get_all_subscribers


class DailyDigestBot:
    def __init__(self):
        self.client = create_client()


# Instantiate bot just once as a global so Click can access it 
bot = DailyDigestBot()


@click.command()
@click.option("--client", is_flag=True, help="Run in client mode (one-off script)")
@click.option("--service", is_flag=True, help="Run in service mode (live bot)")
def launch_program(client, service):
    # Ensure only 1 mode specified
    flags = [client, service]
    if sum(flags) != 1:
        raise click.UsageError("ERROR: You must provide exactly one of --client or --service")

    # Bot acts as a one-off script to perform action
    if client:
        click.echo("Running in client (one-off) mode...")
        
        get_all_subscribers(bot.client, "test-bot")


    # Bot acts as a service running in real-time
    elif service:
        click.echo(f"Running in service (live) mode...")
        

    else:
        raise click.UsageError("ERROR: Please specify --client or --service")


if __name__ == "__main__":
    # Python Click to pass CLI arguments
    # For example,
    #   `python3 bot.py --client`
    #   `python3 bot.py --service`
    # Or alternativey, with Makefile rules
    #   `make run-client`
    #   `make run-service`

    launch_program()


