from mud import game, logging, settings
import asyncio
import argparse
import uvloop

uvloop.install()

ACTION_START = "start"
ACTION_BACKUP = "backup"
ACTION_RESTORE = "restore"

def parse_arguments():
    """Parse arguments provided."""
    parser = argparse.ArgumentParser(description="Undermountain Utility Script")
    parser.add_argument(
        "action",
        type=str,
        help="Action to perform",
        choices=[ACTION_START, ACTION_BACKUP, ACTION_RESTORE],
    )
    return parser.parse_args()


def execute():
    logging.info(settings.NAME)

    args = parse_arguments()
    if args.action == ACTION_START:
        GAME = game.Game()

        loop = asyncio.get_event_loop()
        loop.set_debug(True)

        try:
            loop.run_until_complete(GAME.start())
        except KeyboardInterrupt:
            logging.info("")
            logging.info(GAME.t("SHUTDOWN_MESSAGE"))
            GAME.stop()

        loop.close()
