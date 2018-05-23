# Commands

## What is a Command?

Commands are simple functions that are provided with a few different types of parameters, which can be used to help simplify the information the player is providing.

When a player types input into the game, the Client will attempt to figure out what they intended to do.  It does this using a "FuzzyResolver" which looks for commands that start with what the player is requesting, and continue down the list until they either find something, or fail-- meaning there was no command to run.

This is where you will commonly see the output of "Huh?"


## How do I write a Command?

Writing a command is easy enough, with the first argument `self` being similar to what you'd see in Object Oriented Programming.  `self` will be the Actor or Entity that issued the command, so you have full access to the world through it.

```python
from mud.module import Module


def simple_command(self, name, message, **kwargs):
    """A simple command, which echoes back to the player what they typed.

    :param message: the message they typed after the command
    :return: a float, denoting how many seconds to delay after running
    """
    self.echo("You ran the command '{}' with string '{}' after it.".format(
        name, message))


class SimpleModule(Module):
    """Just a simple module to get started."""
    def setup(self):
        self.game.add_command("simple", simple_command)
```

Save the above file to `modules/simple.py`, add `modules.simple.SimpleModule` to your `settings.py` file `MODULES` section, and voila.. the next time you start the game you have a command called `simple` available to you.


## What else is provided to a Command?

If you look at the function definition, you'll see that there is a `**kwargs` argument, which catches all the extra data provided to the Command handler function.  This is because the Client provides the function with a few extra pieces of information, which we'll outline here.

### name (str)
The name of the command that was typed.  In the above example, this will be the word `simple`; but in some other cases, you may want many keywords to go to the same command, and perform logic based on the name typed.

### message (str)
The raw line of text you provided after the command.

### args (tuple<str>)
A tuple of the strings that were provided in the message, split by their whitespace.

### params (tuple<dict>)
A tuple of dictionaries that make up the translated arguments, which can be used for querying data from the game.  Whether it be killing the second evil goblin in the room, or buying ten health potions, this is the query language of our game.

For example, if you typed:
```text
buy 10*2.'health potion'
```

You'd get a tuple that looks like:
```python
(
    {
        "param_index": 0,  # the index of parameter in the tuple
        "keywords": "health potion",  # keywords to filter by
        "position": 2,  # which instance of the filtered list
        "quantity": 10,  # how many, typically only applies to buying/selling
    },
)
```
