from logging import debug
from math import ceil
from mud.timer_manager import TimerManager
from mud.module import Module
from mud.inject import inject
from mud.collection import Collection
from modules.core import Character
from random import randint


class Battles(Collection):
    def initiate(self, actor, target):
        actor.echo("You attack {}".format(target.name))
        actor.act("{} attacks {}".format(actor.name, target.name))

        event = target.emit("before:death")
        if event.blocked:
            return

        target.act("{} is dead!".format(target.name))
        target.echo("You have been killed!")

        target.emit("after:death", unblockable=True)

        if not isinstance(target, Character):
            target.delete()
        else:
            target.die()
            target.save()

        experience = randint(200, 300)
        actor.gain_experience(experience)
        actor.save()


class CombatManager(TimerManager):
    TIMER_DELAY = 1.0

    @inject("Battles")
    def tick(self, Battles):
        debug("Battles!! {}".format(Battles.query()))


@inject("Actors", "Battles")
def kill_command(self, args, Actors, Battles, **kwargs):
    if not args:
        self.echo("Kill what?")
        return

    room = self.room
    name = args.pop(0)

    target = None
    for actor in room.actors:
        if target:
            break

        # Enable player-killing later.
        if isinstance(actor, Character):
            continue

        keywords = actor.name.lower().split()
        for keyword in keywords:
            if keyword.startswith(name):
                target = actor
                break

    if not target:
        self.echo("Can't find that here.")
        return

    Battles.initiate(self, target)


class RegenerationManager(TimerManager):
    TIMER_DELAY = 5.0

    @inject("Characters")
    def tick(self, Characters):
        debug("Regenerating Characters")
        for char in Characters.query({"online": True}):
            stats = char.stats

            hp = stats.current_hp.base
            max_hp = stats.hp.total
            new_hp = min(max_hp, hp + int(ceil(max_hp * 0.1)))
            char.stats.current_hp.base = new_hp

            mana = stats.current_mana.base
            max_mana = stats.mana.total
            new_mana = min(max_mana, mana + int(ceil(max_mana * 0.1)))
            char.stats.current_mana.base = new_mana

            char.save()

            debug("Regenerated resources for {}".format(char.name))
        debug("Regenerated Characters")


class CombatModule(Module):
    DESCRIPTION = "Add the ability to support round-based combat"

    def __init__(self, game):
        super(CombatModule, self).__init__(game)
        self.game.register_manager(CombatManager)
        self.game.register_manager(RegenerationManager)
        self.game.register_injector(Battles)
        self.game.register_command("kill", kill_command)
        self.game.register_command("murder", kill_command)
        self.game.register_command("attack", kill_command)
        self.game.register_command("battle", kill_command)
