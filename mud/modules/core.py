from mud import module, manager, entity, collection, inject


async def quit_command(self, **kwargs):
    self.echo("""\
{RYou feel a hand grab you, you begin to fly upwards!
{BYou pass through the clouds and out of the world!
{GYou have rejoined Reality!

{WFor {RNews{W, {CRoleplaying{W and {MInfo{W, Visit our website!
{Ch{cttp://{Cw{cww.{Cw{caterdeep.{Co{crg{x""")
    self.quit()


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

COMMAND_HANDLERS = {
    "who": who_command,
    "tell": tell_command,
    "quit": quit_command,
}

class Character(entity.Entity):
    @property
    def game(self):
        return self.client.server.game

    @property
    def emit(self, *args, **kwargs):
        return self.game.emit

    def set_client(self, client):
        self.client = client

    def quit(self):
        self.client.close()

    def echo(self, message=""):
        self.client.writeln(message)

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
            await func(
                self=self,
                line=line,

                keyword=keyword,
                remainder=remainder,

                words=words,

                args=args,
                params=params,
            )




class Characters(collection.Collection):
    ENTITY_CLASS = Character


class Core(module.Module):
    def setup(self):
        self.register_injector("Characters", self.inject_characters)
        self.register_injector("Character", self.inject_character)

    @classmethod
    def inject_characters(cls, game):
        if "characters" not in game.data:
            game.data["characters"] = {}
        return Characters(game.data["characters"])

    @classmethod
    def inject_character(cls, game):
        return Character
