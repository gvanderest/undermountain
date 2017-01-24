"""
EXAMPLE MODULE
"""
from utils.collection import GameCollection, Index, CollectionEntity
from mud.module import Module
from mud.manager import Manager
import logging


class RoomEntity(CollectionEntity):
    def get_room(self):
        Rooms = self.get_injector("Rooms")
        return Rooms.find(self.room_id)


class Area(CollectionEntity):
    pass


class Areas(GameCollection):
    WRAPPER_CLASS = Area

    NAME = "areas"
    INDEXES = [
        Index("id", required=True, unique=True),
        Index("name", required=True, unique=True),
    ]


class RoomExit(CollectionEntity):
    pass


class RoomExits(GameCollection):
    WRAPPER_CLASS = RoomExit

    NAME = "room_exits"
    INDEXES = [
        Index("id", required=True, unique=True),
        Index("direction_id"),
        Index("room_id"),
    ]


class Room(CollectionEntity):
    def get_area(self):
        Areas = self.get_injector("Areas")
        return Areas.find(self.area_id)


class Rooms(GameCollection):
    WRAPPER_CLASS = Room

    NAME = "rooms"
    INDEXES = [
        Index("id", required=True, unique=True),
        Index("name", required=True, unique=True),
        Index("area_id"),
    ]


class Actor(RoomEntity):
    def set_connection(self, connection):
        self._connection = connection

    def get_connection(self):
        return self._connection

    def echo(self, message):
        connection = self._connection
        if connection is None:
            return
        connection.writeln(message)


class Actors(GameCollection):
    WRAPPER_CLASS = Actor

    NAME = "actor"
    INDEXES = [
        Index("id", required=True, unique=True),
        Index("name", required=True, unique=True),
        Index("room_id"),
    ]


class Character(Actor):
    pass


class Characters(Actors):
    WRAPPER_CLASS = Character

    NAME = "characters"


class ExampleManager(Manager):
    HANDLE_EVENTS = [
        "GAME_TICK",
    ]

    def tick(self, Characters, Rooms, Areas):
        chars = Characters.query({
            "room_id": "market_square",
        })

        logging.debug("Characters in room market_square:")
        if chars:
            for char in chars:
                count = char.get("count", 0)
                count += 1
                char.count = count
                char.save()
                room = char.get_room()
                area = room.get_area()
                logging.debug("* {} - {} - {} - {}".format(
                    char.name,
                    room.name,
                    area.name,
                    char.count
                ))
        else:
            print("No characters")


class Entities(GameCollection):
    pass


class Core(Module):
    MODULE_NAME = "Core"
    VERSION = "0.1.0"

    INJECTORS = {
        "Areas": Areas,
        "Rooms": Rooms,
        "RoomExits": RoomExits,
        "Actors": Actors,
        "Characters": Characters,
    }

    MANAGERS = [
        ExampleManager,
    ]
