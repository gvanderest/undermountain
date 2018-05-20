from logging import debug
from math import ceil
from mud.timer_manager import TimerManager
from mud.module import Module
from mud.inject import inject
from mud.collection import Collection
from modules.core import Character
from random import randint, choice


class Battles(Collection):
    def initiate(self, actor, target):
        actor.target_ids = (actor.target_ids or []) + [target.id]
        target.target_ids = (target.target_ids or []) + [actor.id]

        actor.save()
        target.save()

        battle = Battle(actor)
        battle.process_round()


class Battle(object):
    def __init__(self, actor):
        self.actor = actor

    def process_round(self):
        actor = self.actor
        actor.refresh()

        event = actor.handle("before:combat_turn")
        if event.blocked:
            return

        target = next(actor.targets)

        for i in range(3):
            self.attempt_hit(actor, target)

            if target.stats.hp.base > 0:
                continue

            event = target.emit("before:death")
            if event.blocked:
                target.stats.hp.base = 0
                continue

            target.act("{{c{}{{c is {{CDEAD{{c!{{x".format(target.name))
            target.echo("You have been {RKILLED{x!")

            experience = randint(200, 300)
            actor.gain_experience(experience)

            target.act("You hear {self.name}{x's death cry.")
            actor.echo("Death gives you one silver coin for your sacrifice.")
            target.echo()

            target.emit("after:death", unblockable=True)

            for target_target in target.targets:
                if target.id in target_target.target_ids:
                    target_target.target_ids.remove(target.id)
                target_target.save()

            target.target_ids = []

            if not isinstance(target, Character):
                target.delete()
            else:
                target.die()
                target.save()
                target.force("look")

            return

        actor.handle("after:combat_turn")

    def get_damage_amount_text(self, amount):
        if amount < 10:
            return "scratches"
        else:
            return "{B<{w<{B< {BE{bRA{wD{WIC{wA{bTE{BS {B>{W>{B>"

    def attempt_hit(self, actor, target):
        amount = randint(1, 20)
        noun = "punch" if isinstance(actor, Character) else "claw"
        self.damage(actor, target, noun=noun, amount=amount, silent=False)

    def damage(self, actor, target, noun, amount, silent=False):
        if not silent:
            amount_text = self.get_damage_amount_text(amount)
            actor.echo(
                "{{BYour {}{{B {}{{B {}{{B! {{B-{{R={{C{}{{R={{B-{{x".format(
                    noun, amount_text, target.name, amount))
            actor.act(
                "{{c{}'s {}{{c {}{{c {}{{c! {{B-{{R={{C{}{{R={{B-{{x".format(
                    actor.name, noun, amount_text, target.name, amount),
                exclude=target)
            target.echo(
                "{{B{}'s {}{{B {}{{B you! {{B-{{R={{C{}{{R={{B-{{x".format(
                    actor.name, noun, amount_text, amount))

        target.stats.hp.base -= amount


class CombatManager(TimerManager):
    TIMER_DELAY = 1.0

    @inject("Battles")
    def tick(self, Battles):
        debug("Battles!! {}".format(Battles.query()))
        self.process_battles()

    @inject("Actors", "Characters")
    def process_battles(self, Actors, Characters):
        for coll in [Actors, Characters]:
            for actor in coll.query():
                if not actor.target_ids:
                    continue

                battle = Battle(actor)
                battle.process_round()


def flee_command(self, *args, **kwargs):
    if not self.target_ids:
        self.echo("You aren't fighting anyone!")
        return

    room = self.room
    exits = room.exits
    if not exits:
        self.echo("There is nowhere to go!")
        return

    random_exit = choice(list(exits.values()))

    # TODO Make this better
    for target in self.targets:
        if target.target_ids and self.id in target.target_ids:
            target.target_ids.remove(self.id)
        target.save()
    self.targets = []
    self.room = random_exit.room
    self.save()
    self.force("look")


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

        keywords = actor.name.lower().split()
        for keyword in keywords:
            if keyword.startswith(name):
                target = actor
                break

    if target == self:
        self.echo("You can't attack yourself.")
        return

    if not target:
        self.echo("Can't find that here.")
        return

    Battles.initiate(self, target)

@inject("Actors", "Battles")
def punch_command(self, args, Actors, Battles, **kwargs):
    if not args:
        self.echo("Punch whom?")
        return

    room = self.room
    name = args.pop(0)

    target = None
    for actor in room.actors:
        if target:
            break

        keywords = actor.name.lower().split()
        for keyword in keywords:
            if keyword.startswith(name):
                target = actor
                break

    if target == self:
        self.echo("You can't punch yourself.")
        return

    if not target:
        self.echo("Can't find that here.")
        return

    self.act
    Battles.initiate(self, target)


class RegenerationManager(TimerManager):
    TIMER_DELAY = 5.0

    @inject("Characters")
    def tick(self, Characters):
        debug("Regenerating Characters")
        for char in Characters.query({"online": True}):

            if char.target_ids:
                continue

            stats = char.stats

            hp = stats.hp.base
            max_hp = stats.hp.total
            new_hp = min(max_hp, hp + int(ceil(max_hp * 0.1)))
            char.stats.hp.base = new_hp

            mana = stats.mana.base
            max_mana = stats.mana.total
            new_mana = min(max_mana, mana + int(ceil(max_mana * 0.1)))
            char.stats.mana.base = new_mana

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
        self.game.register_command("flee", flee_command)
