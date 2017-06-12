"""
CORE MODULE
"""
from datetime import datetime
import hashlib
import json
import math
import random
from glob import glob
from utils.ansi import Ansi
from mud.collection import FileCollection, Collection, Entity
from utils.collection import Index
from mud.module import Module
from mud.manager import Manager
from mud.map import Map
from utils.listify import listify
from utils.event import Event
from utils.columnify import columnify
from mud.command_resolver import CommandResolver
import logging
from settings import DIRECTIONS, CHANNELS, SOCIALS, IDLE_TIME_TO_DISCONNECT, \
    RACES, CLASSES, GENDERS, MAX_LEVEL


MAP_META = [
    "#=building",
    "#=city",
    "P=field",
    "F=forest",
    "H=hills",
    "M=mountain",
    "W=swim",
    "W=noswim",
    "X=unused",
    "%=air",
    "D=desert",
    "+=road",
    "i=inn",
    "s=shop",
    "t=temple",
    "g=guild",
    "S=swamp",
    "J=jungle",
    "#=dungeon",
    "G=garden",
    "C=cavern",
    "+=cityst",
    "+=asport",
    "H=ashangar",
    "H=phome",
    "H=phangar",
    "D=dock",
    "B=bridge",
    "+=dirtpath",
    "B=bttlfld",
    "F=factory",
    "J=junkyard",
    "L=emptylot",
    "U=underwtr",
    "@=YOU  |,-=normal path  |,-=door |,-=one way  |,-=secret  |,-=non-linear"
]


def description_command(self, arguments):
    """Set and view your own description."""

    def output_desc():
        self.echo("Your description is:")
        for line in desc:
            self.echo(line)

    desc = self.get_description()

    if not arguments:
        output_desc()
        return

    # Append to the description
    if arguments[0] == "+":
        arguments = arguments[1:]
        line = " ".join(arguments)
        desc.append(line)

    # Remove from the description
    elif arguments[0] == "-":
        if not desc:
            self.echo("You don't have any description lines to remove.")
            return

        desc.pop()

    # Remove the entire description
    elif arguments[0] == "clear":
        desc = []

    # Set the description to a line
    else:
        line = " ".join(arguments)
        desc = [line]

    self.set_description(desc)
    self.save()
    output_desc()


def advance_command(self, arguments, Characters):
    if len(arguments) < 2:
        self.echo("Advance who to what level?")
        return False

    game = self.get_game()
    name = arguments[0]
    game
    level = int(arguments[1])
    actor = Characters.find({"name": name})

    if actor.get_level() > level:
        self.echo("Sorry, can't delevel a player.")
        return False

    actor.set_level(level)
    actor.save()


def flee_command(self):
    """Run away from Combat."""

    if not self.is_fighting():
        self.echo("You aren't fighting anyone.")
        return False

    # Pick a random exit
    room = self.get_room()
    exits = room.get_exits()
    random_exit = random.choice(exits)

    fleeing = self.event_to_room("fleeing")
    if fleeing.is_blocked():
        self.echo("You try to run, but your path is blocked!")
        return False

    walk_command(self, random_exit.direction_id, fleeing=True)

    new_room = self.get_room()
    if new_room != room:
        self.leave_combat()
        self.act("[actor.name] has fled!")
        self.event_to_room("fled")

    self.save()


def afk_command(self):
    if self.is_afk():
        self.remove_flag("afk")
        self.echo("You are no longer marked as AFK.")
    else:
        self.add_flag("afk")
        self.echo("You are now marked as AFK.")
    self.save()


def map_command(self):
    room = self.get_room()
    area = room.get_area()
    area_name = area.name if area else "Unknown"
    mapped = Map.generate_from_room(room, width=64, height=33)
    map_lines = mapped.format_lines()
    meta_width = 15

    self.echo("{}'s Map of {}".format(self.name, area_name).center(80))

    for row in range(35):
        meta = MAP_META[row].ljust(meta_width) if row < len(MAP_META) \
            else (" " * meta_width)
        map_line = map_lines[row] if row < len(map_lines) else ""
        self.echo(meta + " " + map_line)


def recall_command(self):
    """Move Actor to the stating Room."""
    self.echo("You pray for transportation!")
    self.act("[actor.name] prays for transportation!")

    if not self.can_recall():
        return self.echo("You cannot recall from this room.")

    self.echo("You disappear in a flash!")
    self.act("[actor.name] disappears in a flash!")

    self.recall()
    self.save()

    self.echo("You appear suddenly in a new place..")
    self.act("[actor.name] appears suddenly!")

    self.handle_command("look")


def prompt_command(self, arguments):
    """Set the prompt for an Actor."""
    if not arguments:
        self.prompt_enabled = not self.prompt_enabled
        return

    self.prompt = " ".join(arguments)
    self.echo("Your prompt has been set to: {}".format(self.prompt))
    self.save()


def force_command(self, arguments):
    if not arguments:
        self.echo("Force who do to what?")
        return

    if len(arguments) == 1:
        self.echo("Force them to do what?")
        return

    target_name = arguments[0]
    commands = " ".join(arguments[1:])

    target = self.find_room_actor(target_name)
    if not target:
        self.echo("You can't find them.")
        return

    # TODO Check permissions/power
    self.echo("You force %s{x to: %s" % (target.name, commands))
    target.handle_command(commands)


def score_command(self):
    """Display the Player's Character scoresheet."""
    lines = []
    lines.append("{GName{g: {x%s %s" % (self.name, self.get("title", "")))

    lines.append("{GDesc{g:{x %s %s %s %s %s {GLevel{g: {x%d {GAge{g:{x %d" % (
        "True", "Neutral", "Male", "Heucuva", "Priest", 101, 306
    ))

    lines.append("{GHP{g:{x%d{g/{x%d {g({c%d{g) {GMana{g:{x%d{g/{x%d {g"
                 "({c%d{g) {GMove{g:{x%d{g/{x%d {g({c%d{g) {GSaves{g:{x%d" % (
                     8206, 8206, 2794, 11092, 11092, 10132, 1248, 1248,
                     998, -66))

    lines.append("{g------------+-----------------------+---------------{x")
    lines.append("{GStr{g: {x%d{g({x%d{g) {g| {GItems{g:     {x%d{g/{x%d     "
                 "{g| {GHitroll{g: {x%d" % (
                    25, 25, 25, 125, 255))
    lines.append("{GInt{g: {x%s{g({x%s{g) | {GWeight{g:    {x%s{g/ {x%s     "
                 "{g| {GDamroll{g: {x%s" % (25, 25, 20, 72, 285))
    lines.append("{GWis{g: {x%s{g({x%s{g) +----------------+------+-----------"
                 "----" % (25, 25))
    lines.append("{GDex{g: {x%s{g({x%s{g) | {GPractices{g:  {x%s {g| {GArena "
                 "Wins{g:     {x%s" % (25, 25, 10, 0))
    lines.append("{GCon{g: {x%s{g({x%s{g) | {GTrains{g:     {x%s {g| {GArena "
                 "Losses{g:   {x%s" % (25, 25, 10, 0))
    lines.append("{g------------+---------+------+----------------------")
    lines.append("{GCoins Platinum{g:    {x%s {g| {GExperience" % (10))
    lines.append("      {GGold{g:        {x%s {g|  {GCurrent{g: {x%s" % (
        10, 10000000
    ))
    lines.append("      {GSilver{g:      {x%s {g| {GAdventure Points{g: "
                 "{x%s" % (10, 100))
    lines.append("{g----------------------+-----------------------------")
    lines.append("{GArmor Pierce{g:  {x%d [%s{x]" % (123, "super armored"))
    lines.append("      {GBash{g:    {x%d [%s{x]" % (123, "super armored"))
    lines.append("      {GSlash{g:   {x%d [%s{x]" % (123, "super armored"))
    lines.append("      {GMagic{g:   {x%d [%s{x]" % (123, "super armored"))
    lines.append("{g----------------+-------------+---------------------")
    lines.append("{GAlignment{g:   {x%d {g| {GWimpy{g:    {x%d {g| {GQuest "
                 "Points{g: {x%d" % (49, 0, 1984))

    lines.append("{g----------------+-------------+---------------------{x")
    lines.append("{GPkStatus{g: {x%s{x" % ("PK"))
    lines.append("{g----------------------------------------------------{x")

    output = "\n".join(lines)
    self.echo(output)


def scrollify(lines, header=""):
    output = """\
  __________________________________________________________________________
 /\\_\\                                                                     \\_\\
|/\\\\_\\""" + header.center(69)+ """\\_\\
\\_/_|_|                                                                     |_|
"""
    for line in lines:
        output += "    |_| " + line.center(67, " ") + " |_|"
    output += """
 ___|_|                                                                     |_|
/ \\ |_|                                                                     |_|
|\\//_/                                                                     /_/
 \\/_/_____________________________________________________________________/_/
"""
    return output


def wizlist_command(self, Characters):
    """List the Immortals."""
    names = [char.name for char in Characters.query() if char.is_immortal()]
    self.echo(scrollify(names, header="Gods and Rulers Of Waterdeep"))


def default_receive_check(a, t):
    return True


def channel_command(self, message, Characters):
    """Echo a Channel to the Game."""
    parts = message.split(" ")
    channel_name = parts.pop(0)
    message = " ".join(parts)

    if not message:
        self.echo("Channel toggling is not yet supported.")
        return

    channel = None
    for channel_id, entry in CHANNELS.items():
        if channel_id.startswith(channel_name):
            channel = entry
            break

    template = channel.get("format", "")
    for char in Characters.query({"online": True}):
        receive_check = channel.get("receive_check", default_receive_check)
        if self == char:
            continue
        if receive_check(self, char):
            char.echo(template.format(actor=self, message=message))

    self_template = channel.get("self_format", template)
    self.echo(self_template.format(actor=self, message=message))


def social_command(self, message):
    """Handle an Actor performing a social emote."""
    parts = message.split(" ")
    social_name = parts.pop(0)

    target = None
    if parts:
        # TODO Figure out target
        pass

    social = None
    for social_id, entry in SOCIALS.items():
        if social_id.startswith(social_name):
            social = entry
            break

    if target is None:
        self.gecho(social["me_to_room"].format(me=self))
        self.gecho(social["actor_to_room"].format(actor=self))
        return

    if target == self:
        self.gecho(social["me_to_self"].format(me=self))
        self.gecho(social["actor_to_self"].format(actor=self))
        return

    self.gecho(social["me_to_target"].format(me=self, target=target))
    self.gecho(social["actor_to_target"].format(actor=self, target=target))
    self.gecho(social["actor_to_me"].format(actor=self, me=target))


def walk_command(self, message, fleeing=False):
    """Walk in a direction."""
    arguments = message.split(" ")

    if not arguments:
        self.echo("Walk where?")
        return False

    direction = None
    for direction_id, entry in DIRECTIONS.items():
        if direction_id.startswith(arguments[0]):
            direction = entry
            break

    if direction is None:
        self.echo("You can't walk in that direction.")
        return False

    from_room = self.get_room()
    exit = from_room.get_exit(direction_id)

    if exit is None:
        self.echo("You can't walk in that direction.")
        return False

    to_room = exit.get_room()

    data = {"fleeing": fleeing}
    for event_id in ["walking", "leaving", "entering"]:
        event = self.event_to_room(
            event_id, data, room=from_room, blockable=True)
        if event.is_blocked():
            return False

    self.act("[actor.name] leaves [direction_id].", {
        "direction_id": direction_id
    })

    if to_room is None:
        raise Exception("Room does not exist for exit {} in room {}".format(
            direction_id,
            to_room.id
        ))

    self.set_room(to_room)

    self.save()

    self.handle_command("look")

    self.act("[actor.name] has arrived.")

    for event_id in ["walked", "left", "entered"]:
        self.event_to_room(event_id, room=to_room)


def sockets_command(self):
    """List the socket Connections."""
    game = self.get_game()
    connections = game.get_connections()
    self.echo("[Port  Num Connected_State Login@ Idle] Player Name Host")
    self.echo("-" * 79)
    count = 0
    now = datetime.now()

    for conn in connections:
        count += 1
        state = "handshaking"
        actor_name = "UNKNOWN"
        client = conn.get_client()
        age = now - conn.get_last_input_date()
        minutes = math.floor(age.seconds / 60)

        if client:
            state = client.state
            actor = client.get_actor()
            if actor:
                actor_name = actor.name

        self.echo("[%3d %15s %7s %3d] %s %s (%s) %s" % (
            count,
            state,
            "00:00XX",
            minutes,
            actor_name,
            conn.hostname,
            conn.ip,
            conn.TYPE
        ))

    self.echo()
    self.echo("%d users" % count)


def exception_command(self):
    """Raise an Exception."""
    raise Exception("Testing exception")


def title_command(self, arguments):
    if not arguments:
        self.echo("Change your title to what?")
        return

    if arguments[0] == "clear":
        self.title = ""
        self.echo("Your title has been cleared.")
    else:
        self.title = " ".join(arguments)
        self.echo("Your title has been set to: %s{x" % self.title)

    self.save()


def get_actor_sort_values(actor):
    """Provide values, which are always sorted descending."""
    return (
        1 if actor.is_immortal() else 0,
        actor.get_level()
    )


def who_command(self, arguments, Characters):
    """Display a list of which Characters are online."""
    total_count = 0
    visible_count = 0
    top_count = 999

    self.echo((" " * 15) + "{GThe Visible Mortals and Immortals of Waterdeep")
    self.echo("{g" + ("-" * 79))

    actors = list(Characters.query({"online": True}))
    actors = sorted(actors, key=get_actor_sort_values, reverse=True)

    for actor in actors:
        total_count += 1

        if not self.can_see(actor):
            continue

        visible_count += 1

        line = ""

        level_restring = actor.get("who_level_restring", None)
        if level_restring:
            line += level_restring + "{x"
        else:
            if actor.is_immortal():
                line += "{RIMM{x"
            elif actor.is_max_level():
                line += "{GHRO{x"
            else:
                line += "{x%s{x" % (str(actor.get_level()).rjust(3))

        line += " "

        who_restring = actor.get("who_restring", None)
        if who_restring:
            line += who_restring
        else:
            gender_restring = actor.get("who_gender_restring", None)
            line += gender_restring if gender_restring else \
                GENDERS[actor.gender_id]["who_name"]

            line += " "

            race_restring = actor.get("who_race_restring", None)
            line += race_restring if race_restring else \
                RACES[actor.race_id]["who_name"]

            line += " "

            class_restring = actor.get("who_class_restring", None)
            line += class_restring if class_restring else \
                CLASSES[actor.class_id]["who_name"]

            line += " "

            clan_restring = actor.get("who_clan_restring", None)
            if clan_restring:
                line += clan_restring
            else:
                clan = actor.get_organization("clan")
                if not clan or clan.is_hidden():
                    line += " " * 5
                else:
                    line += Ansi.pad_right(clan.who_name, 5)

        line += " "

        flag_restring = actor.get("who_flags_restring", None)
        if flag_restring:
            line += "{x[%s{x]" % flag_restring
        else:
            line += ("{x[...{BN{x......]{x" if actor.is_immortal()
                     else "  {x[.{BN{x......]{x")
        line += " "

        if actor.is_afk():
            line += "[{yAFK{x] "

        prefix = actor.get("prefix", None)
        if prefix:
            line += prefix + " "

        line += actor.name

        if actor.title:
            if actor.title[0] not in ",.":
                line += " "
            line += ("{x%s{x" % actor.title) if actor.title else ""

        faction = actor.get_organization("faction")
        if faction:
            line += " {x[%s{x|%s{x]" % ("{RL", faction.who_name)

        for bracket in actor.get("who_brackets", []):
            line += (" {x[%s{x]" % bracket)

        self.echo(line)

    self.echo()
    self.echo(("{GPlayers found{g: {x%s   " % visible_count) +
              ("{GTotal online{g: {W%s   " % total_count) +
              ("{GMost on today{g: {x%s" % top_count))


def swear_command(self, arguments):
    self.echo("Testing swear filter: fuck Fuck FUCK fUcK fuCK? !!Fuck!!")


LOOK_ACTOR_FLAGS = (
    ("y", "V", "invisible"),
    ("8", "H", "hiding"),
    ("c", "C", "charmed"),
    ("b", "T", "pass_door"),
    ("w", "P", "faerie_fire"),
    ("C", "I", "iceshield"),
    ("r", "I", "fireshield"),
    ("B", "L", "shockshield"),
    ("R", "E", "evil"),
    ("Y", "G", "good"),
    ("W", "S", "sanctuary"),
    ("G", "Q", "immortal_quest"),
)


def exits_command(self):
    """List the exits from the current Room."""
    from settings import DIRECTIONS

    room = self.get_room()
    exits = room.get_exits()

    self.echo("Obvious exits:")
    if not exits:
        self.echo("None.")
        return

    for exit in exits:
        next_room = exit.get_room()
        self.echo("%s - %s" % (
            DIRECTIONS[exit.direction_id]["name"],
            next_room.name
        ))


def finger_command(self, arguments, Characters):
    """Look up a Character who may be offline."""
    from modules.core import Character
    if not arguments:
        self.echo("Finger who?")
        return

    name = Character.clean_name(arguments[0])
    actor = Characters.find({"name": name})
    if not actor:
        self.echo("No such player: {}".format(name))
        return

    gender = GENDERS[actor.gender_id]["who_name"]

    lines = []
    lines.append("{B+{b-----------------------{C[ {BWa{bt{8e{wr{8d{be{Bep{RM{rUD {RCharacter Info {C]{b-----------------------{B+{x")
    lines.append(" {RN{rame %s{x   : %s %s{x" % (gender, actor.name, actor.get("title", "")))

    description = actor.get("description", [])
    if description:
        lines.append("{B+{b-------------------------------{B| {CDE{wSC{cRIP{wTI{CON {B|{b-------------------------------{B+{x")

        for line in description:
            lines.append(line)

    lines.append("{B+{b-----------------------------------------------------------------------------{B+{x")
    lines.append(" %s's login status is currently unknown." % (actor.name))
    lines.append("{B+{b-----------------------------------------------------------------------------{B+{x")

    self.echo("\n".join(lines))


def kill_command(self, arguments, Characters, Actors):
    """Attack an Actor within the Room."""
    if not arguments:
        self.echo("Attack who?")
        return

    # FIXME support multiple arguments and querying
    target = self.find_room_actor(arguments[0])

    if not target:
        self.echo("You can't find them.")
        return

    if target == self:
        self.echo("Suicide is a mortal sin.")
        return

    attacking = self.event_to_room("attacking", {"target": target})

    if attacking.is_blocked():
        return

    self.attack(target)

    self.event_to_room("attacked", {"target": target})

    self.save()
    target.save()

    self.perform_combat_round_attacks()


def look_command(self, arguments, Characters, Actors, Objects):
    minimap_enabled = True
    from settings import SELF_KEYWORDS

    def format_actor_flags(actor):
        flag_found = False
        flags = ""
        for color, symbol, flag_id in LOOK_ACTOR_FLAGS:
            if not actor.has_flag(flag_id):
                symbol = "."
            else:
                flag_found = True
            flags += "{%s%s" % (color, symbol)

        if flag_found:
            return "{x[%s{x] " % flags
        return ""

    def format_actor(actor):
        return "%s%s is here{x" % (
            format_actor_flags(actor),
            actor.format_name_to(self)
        )

    def format_object(obj):
        return "%s is lying here." % obj.name

    room = self.get_room()

    def look_at_actor(target):
        for index, line in enumerate(target.get("description", [
            "You see nothing special about %s." % target.name
        ])):
            self.echo(("{C" + line) if index == 0 else line)
        self.echo("{x%s{x {Ris in excellent condition.{x" % (
            target.name
        ))

    if arguments:
        keyword = arguments[0]

        if keyword in SELF_KEYWORDS:
            look_at_actor(self)
            return

        # TODO Look at objects too
        # TODO support multiple arguments and positionals
        target = self.find_room_actor(keyword)
        if target:
            look_at_actor(target)
        else:
            self.echo("You don't see that here.")

        return

    lines = []
    name_line = "{B%s{x " % room.name

    # TODO Remove this, it's for debugging only
    name_line += "(%s:%s/%s) " % (room.area_vnum, room.vnum, room.id)

    if room.has_flag("safe"):
        name_line += "{R[{WSAFE{R]{x "

    if room.has_flag("noloot"):
        name_line += "{R[{WNOLOOT{R]{x "

    if room.has_flag("law"):
        name_line += "{w[{WLAW{w]{x "

    lines.append(name_line)

    description = room.get_description()
    for index, line in enumerate(description):
        if index == 0:
            lines.append("{x  " + line)
        else:
            lines.append(line)

    lines.append("")

    basic_exits = []
    door_exits = []
    secret_exits = []

    for direction_id, direction in DIRECTIONS.items():
        exit = room.get_exit(direction_id)
        if not exit:
            continue

        if exit.is_door() and exit.is_closed():
            if exit.is_secret():
                secret_exits.append(direction["name"])
            else:
                door_exits.append(direction["name"])

        else:
            basic_exits.append(direction["name"])

    line = ""
    line += "{x[{GExits{g:{x %s{x]" % (
        " ".join(basic_exits) if basic_exits else "none"
    )
    line += "   "
    line += "{x[{GDoors{g:{x %s{x]" % (
        " ".join(door_exits) if door_exits else "none"
    )

    if self.is_immortal():
        line += "   "
        line += "{x[{GSecret{g:{x %s{x]" % (
            " ".join(secret_exits) if secret_exits else "none"
        )

    lines.append(line)

    players = Characters.query({"online": True, "room_id": room.id})
    for player in players:
        if player == self:
            continue
        lines.append(format_actor(player))

    actors = Actors.query({"room_id": room.id})
    for actor in actors:
        lines.append(format_actor(actor))

    objects = Objects.query({"room_id": room.id})
    for obj in objects:
        lines.append(format_object(obj))

    # Prefix with map, if applicable
    minimap_height = 9
    minimap_width = 16
    minimap_gutter = 2
    if minimap_enabled:
        minimap = Map.generate_from_room(room, width=minimap_width,
                                         height=minimap_height)
        minimap_lines = minimap.format_lines()

        for x in range(minimap_height - len(lines)):
            lines.append("")

        for index, line in enumerate(lines):
            newline = ""
            newline += minimap_lines[index] if index < minimap_height else \
                (" " * minimap_width)
            newline += " " * minimap_gutter
            newline += line

            lines[index] = newline

    for line in lines:
        self.echo(line)


def quit_command(self, arguments):
    self.echo("""
{RYou feel a hand grab you, you begin to fly upwards!
{BYou pass through the clouds and out of the world!
{GYou have rejoined Reality!

{WFor {RNews{W, {CRoleplaying{W and {MInfo{W, Visit our website!
{Ch{cttp://{Cw{cww.{Cw{caterdeep.{Co{crg{x""")
    client = self.get_client()
    if not client:
        return
    client.quit()


def me_command(self, arguments):
    message = " ".join(arguments)
    self.gecho(message, emote=True)


def random_range(bottom, top):
    return random.randint(bottom, top)


class RoomEntity(Entity):
    def say(self, message):
        self.handle_command("say " + message)

    def handle_event(self, event):
        """Handle the Event being passed to it and return it."""
        all_subroutines = self.get("subroutines", {})
        subroutines_for_event = all_subroutines.get(event.type, [])
        for index, subroutine in enumerate(subroutines_for_event):
            filename = "{}:{}:{}".format(self.id, event.type, index)
            compiled = compile(subroutine, filename, "exec")
            target = event.data["source"]
            # self_proxy = self.get_subroutine_proxy()
            # target_proxy = event.data["source"].get_subroutine_proxy()

            variables = {
                "random": random_range,
                "self": self,
                "target": target,
                "event": event
            }
            exec(compiled, variables, variables)
            if event.is_blocked():
                return event

        return event

    def set_room(self, room):
        """Set the Room for the RoomEntity."""
        self.room_id = room.id

    def event_to_room(self, type, data=None, room=None, blockable=True):
        """Pass an Event to be handled by the Room and return it."""
        if data is None:
            data = {}

        data["source"] = self

        if room is None:
            room = self.get_room()

        event = Event(type, data, blockable=blockable)

        return room.handle_event(event)

    def logout(self):
        self.online = False

    def login(self):
        self.online = True
        self.check_integrity()

    def get_experience(self):
        """Return the current amount of experience the Actor has."""
        return self.experience

    def get_experience_per_level(self):
        """Return the amount of experience the Actor needs per level."""
        return self.experience_per_level

    def get_level_experience_remaining(self):
        """Return the amount of experience the Actor needs to reach level."""
        return self.experience_per_level - self.experience

    def gain_experience(self, amount):
        """Apply an experience gain to the Actor."""
        self.experience += amount
        while self.experience >= self.experience_per_level:
            self.gain_level()
            self.experience -= amount

    def set_level(self, level):
        diff = level - self.level
        for x in range(diff):
            self.gain_level()

    def gain_level(self):
        self.level += 1
        self.level = min(MAX_LEVEL, self.level)
        self.echo("You have gained a level!  You are now level {}!".format(
            self.level))
        self.echo("Your stats have improved: X hp, Y mana, Z training points!")

    def is_max_level(self):
        """Return if the Actor is at max level."""
        return self.level == MAX_LEVEL

    def get_level(self):
        """Return the Actor's level."""
        return min(MAX_LEVEL, self.level)

    def check_integrity(self):
        room = self.get_room()
        self.room_id = room.id

        # FIXME do not leave in
        # FIXME do not leave in
        self.set_stat_base('hp', 9000)
        self.set_stat_base('current_hp', 9000)
        self.set_stat_base('mana', 9000)
        self.set_stat_base('current_mana', 9000)
        self.experience = 0
        self.experience_per_level = 3000
        self.level = 1
        # FIXME do not leave in
        # FIXME do not leave in

    def get_room(self):
        """Return the Room that the RoomEntity is in."""
        from settings import DEFAULT_ROOM_VNUM
        area_vnum, room_vnum = DEFAULT_ROOM_VNUM.split(":")

        Rooms = self.get_injector("Rooms")

        room = Rooms.find(self.room_id)

        if not room:
            room = Rooms.find({"area_vnum": area_vnum, "vnum": room_vnum})

            if not room:
                raise Exception(
                    "RoomEntity {} fallback room {} cannot be found.".format(
                        self.id,
                        DEFAULT_ROOM_VNUM))

        return room

    def get_flags(self):
        """Return list of flags."""
        return self.get("flags", [])

    def has_flag(self, flag_id):
        """Return whether the flag is present."""
        return flag_id in self.get_flags()

    def add_flag(self, flag_id):
        if not self.flags:
            self.flags = []

        if flag_id not in self.flags:
            self.flags.append(flag_id)

    def remove_flag(self, flag_id):
        if not self.flags:
            self.flags = []

        if flag_id in self.flags:
            self.flags.remove(flag_id)


class Area(Entity):
    def handle_event(self, event):
        game = self.get_game()
        event = game.handle_event(event)

        return event


class Areas(FileCollection):
    WRAPPER_CLASS = Area

    NAME = "areas"
    INDEXES = [
        Index("id", required=True, unique=True),
        Index("name"),
    ]

    def deserialize(self, contents):
        """Extract the Rooms and attach to game."""
        game = self.get_game()
        Rooms = game.get_injector("Rooms")

        area = super(Areas, self).deserialize(contents)
        rooms = area.get("rooms", [])

        for room in rooms:
            Rooms.save(room)

        return area


class RoomExit(Entity):
    def __init__(self, data, room, parent_room):
        super(RoomExit, self).__init__(data)
        self._room = room
        self._parent_room = parent_room

    def get_room(self):
        """Return the Room."""
        return self._room

    def get_flags(self):
        """Return list of flags."""
        return self.get("flags", [])

    def has_flag(self, flag_id):
        """Return whether the flag is present."""
        return flag_id in self.get_flags()

    def is_door(self):
        """Return whether exit is a door or not."""
        return self.has_flag("door")

    def is_secret(self):
        """Return whether exit is a secret exit or not."""
        return self.has_flag("secret")

    def is_closed(self):
        """Return whether exit is closed or not."""
        return self.has_flag("closed")

    def is_open(self):
        """Return whether exit is open or not."""
        return not self.is_closed()


class Room(Entity):
    def has_flag(self, flag):
        """Return Whether the Room has a flag or not."""
        flags = self.get("flags", [])
        return flag in flags

    def query_actors(self):
        """Generate the list of Characters/Actors."""
        Characters, Actors = self.get_injectors("Characters", "Actors")
        for char in Characters.query_by_room(self.id):
            yield char

        for actor in Actors.query_by_room(self.id):
            yield actor

    def get_area(self):
        Areas = self.get_injector("Areas")
        return Areas.find(self.area_id)

    def handle_event(self, event):
        """Pass the Event to the Room occupants and return it."""
        Actors, Objects = self.get_injectors(
            "Actors", "Objects")

        # TODO Add "SAFE" room flag to prevent
        if event.type == "attacking" and self.has_flag("safe"):
            actor = event.data["source"]
            actor.echo("You can't do that here.")
            event.block()
            return event

        for actor in Actors.query({"room_id": self.id}):
            event = actor.handle_event(event)
            if event.is_blocked():
                return event

        for obj in Objects.query({"room_id": self.id}):
            event = obj.handle_event(event)
            if event.is_blocked():
                return event

        area = self.get_area()
        event = area.handle_event(event)

        return event

    def get_exits(self):
        """Return dict of exits."""
        exits = []
        for direction_id in self.get("exits", {}):
            exits.append(self.get_exit(direction_id))
        return exits

    def get_exit(self, direction_id):
        """Return a RoomExit."""
        Rooms = self.get_injector("Rooms")

        exits = self.get("exits", {})
        raw_exit = exits.get(direction_id, None)
        if not raw_exit:
            return None

        raw_exit["direction_id"] = direction_id

        room_id = raw_exit.get("room_id", None)
        if not room_id:
            logging.error("Room {} {} exit does not exist".format(
                self.vnum, direction_id))

        exit_room = Rooms.get(room_id)
        return RoomExit(raw_exit, exit_room, self)

    def get_description(self):
        """Return the list of description lines."""
        return self.get("description", [])


class Rooms(Collection):
    WRAPPER_CLASS = Room

    NAME = "rooms"
    INDEXES = [
        Index("id", required=True, unique=True),
        Index("vnum", required=True, unique=True),
        Index("name"),
        Index("area_vnum", required=True),
        Index("area_id"),
    ]


class Organization(Entity):
    def is_hidden(self):
        return self.hidden is True



COMMAND_RESOLVER = CommandResolver()

COMMANDS = {
    "description": description_command,
    "look": look_command,
    "flee": flee_command,
    "kill": kill_command,
    "exits": exits_command,
    "finger": finger_command,
    "afk": afk_command,
    "map": map_command,
    "recall": recall_command,
    "quit": quit_command,
    "me": me_command,
    "swear": swear_command,
    "title": title_command,
    "exception": exception_command,
    "sockets": sockets_command,
    "who": who_command,
    "walk": walk_command,
    "wizlist": wizlist_command,
    "score": score_command,
    "force": force_command,
    "prompt": prompt_command,
    "advance": advance_command,
}


for direction_id in DIRECTIONS.keys():
    COMMANDS[direction_id] = walk_command

for channel_id in CHANNELS.keys():
    COMMANDS[channel_id] = channel_command

for social_id in SOCIALS.keys():
    COMMANDS[social_id] = social_command


def commands_command(self):
    """List out the available commands."""
    # TODO add checks to filter out available commands
    lines = columnify(COMMANDS.keys(), return_lines=True)
    for line in lines:
        self.echo(line)


COMMANDS['commands'] = commands_command


COMMAND_RESOLVER.update(COMMANDS)


class Object(RoomEntity):
    def get_description(self):
        """Return the list of description lines."""
        return self.description or []

    def set_description(self, description):
        """Set the list of description lines."""
        self.description = description or []

    def format_received_act_message(self, message, data=None):
        """Return a replaced out message."""

        if data is None:
            data = {}

        for key, value in data.items():
            pattern = "[%s]" % key

            if pattern in message:
                if callable(value):
                    value = value(self)
                message = message.replace(pattern, value)

        return message

    def act_to(self, target, *args, **kwargs):
        kwargs["include"] = [target]
        return self.act(*args, **kwargs)

    def act(self, message, data=None, target=None, exclude=None, include=None):
        if data is None:
            data = {}

        if exclude is None:
            exclude = [self]

        if include:
            included_actors = include
        else:
            room = self.get_room()
            included_actors = room.query_actors()

        for actor in included_actors:
            if actor in exclude:
                continue

            data["actor.name"] = self.format_name_to
            if target:
                data["target.name"] = target.format_name_to

            message = actor.format_received_act_message(message, data)
            actor.echo(message)


class Actor(Object):
    # TODO move commands and handlers/logic out into their own places
    ONE_CHAR_ALIASES = {
        "'": "say",
        "/": "recall",
        "=": "cgossip",
        "?": "help",
    }

    def can_recall(self):
        """Return whether the Actor can recall home or not."""
        # TODO implement this
        room = self.get_room()
        return not (room.area_vnum == "westbridge" and room.vnum == "3001")

    def recall(self, silent=False):
        from settings import DEFAULT_ROOM_VNUM
        Rooms = self.get_injector("Rooms")

        area_vnum, room_vnum = DEFAULT_ROOM_VNUM.split(":")

        room = Rooms.find({"area_vnum": area_vnum, "vnum": room_vnum})

        self.set_room(room)

    def get_stats(self):
        """Return the dict of stats."""
        return self.get("stats", {})

    def get_stat_base(self, stat_id):
        """Return the base value of a stat."""
        return self.get_stat(stat_id).get("base", 0)

    def set_stat(self, stat_id, stat):
        """Set the value of a base stat."""
        stats = self.get_stats()
        stats[stat_id] = stat
        self.stats = stats

    def set_stat_base(self, stat_id, value):
        """Set the value of a base stat."""
        stat = self.get_stat(stat_id)
        stat["base"] = value
        self.set_stat(stat_id, stat)

    def get_stat_bonus(self, stat_id):
        """Return the bonus value of a stat."""
        return self.get_stat(stat_id).get("bonus", 0)

    def get_stat(self, stat_id):
        """Return the detailed object of a stat."""
        return self.get_stats().get(stat_id, {})

    def get_stat_total(self, stat_id):
        """Return the detailed object of a stat."""
        stat = self.get_stat(stat_id)
        return stat.get("base", 0) + stat.get("bonus", 0)

    def perform_combat_round_attacks(self):
        """Handle a combat round for this Actor."""
        targets = self.get_targets()

        if not targets:
            return

        room = self.get_room()

        target = targets.pop(0)
        for _ in range(8):

            # Target died, or moved away somehow
            target_room = target.get_room()
            if target.is_dead() or target_room != room:
                target.save()

                if not targets:
                    break
                target = targets.pop(0)

            amount = random.randint(100, 300)
            self.echo("{BYour punch {r*{R*{r* {bDE{BV{wASTA{BT{bES {r*{R*{r* {B%s{B! -{R={C%d{R={B-{x" % (target.format_name_to(self), amount))
            self.act("{c[actor.name]'s punch {r*{R*{r* {bDE{BV{wASTA{BT{bES {r*{R*{r* {c[target.name]{c! {B-{R={C%d{R={B-{x" % (amount), target=target, exclude=[self, target])
            self.act_to(target, "{c[actor.name]'s punch {r*{R*{r* {bDE{BV{wASTA{BT{bES {r*{R*{r* {cyou! -{R={C%d{R={B-{x" % (amount))
            target.receive_damage(amount, self)
            target.save()

    def receive_damage(self, amount, attacker):
        """Handle receiving damage."""
        hp = self.get_stat_base('current_hp')
        new_hp = hp - amount

        if new_hp <= 0:
            self.set_stat_base('current_hp', 0)
            self.die(attacker)
        else:
            self.set_stat_base('current_hp', new_hp)

    def is_dead(self):
        """Return whether you are dead or not."""
        self.get_stat_base('current_hp') <= 0

    def leave_combat(self):
        for target in self.get_targets():
            target.remove_combat_target(self)
            self.remove_combat_target(target)

    def die(self, killer):
        """Handle death."""
        dying = self.event_to_room("dying")

        # If dying is blocked, and the Actor is not dead, kick out
        if dying.is_blocked() and not self.is_dead():
            return

        self.leave_combat()

        self.act("[actor.name] has been killed!")
        self.echo("You have been killed!")
        self.gecho("*** %s has been killed by %s" % (self.name, killer.name))
        self.recall(silent=True)

        # FIXME do not leave here
        self.set_stat_base("current_hp", 100)
        killer.gain_experience(3000)
        # FIXME do not leave here

        self.event_to_room("died", blockable=False)

    def attack(self, target):
        """Initiate combat with a target."""
        self.add_combat_target(target)
        if not target.is_fighting(self):
            target.attack(self)

    def add_combat_target(self, target):
        self.targets = self.get("targets", [])

        if target.id not in self.targets:
            self.targets.append(target.id)

    def remove_combat_target(self, target):
        self.targets = self.get("targets", [])

        target_id = target.id
        if target_id in self.targets:
            self.targets.remove(target_id)

    def get_targets(self):
        """Return a list of Actors."""
        Actors, Characters = self.get_injectors("Actors", "Characters")

        outputs = []

        for target_id in self.get_target_ids():
            actor = Actors.find(target_id) or Characters.find(target_id)
            outputs.append(actor)

        return outputs

    def get_target_ids(self):
        return self.get("targets", [])

    def is_fighting(self, target=None):
        """Return whether the Actor is fighting."""

        target_ids = self.get_target_ids()

        if target is not None:
            return target.id in target_ids

        return len(target_ids) > 0

    def is_race(self, race_id):
        """Return whether Actors is of Race provided."""
        return self.race_id == race_id

    def is_online(self):
        return True

    def is_afk(self):
        return self.has_flag("afk")

    def find_room_actor(self, keywords, can_see=True):
        room = self.get_room()
        Actors, Characters = self.get_injectors("Actors", "Characters")
        targets = [
            Characters.query({"room_id": room.id, "online": True}),
            Actors.query({"room_id": room.id}),
        ]
        for actors in targets:
            for actor in actors:
                if can_see and not self.can_see(actor):
                    continue

                if not actor.matches_keywords(keywords):
                    continue

                return actor

    def matches_keywords(self, keywords):
        return self.keywords.startswith(keywords)

    def get_organization(self, type_id):
        """Return the Organization of a type."""
        from settings import ORGANIZATIONS

        organization_id = self.get_organization_id(type_id)

        if not organization_id:
            return None

        org = ORGANIZATIONS.get(organization_id, None)
        if not org:
            return None

        return Organization(org)

    def get_organization_id(self, type_id):
        """Return the Organization ID that matches the requested type."""
        return self.get_organization_ids().get(type_id, None)

    def get_organization_ids(self):
        """Return the key/value pairs of Organizations."""
        return self.get("organizations", {})

    def can_see(self, target):
        """Return whether this Actor can see target Entity."""
        return True

    def is_visible_to(self, target):
        """Return whether this Actor is visible to the target Entity."""
        return target.can_see(self)

    def format_name_to(self, target):
        """Format the name of an Actor to another target, taking visibility
           into account."""
        if target.can_see(self):
            return self.name
        return "Someone"

    def set_client(self, client):
        self._client = client

    def get_client(self):
        if self._client:
            return self._client

        connection = self._game.get_actor_connection(self)
        if not connection:
            return None

        client = connection.client
        if client is None:
            return

        return client

    def echo(self, message=""):
        client = self.get_client()
        if not client:
            return
        client.writeln(message)

    def gecho(self, message, exclude=None):
        exclude = listify(exclude)

        game = self.get_game()
        connections = game.get_connections()
        for conn in connections:
            client = conn.get_client()
            actor = client.get_actor()

            if actor is None:
                continue

            if actor in exclude:
                continue

            actor.echo(message)

    def get_aliases(self):
        return {}

    def get_game(self):
        return self._game

    def quit(self):
        client = self.get_client()
        client.quit()

    def handle_command(self, message, ignore_aliases=False):
        message = message.rstrip()

        if not message:
            return

        if not ignore_aliases:
            # Handle a one-character alias prefix
            possible_aliases = "".join(self.ONE_CHAR_ALIASES.keys())
            if message[0] in possible_aliases:
                existing = message
                message = self.ONE_CHAR_ALIASES[existing[0]]
                if existing[1:]:
                    message += " " + existing[1:]

            # Handle player aliases
            aliases = self.get_aliases()
            parts = message.split(" ")
            if parts[0] in aliases:
                parts = aliases[parts[0]].split(" ") + parts[1:]

        command = parts.pop(0).lower()
        arguments = tuple(parts)
        named_arguments = {}

        handlers = COMMAND_RESOLVER.get(command)
        # TODO Add secondary resolution checks: level, access, etc.
        handler = handlers[0] if handlers else None

        # Execute the appropriate code
        if handler is None:
            self.echo("Huh?")
            return

        game = self.get_game()
        try:
            game.inject(
                handler,
                _self=self,
                arguments=arguments,
                message=message,
                **named_arguments
            )
        except Exception as e:
            game.handle_exception(e)
            self.echo("Huh?!  (Code bug detected and reported.)")


class Objects(Collection):
    WRAPPER_CLASS = Object

    NAME = "objects"
    INDEXES = [
        Index("id", required=True, unique=True),
        Index("name", required=True, unique=True),
        Index("room_id"),
    ]


class Actors(Collection):
    WRAPPER_CLASS = Actor

    NAME = "actors"
    INDEXES = [
        Index("id", required=True, unique=True),
        Index("name", required=True, unique=True),
        Index("room_id"),
        Index("fighting"),
    ]

    def query_by_room(self, room, spec=None):
        """Generate Actors in a Room."""
        if spec is None:
            spec = {}

        if isinstance(room, str):
            room_id = room
        else:
            room_id = room.id

        spec["room_id"] = room_id

        for actor in self.query(spec):
            yield actor


class Character(Actor):
    def is_online(self):
        return self.online is True

    @classmethod
    def clean_name(cls, name):
        """Return a cleaned version of a name string."""
        return name.strip().lower().title()

    def matches_keywords(self, keywords):
        return self.name.lower().startswith(keywords)

    def is_immortal(self):
        return self.has_flag("immortal")

    @classmethod
    def generate_password(self, password):
        """Return a SHA256 hashed password with appropriate salting."""
        cleaned = password.strip()
        from settings import PASSWORD_SALT_PREFIX, PASSWORD_SALT_SUFFIX
        salted = PASSWORD_SALT_PREFIX + cleaned + PASSWORD_SALT_SUFFIX
        return hashlib.sha256(salted.encode("utf-8")).hexdigest()

    def password_is(self, password):
        """Return whether the password matches this Character's or not."""
        return self.password == self.generate_password(password)


class Characters(Actors):
    WRAPPER_CLASS = Character

    NAME = "characters"

    INDEXES = Actors.INDEXES + [
        Index("online"),
        Index("fighting"),
    ]

    def query_by_room(self, room):
        """Generate Actors in a Room."""
        for char in super(Characters, self).query_by_room(
                room, {"online": True}):

            yield char


class Entities(Collection):
    pass


class EntityManager(Manager):
    INJECTOR_NAME = None
    DATA_PATH = None

    def start(self):
        Entities = self.game.get_injector(self.INJECTOR_NAME)
        for path in glob(self.DATA_PATH + "/*"):
            data = json.loads(open(path).read())
            Entities.save(data)


class CharactersManager(EntityManager):
    INJECTOR_NAME = "Characters"
    DATA_PATH = "data/characters"


class IdleManager(Manager):
    def tick(self):
        now = datetime.now()
        max_age = IDLE_TIME_TO_DISCONNECT

        for conn in self.game.get_connections():
            age = (now - conn.get_last_input_date()).seconds
            if age > max_age:
                message = "You are being disconnected for being idle."
                actor = conn.get_actor()
                if actor:
                    actor.echo(message)
                    actor.handle_command("quit")
                else:
                    conn.writeln(message)
                    conn.destroy()


class CombatManager(Manager):
    def init(self):
        self.ticks = 0

    def handle_event(self, event):
        if event.type == "walking":
            fleeing = event.data.get("fleeing", False)
            actor = event.data.get("source", None)
            if actor.is_fighting() and not fleeing:
                actor.echo("No way!  You are still fighting!")
                event.block()

        return event

    def tick(self, Characters):
        # FIXME use constants for this
        self.ticks += 1

        if self.ticks % 5 == 0:
            for character in Characters.query():
                character.perform_combat_round_attacks()


class Core(Module):
    MODULE_NAME = "Core"
    VERSION = "0.1.0"

    INJECTORS = {
        "Rooms": Rooms,
        "Objects": Objects,
        "Actors": Actors,
        "Characters": Characters,
        "Areas": Areas,
    }

    MANAGERS = [
        CharactersManager,
        IdleManager,
        CombatManager,
    ]
