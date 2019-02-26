from mud import module, manager, entity, collection, inject
from mud.utils import listify


SOCIALS = {
    "grin": {
        "me_to_room": "You grin.",
        "actor_to_room": "{actor.name} grins.",

        "me_to_target": "You grin at {target.name}.",
        "actor_to_me": "{actor.name} grins at you.",
        "actor_to_target": "{actor.name} grins at {target.name}.",

        "me_to_me": "You grin to yourself",
        "actor_to_self": "{actor.name} grins to {actor.himself}.",
    },
}


@inject("Characters")
async def sockets_command(self, Characters, **kwargs):
    self.echo("[Num Connected_State Login@ Idl] Player Name Host")
    self.echo("--------------------------------------------------------------------------")

    count = 0

    for actor in Characters.query():
        count += 1

        client = actor.client
        self.echo(str((
            client.id,
            client.state,
            client.created_date,
            0,
            actor.name,
            client.host,
        )))

    self.echo()
    self.echo(f"{count} users")


async def quit_command(self, **kwargs):
    self.echo("""\
{RYou feel a hand grab you, you begin to fly upwards!
{BYou pass through the clouds and out of the world!
{GYou have rejoined Reality!

{WFor {RNews{W, {CRoleplaying{W and {MInfo{W, Visit our website!
{Ch{cttp://{Cw{cww.{Cw{caterdeep.{Co{crg{x""")
    self.quit()


async def look_command(self, **kwargs):
    self.echo("""\
{BThe Temple of Life
{x  This is the interior of a large white marble temple.  A pipe organ
plays in the background as people sing a hymn of peacefulness.  A
priest up front tells the story of the forces of the realms, be it Life,
the force that gives breath and a heartbeat, and Death, the force that
steals these gifts away.  There is a guard standing watch, keeping the
peace.  To the south is the Temple Square and to the west is the donation
room.  To the east is the {RCity Morgue{x and a newer section of Main Street
heads off to the north.

[Exits: north east south west]   [Doors: none]   [Secret: none]
{x( 2) {8A bed of black roses magically grow here.
{x[.......{BL{x....] Hollywood Hogan is here, looking out for Sting.""")


@inject("Characters")
async def tell_command(self, keyword, args, Characters, **kwargs):
    # TODO: Convert to using params
    # TODO: Convert to find Actors using clean method
    # TODO: Fuzzy search
    if len(args) < 2:
        self.echo("Tell who what?")
        return

    name = args.pop(0)
    message = " ".join(args)

    target = Characters.find({"name__istartswith": name})

    event = self.emit("global:whisper", {
        "target": target,
        "message": message,
    })

    if event.blocked:
        return

    if not target:
        self.echo("They couldn't be found.")
    else:
        self.echo(f"{{gYou tell {target.name} '{{G{message}{{g'{{x")
        if target != self:
            target.echo(f"{{g{self.name} tells you '{{G{message}{{g'{{x")


@inject("Characters")
async def who_command(self, Characters, **kwargs):
    # TODO: Add functionality to use filters
    # TODO: Cleanly request online Characters
    count = 0
    self.echo("""\
               {GThe Visible Mortals and Immortals of Waterdeep
{g-----------------------------------------------------------------------------{x""")

    for actor in Characters.query():
        line = f"{{x  1 {{BM {{CH{{cuman {{MN{{mov      {{w[.{{BN{{w......] {{x{actor.name}"
        self.echo(line)

    self.echo()
    self.echo(f"{{GPlayers found{{g: {{w{count}   {{GTotal online{{g: {{W{count}   {{GMost on today{{g: {{w{count}{{x")


async def exception_command(self, **kwargs):
    raise Exception("Test.")


@inject("Characters")
async def social_command(self, keyword, args, Characters, **kwargs):
    # TODO: Only look for people in this room.
    social = SOCIALS[keyword]

    if not args:
        self.act_to(self, social["me_to_room"])
        self.act(social["actor_to_room"])
        return

    target_name = args.pop(0)
    target = Characters.find({"name__istartswith": target_name})

    if not target:
        self.echo("You can't find them.")
        return

    if target == self:
        self.act_to(self, social["me_to_me"])
        self.act(social["actor_to_self"])
    else:
        self.act_to(self, social["me_to_target"])
        self.act_to(target, social["actor_to_me"])
        self.act(social["actor_to_target"], exclude=target)


async def emote_command(self, remainder, **kwargs):
    self.act_to(self, "{c{actor.name} " + remainder + "{x")
    self.act("{c{actor.name} " + remainder + "{x", replace_name=True)


BASIC_COMMANDS = {
    "who": who_command,
    "tell": tell_command,
    "quit": quit_command,
    "look": look_command,
    "sockets": sockets_command,
    "exception": exception_command,
    "emote": emote_command,
    "pmote": emote_command,
}

COMMAND_HANDLERS = {}
COMMAND_HANDLERS.update(BASIC_COMMANDS)
COMMAND_HANDLERS.update({name: social_command for name in SOCIALS})

class Actor(entity.Entity):
    @property
    def game(self):
        return self.client.server.game

    @property
    def emit(self, *args, **kwargs):
        return self.game.emit

    def echo(self, message="", newline=True):
        getattr(self.client, "writeln" if newline else "write")(message)

    @inject("Characters")
    def act(self, message, exclude=None, replace_name=False, Characters=None):
        for actor in Characters.query():
            if actor == self or actor == exclude:
                continue

            self.act_to(actor, message, replace_name=replace_name)

    def act_to(self, target, message, replace_name=False):
        # TODO: Make this use lambdas to improve performance.
        replaces = {
            "actor.name": self.name,
            "actor.himself": "himself",
            "actor.herself": "himself",
            "actor.itself": "himself",

            "target.name": target.name,
            "target.himself": "himself",
            "target.herself": "himself",
            "target.itself": "himself",
        }

        output = message

        for (key, value) in replaces.items():
            output = output.replace(f"{{{key}}}", value)

        # TODO: Capitalize the first letter if it's the start of the line
        if replace_name:
            output = output.replace(target.name, "you")

        target.echo(output)


class Character(Actor):
    def set_client(self, client):
        self.client = client

    def quit(self):
        self.client.close()

    def echo_prompt(self):
        self.echo()
        self.echo(f"{{8[{{R1{{8/{{r1{{8h {{B1{{8/{{b1{{8m {{M1{{8v {{W{self.name}{{8({{Y1484{{8) {{WBaths{{8({{w0{{8/{{w12{{Bam{{8) {{W22{{8]{{x ", newline=False)

    async def force(self, commands):
        await self.handle_input(commands)

    async def handle_input(self, line):
        words = line.split(" ")
        keyword = words[0] if words else ""

        func = COMMAND_HANDLERS.get(keyword)

        args = words[1:] if words else []
        remainder = " ".join(args)

        params = [] # TODO: Parse indexes, counts, keywords, etc.

        if not func:
            self.echo("Huh?")
        else:
            try:
                await func(
                    self=self,
                    line=line,

                    keyword=keyword,
                    remainder=remainder,

                    words=words,

                    args=args,
                    params=params,
                )
            except Exception as e:
                self.game.handle_exception(e)
                self.echo("Huh?!")

        self.echo_prompt()


class Characters(collection.Collection):
    ENTITY_CLASS = Character


class Wiznet(module.Module):
    def setup(self):
        self.bind("global:exception", self.handle_exception)
        self.bind("global:input", self.handle_input)

    def wiznet(self, category, message):
        for conn in self.game.connections:
            conn.writeln(f"{{Y--> {{W{category}{{w: {message}{{x")

    def handle_exception(self, event):
        self.wiznet("exception", event.data["traceback"])

    def handle_input(self, event):
        line = event.data["line"]
        name = event.data["name"] or "Unknown"
        host = event.data["host"] or "Unknown Host"

        self.wiznet("input", f"{name}({host}): {line}")


class Core(module.Module):
    def setup(self):
        self.register_injector("Characters", self.inject_characters)
        self.register_injector("Character", self.inject_character)
        self.register_module(Wiznet)

    @classmethod
    def inject_characters(cls, game):
        if "characters" not in game.data:
            game.data["characters"] = {}
        return Characters(game.data["characters"])

    @classmethod
    def inject_character(cls, game):
        return Character
