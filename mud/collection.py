from utils.collection import Collection as BaseCollection


class Collection(BaseCollection):
    def __init__(self, game):
        self.game = game
        state = self.game.get_state()
        records = state.get(self.NAME, {})
        state[self.NAME] = self.records
        self.game.set_state(state)

        super(Collection, self).__init__(records)
