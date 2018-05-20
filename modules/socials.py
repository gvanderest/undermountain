from mud.module import Module
from mud.inject import inject
from mud.collection import Collection, Entity, FileStorage
from utils.tablefy import tablefy

class Socials(Collection):
    ENTITY_CLASS = Entity
    STORAGE_CLASS = FileStorage

@inject("Socials")
def socials_command(self, Socials, *args, **kwargs):
    # TO_DO Table-fy this.
    all_socials = []
    for social in Socials.query():
        all_socials.append(social.name)

    if all_socials:
        msg = tablefy(all_socials)
        self.echo(msg)
    else:
        self.echo("There are no social commands loaded.")


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
        #self.echo("name is: {} and args are: {} with type {}".format(name, args, type(args)))  # troubleshooting
        prop_target = args.pop(0).lower()
        targets = list(self.find_targets())
        #self.echo("targets returns are: {}".format(targets))  # troubleshooting
        target = self.find_target(prop_target)
    else:
        prop_target = None
        target = None

    if prop_target and not target:
        bad_target = True

    if not bad_target:  # either a target was supplied and found, or none supplied.

        social = Socials.get({"name": name})

        if target:
            if target == self:
                self.act_to(self, social.actor_auto)
                self.act(social.others_auto)
                return

            self.act_to(target, social.target_found)
            self.act_to(self, social.actor_found_target)
            self.act(social.others_found, exclude=[self, target])

        else:  # untargeted social
            self.act_to(self, social.actor_no_arg)
            self.act(social.others_no_arg, exclude=self)

    else:
        self.echo("You couldn't find your target.")


@inject("Socials")
def handle_social_old(self, name, args, Socials, **kwargs):

    bad_target = False  # In the event that a bad target is supplied 'hug zkjhkfjh' the social itself fails.

    if args:
        #self.echo("name is: {} and args are: {} with type {}".format(name, args, type(args)))  # troubleshooting
        prop_target = args.pop(0).lower()
        targets = list(self.find_targets())
        #self.echo("targets returns are: {}".format(targets))  # troubleshooting
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
                # self.echo(social.actor_auto)
                msg = self.replace_tokens(social.actor_auto, target)
                if msg:
                    self.echo(msg)
                    if others:
                        msg = self.replace_tokens(social.others_auto, target)
                        if msg:
                            for other in others:
                                other.echo(msg)
            else:
                # handle_targeted social, but not targeted at self.
                msg = self.replace_tokens(social.actor_found_target, target)
                if msg:
                    self.echo(msg)  # echo to actor

                # now echo to the target
                msg = self.replace_tokens(social.target_found, target)
                if msg:
                    target.echo(msg)

                # handle any remaining spectators
                others.remove(target)
                if others:
                    msg = self.replace_tokens(social.others_found, target)
                    if msg:
                        for other in others:
                            other.echo(msg)
        else:
            msg = self.replace_tokens(social.actor_no_arg)
            if msg:
                self.echo(msg)

            if others:
                msg = self.replace_tokens(social.others_no_arg)
                if msg:
                    for other in others:
                        other.echo(msg)
    else:
        self.echo("You couldn't find your target.")


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
