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
    social = Socials.get({"name": name})
    self.echo("args: {}".format(args))
    if not social:
        self.echo("Could not find social.")
        return

    if args:
        self.echo("arguments are: {}".format(args))
        target = args[0]
    else:
        target = None

    if target:
        self.echo("You are trying to use the {} social and your target is: {}".format(social.name, target))
    else:
        self.echo("You are trying to use the {} social.".format(social.name))
        self.echo("target_is_required: {}".format(social.target_is_required))
        self.echo("actor_no_arg: {}".format(social.actor_no_arg))
        self.echo("others_no_arg: {}".format(social.others_no_arg))
        self.echo("actor_found_target: {}".format(social.actor_found_target))



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
