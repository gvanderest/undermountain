# from mud.module import Module
# from mud.collection import Entity
#
# class EmotesModule(Module):
#     DESCRIPTION = "Emoting related commands."
#
#     def __init__(self, game):
#         super(EmotesModule, self).__init__(game)
#         self.game.register_command("emote", emote_command)
#         self.game.register_command("pmote", pmote_command)
#         self.game.register_command("xmote", xmote_command)
#         self.game.register_command("sayto", sayto_command)
#
#
# def emote_command(self, message, **kwargs):
#     if message:
#         message = "{c" + self.name + " " + message + "{x"
#         self.echo(message)
#         targets = self.find_targets()
#         targets = list(targets)
#         targets.remove(self)
#         if targets:
#             for t in targets:
#                 t.echo(message)
#     else:
#         self.echo("Emote what?")
#
# def pmote_command(self, message, **kwargs):
#     """
#     Must replace target in message with 'you' or if "target's", then replace with actor.gender.possessive
#     :param self:
#     :param prop_target: proposed target
#     :param message:
#     :param kwargs:
#     :return:
#     pmote looks at Player to see if Player's shoes are untied. -- Actor and rest of room, excepting Player.
#     Actor looks at you to see if your shoes are untied. -- only Player sees this echo.
#
#     """
#
#     if message:
#
#         targets = self.find_targets()
#         targets = list(targets)
#         targets.remove(self)
#
#         self.echo("{B" + message + "{x")
#
#         if targets:
#             valid_targets = []
#             valid_targets_keys = []
#             for target in targets:
#                 keys = target.name.split()
#                 for key in keys:
#                     if key.istitle():
#                         valid_targets.append(target)
#                         valid_targets_keys.append(key)
#
#             if valid_targets:
#                 for key in valid_targets_keys:
#
#                 self.echo("Valid targets are: {}".format(valid_targets))
#                 self.echo("Valid targets were found.")
#                 # do replacements if any matches are found.
#
#
#
#     else:
#         self.echo("Pmote what?")
#
#
# def xmote_command(self, message, **kwargs):
#     self.echo("wee, an xmote!")
#
# def sayto_command(self, message, **kwargs):
#     self.echo("wee, a sayto!")
#
# """
# Examine the following, pulled from core.py
#
# def say_command(self, message, **kwargs):
#     if not message:
#         self.echo("Say what?")
#         return
#
#     say_data = {"message": message}
#     say = self.emit("before:say", say_data)
#     if say.blocked:
#         return
#
#     self.echo("{{MYou say {{x'{{m{}{{x'".format(message))
#     self.act("{M{self.name} says {x'{m{message}{M{x'", {
#         "message": message,
#     })
#
#     self.emit("after:say", say_data, unblockable=True)
#
# -- from class Actor, this method:
#     def act(self, template, data=None, exclude=None):
#         Actors, Characters = self.game.get_injectors("Actors", "Characters")
#         if data is None:
#             data = {}
#
#         data["self"] = self
#
#         message = template
#
#         for collection in (Characters, Actors):
#             for actor in collection.query({"room_id": self.room_id}):
#                 if actor == self or actor == exclude:
#                     continue
#
#                 if "{message}" in message:
#                     message = message.replace("{message}", data["message"])
#                 if "{self.name}" in message:
#                     message = message.replace("{self.name}", data["self"].name)
#
#                 actor.echo(message)
#
#
# """
