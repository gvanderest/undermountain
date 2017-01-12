"""
EXAMPLE MODULE
"""
from utils.collection import GameCollection, Index, CollectionEntity
from mud.module import Module
from mud.manager import Manager
import logging


class Character(CollectionEntity):
    pass


class Characters(GameCollection):
    WRAPPER_CLASS = Character

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
        Characters = self.game.get_injector('Characters')

        chars = Characters.query({
            "room_id": "market_square",
        })

        logging.info("tick")
        print("Characters in room market_square:")
        if chars:
            for char in chars:
                count = char.get("count", 0)
                count += 1
                char.count = count
                char.save()
                print("* {} - {}".format(char.name, char.count))
        else:
            print("No characters")

        return event


class Entities(GameCollection):
    pass


class ExampleModule(Module):
    MODULE_NAME = "ExampleModule"
    VERSION = "0.1.0"

    INJECTORS = {
        "Characters": Characters,
    }

    MANAGERS = [
        ExampleManager,
    ]
