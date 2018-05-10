from mud.module import Module
from mud.inject import inject
from mud.collection import Collection
from modules.core import Character


class Socials(Collection):
    ENTITY_CLASS = Social
    STORAGE_CLASS = FileStorage

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
#    theres also `actor_nobody_actor` and `actor_nobody_room` templates (edited)
#    and `{actor.name}` and `{target.name}` placeholders
#    REVIEW: combat, core and telnet usage of Actor.act code


    def __init__(self, name, actor_no_arg=None, others_no_arg=None, actor_found_target=None, others_found=None, target_found=None, actor_auto=None, others_auto=None):
        self.name = name  # The name of the social; 'smile', 'hug', etc.
        self.actor_no_arg = actor_no_arg
        self.others_no_arg = others_no_arg
        self.actor_found_target = actor_found_target
        self.others_found = others_found
        self.target_found = target_found
        self.actor_auto = actor_auto
        self.others_auto = others_auto

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


class SocialsModule(Module):
    DESCRIPTION = "Allow players to edit socials."

    def __init__(self, game):
        super(SocialModule, self).__init__(game)
        self.game.register_command("socials", socials_command)
        #self.game.register_command("sedit", social_edit_command)


"""
borrowed from olc_act.c from wdmud
check these for how to handle 'setters'

// Dynamic Socials - Coyote
SEDIT ( sedit_char_auto )
{
  SOCIAL_TYPE * social;

  EDIT_SOCIAL ( ch, social );


  if ( argument[0] == '\0' )
  {
    send_to_char ( "Syntax:  1 [string]\n\r", ch );
    return FALSE;
  }

  free_string ( &social->char_auto );

  str_dup ( &social->char_auto, argument );

  send_to_char ( "Self-Target, to Character string set.\n\r", ch );
  return TRUE;
}

SEDIT ( sedit_others_auto )
{
  SOCIAL_TYPE * social;

  EDIT_SOCIAL ( ch, social );

  if ( argument[0] == '\0' )
  {
    send_to_char ( "Syntax:  2 [string]\n\r", ch );
    return FALSE;
  }

  free_string ( &social->others_auto );

  str_dup ( &social->others_auto, argument );

  send_to_char ( "Self-Target, to others string set.\n\r", ch );
  return TRUE;
}

SEDIT ( sedit_char_found )
{
  SOCIAL_TYPE * social;

  EDIT_SOCIAL ( ch, social );

  if ( argument[0] == '\0' )
  {
    send_to_char ( "Syntax:  3 [string]\n\r", ch );
    return FALSE;
  }

  free_string ( &social->char_found );

  str_dup ( &social->char_found, argument );

  send_to_char ( "Other-Target, to Character string set.\n\r", ch );
  return TRUE;
}

SEDIT ( sedit_vict_found )
{
  SOCIAL_TYPE * social;

  EDIT_SOCIAL ( ch, social );

  if ( argument[0] == '\0' )
  {
    send_to_char ( "Syntax:  4 [string]\n\r", ch );
    return FALSE;
  }

  free_string ( &social->vict_found );

  str_dup ( &social->vict_found, argument );

  send_to_char ( "Other-Target, to Victim string set.\n\r", ch );
  return TRUE;
}

SEDIT ( sedit_others_found )
{
  SOCIAL_TYPE * social;

  EDIT_SOCIAL ( ch, social );

  if ( argument[0] == '\0' )
  {
    send_to_char ( "Syntax:  5 [string]\n\r", ch );
    return FALSE;
  }

  free_string ( &social->others_found );

  str_dup ( &social->others_found, argument );

  send_to_char ( "Other-Target, to others string set.\n\r", ch );
  return TRUE;

}

SEDIT ( sedit_char_no_arg )
{
  SOCIAL_TYPE * social;

  EDIT_SOCIAL ( ch, social );

  if ( argument[0] == '\0' )
  {
    send_to_char ( "Syntax:  6 [string]\n\r", ch );
    return FALSE;
  }

  free_string ( &social->char_no_arg );

  str_dup ( &social->char_no_arg, argument );

  send_to_char ( "No Target, to Character string set.\n\r", ch );
  return TRUE;
}

SEDIT ( sedit_others_no_arg )
{
  SOCIAL_TYPE * social;

  EDIT_SOCIAL ( ch, social );

  if ( argument[0] == '\0' )
  {
    send_to_char ( "Syntax:  7 [string]\n\r", ch );
    return FALSE;
  }

  free_string ( &social->others_no_arg );

  str_dup ( &social->others_no_arg, argument );

  send_to_char ( "No Target, to others string set.\n\r", ch );
  return TRUE;

}

SEDIT ( sedit_char_not_found )
{
  SOCIAL_TYPE * social;

  EDIT_SOCIAL ( ch, social );

  if ( argument[0] == '\0' )
  {
    send_to_char ( "Syntax:  3 [string]\n\r", ch );
    return FALSE;
  }

  free_string ( &social->char_not_found );

  str_dup ( &social->char_not_found , argument );

  send_to_char ( "Target not found string set.\n\r", ch );
  return TRUE;
}

"""
