from mud.module import Module
from mud.inject import inject
from mud.collection import Collection, Entity, FileStorage


class Socials(Collection):
    ENTITY_CLASS = Entity
    STORAGE_CLASS = FileStorage

@inject("Socials")
def socials_command(self, Socials, *args, **kwargs):
    # TO_DO Table-fy this.
    self.echo("Socials List")
    for social in Socials.query():
        self.echo(social.name)

class SocialsModule(Module):
    DESCRIPTION = "Allow players to edit socials."

    def __init__(self, game):
        super(SocialsModule, self).__init__(game)
        self.game.register_command("socials", socials_command)
        # self.game.register_command("sedit", social_edit_command)
        self.game.register_injector(Socials)
        coll = self.game.get_injector("Socials")
        for social in coll.query():
            self.game.register_command(social.name, handle_social)


@inject("Socials")
def handle_social(self, name, args, Socials, **kwargs):

    bad_target = False  # In the event that a bad target is supplied 'hug zkjhkfjh' the social itself fails.

    if args:
        prop_target = args.pop[0].lower()
        target = self.find_target(prop_target)
    else:
        prop_target = None
        target = None

    if prop_target and not target:
        bad_target = True

    if not bad_target:  # either a target was supplied and found, or none supplied.
        social = Socials.get({"name": name})
        targets = self.find_targets()

        others = targets
        others = list(others)
        others.remove(self)
        if target:
            if target == self:
                self.echo(social.actor_auto)
                if others:
                    for other in others:
                        other.echo(social.others_auto)
            else:
                self.echo(social.actor_found_target)
                target.echo(social.target_found)
                others.remove(target)
                if others:
                    for other in others:
                        other.echo(social.others_found)
        else:
            self.echo(social.actor_no_arg)
            if others:
                for other in others:
                    other.echo(social.others_no_arg)
    else:
        self.echo("Target not found.")


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

SEDIT ( sedit_others_no_target )
{
  SOCIAL_TYPE * social;

  EDIT_SOCIAL ( ch, social );

  if ( argument[0] == '\0' )
  {
    send_to_char ( "Syntax:  7 [string]\n\r", ch );
    return FALSE;
  }

  free_string ( &social->others_no_target );

  str_dup ( &social->others_no_target, argument );

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
