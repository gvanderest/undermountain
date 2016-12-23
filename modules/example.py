"""
EXAMPLE MODULE
"""
from utils.collection import Collection, Index
from mud.module import Module
from mud.manager import Manager
import logging


class Characters(Collection):
    NAME = "characters"
    INDEXES = [
        Index("id", required=True, unique=True),
        Index("name", required=True, unique=True),
        Index("room_id"),
    ]


class ExampleManager(Manager):
    HANDLE_EVENTS = [
        "GAME_TICK",
    ]

    def handle_event(self, event):
        Characters, Entities = \
                self.game.get_injectors('Characters', 'Entities')

        chars = Characters.query({
            "room_id": "market_square",
        })

        logging.info("tick")
        print("Characters in room market_square:")
        if chars:
            for char in chars:
                print("* {}".format(char["name"]))
        else:
            print("No characters")

        return event


class Entities(Collection):
    pass


class ExampleModule(Module):
    MODULE_NAME = "ExampleModule"
    VERSION = "0.1.0"

    INJECTORS = {
        "Characters": Characters,
        "Entities": Entities,
    }

    MANAGERS = [
        ExampleManager,
    ]
