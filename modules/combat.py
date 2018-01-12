from logging import debug
from math import ceil
from mud.timer_manager import TimerManager
from mud.module import Module
from mud.inject import inject
from mud.collection import Collection
from modules.core import Character
from random import randint


class Battles(Collection):
    def get_damage_amount_text(self, amount):
        if amount < 10:
            return "scratches"
        else:
            return "{B<{w<{B< {BE{bRA{wD{WIC{wA{bTE{BS {B>{W>{B>"

    def attempt_hit(self, actor, target):
        amount = \
            randint(1, 3) if actor.name != "a giant bear" else randint(50, 70)
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

        target.stats.current_hp.base -= amount

    def initiate(self, actor, target):
        actor.fighting = True
        target.fighting = True

        for _ in range(3):
            self.attempt_hit(actor, target)

            if target.stats.current_hp.base > 0:
                continue

            event = target.emit("before:death")
            if event.blocked:
                continue

            target.act("{{c{}{{c is {{CDEAD{{c!{{x".format(target.name))
            target.echo("You have been {RKILLED{x!")

            experience = randint(200, 300)
            actor.gain_experience(experience)

            target.act("You hear {self.name}{x's death cry.")
            actor.echo("Death gives you one silver coin for your sacrifice.")
            target.echo()

            target.emit("after:death", unblockable=True)

            target.fighting = False
            actor.fighting = False
            actor.save()

            if not isinstance(target, Character):
                target.delete()
            else:
                target.die()
                target.save()
                target.force("look")

            break


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
