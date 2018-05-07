from logging import debug
from math import ceil
from mud.timer_manager import TimerManager
from mud.module import Module
from mud.inject import inject
from mud.collection import Collection
from modules.core import Character
from random import randint, choice


class Socials(Collection):
    def initiate(self, actor, target):
        actor.target_ids = (actor.target_ids or []) + [target.id]
        target.target_ids = (target.target_ids or []) + [actor.id]

        actor.save()
        target.save()

        battle = Battle(actor)
        battle.process_round()


class Social(object):
    """
    Socials should have: actor, target(can be None, actor, or target)

    self.name = "smile"                                                             # name of the social
    self.actor_no_arg = "Smile at who?"  | "You smile."                             # no target, to actor
    self.others_no_arg = "<actor> tries to smile, but fails." | "<actor> smiles."   # no target,  to others
    self.actor_found_target = "You smile at <target>."                              # target found, to actor
    self.others_found = "<actor> smiles at <target>."                               # target found, to others
    self.target_found = "<actor> smiles at you."                                    # target found, to target
    self.actor_auto = "You smile at yourself... you feel good about YOU!"           # actor == target, to actor
    self.others_auto = "<actor> smiles at himself. What a wacko."                   # actor == target, to others

    From Kel:

    because this will use an “act” type method, we’ll let it handle that itself.. and within the string, I’d say put a placeholder that will be replaced out, just designate whether it’s the actor or target
    so.. the following would work: `{actor.himself}` `{target.herself}` `{actor.itself}` `{actor.him}` `{target.her}` (edited)
    so you could technically do `{actor.himself}` or `{actor.him}self`
    ther’es also `actor_nobody_actor` and `actor_nobody_room` templates (edited)
    and `{actor.name}` and `{target.name}` placeholders


    """
    def __init__(self, actor):
        self.actor = actor

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

        target.stats.current_hp.base -= amount
