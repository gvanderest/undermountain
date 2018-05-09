from logging import debug
from math import ceil
from mud.timer_manager import TimerManager
from mud.module import Module
from mud.inject import inject
from mud.collection import Collection
from modules.core import Character
from random import randint, choice


class Socials(Collection):
    def initiate(self, actor, target=None):
        social = Social(actor, target)
        social.process_social()

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
    """

#    From Kel:
#    because this will use an “act” type method, we’ll let it handle that itself.. and within the string,
#    I’d say put a placeholder that will be replaced out, just designate whether it’s the actor or target
#    the following would work: `{actor.himself}` `{target.herself}` `{actor.itself}` `{actor.him}` `{target.her}`
#    so you could technically do `{actor.himself}` or `{actor.him}self`
#    ther’es also `actor_nobody_actor` and `actor_nobody_room` templates (edited)
#    and `{actor.name}` and `{target.name}` placeholders
#    REVIEW: combat, core and telnet usage of Actor.act code


    def __init__(self, name):
        self.name = name  # The name of the social; 'smile', 'hug', etc.

    def set_actor_no_arg(self, echo):
        self.actor_no_arg = echo

    def set_others_no_arg(self, echo):
        self.others_no_arg = echo

    def set_actor_found_target(self, echo):
        self.actor_found_target = echo

    def set_others_found(self, echo):
        self.others_found = echo

    def set_target_found(self, echo):
        self.target_found = echo

    def set_actor_auto(self, echo):
        self.actor_auto = echo

    def set_others_auto(self, echo):
        self.others_auto = echo

    # processing

    def others_are_present(self):
        pass

    def target_was_found(self):
        pass

    @inject("Characters")
    def process_social(self):
        pass


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
