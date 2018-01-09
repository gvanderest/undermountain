from mud.timer_manager import TimerManager
from mud.module import Module
from mud.inject import inject
from mud.collection import Collection

import logging
import math


class Battles(Collection):
    pass


class CombatManager(TimerManager):
    TIMER_DELAY = 1.0

    @inject("Battles")
    def tick(self, Battles):
        logging.debug("Battles!! {}".format(Battles.query()))


class RegenerationManager(TimerManager):
    TIMER_DELAY = 5.0

    @inject("Characters")
    def tick(self, Characters):
        logging.debug("Regenerating Characters")
        for char in Characters.query({"online": True}):
            stats = char.stats

            hp = stats.current_hp.base
            max_hp = stats.hp.total
            new_hp = min(max_hp, hp + int(math.ceil(max_hp * 0.1)))
            char.stats.current_hp.base = new_hp

            mana = stats.current_mana.base
            max_mana = stats.mana.total
            new_mana = min(max_mana, mana + int(math.ceil(max_mana * 0.1)))
            char.stats.current_mana.base = new_mana

            char.save()

            logging.debug("Regenerated resources for {}".format(char.name))
        logging.debug("Regenerated Characters")


class CombatModule(Module):
    DESCRIPTION = "Add the ability to support round-based combat"

    def __init__(self, game):
        super(CombatModule, self).__init__(game)
        self.game.register_manager(CombatManager)
        self.game.register_manager(RegenerationManager)
        self.game.register_injector(Battles)
