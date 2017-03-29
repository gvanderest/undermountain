from utils.collection import EntityCollection, CollectionEntity
import logging


class Collection(EntityCollection):
    def __init__(self, game):
        self.game = game

        state = self.game.get_state()
        records = state.get(self.NAME, {})
        state[self.NAME] = records
        self.game.set_state(state)
        logging.info("LOADED {} OBJECTS".format(len(records)))

        super(Collection, self).__init__(records)

    def wrap_record(self, record):
        wrapped = super(Collection, self).wrap_record(record)
        wrapped._game = self.game
        return wrapped

    def get_game(self):
        """Return the Game."""
        return self.game


class Entity(CollectionEntity):
    def get_game(self):
        """Return the Game."""
        return self._game
