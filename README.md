# Undermountain Python MUD Engine

A modular MUD platform for flexibly creating worlds, written in Python.

## Features
* Telnet Server
* WebSocket Server
* Module System for Extensibility


## Installation
1. Install Python3

    See: https://www.python.org/downloads/

    At this time, Python 2.7.X may still work, but with our target being
    Python3, there may be conflicts that will not be resolved unless they
    affect the newest versions of the Python3 interpreter.

2. Download the code from this repository

    ```
    git clone https://github.com/gvanderest/undermountain.git
    ```

3. Create a virtual environment (recommended)
    If you wish to create a sandbox that prevents the Undermountain engine
    from being affected by the rest of the system, it can be created via
    the virtual environment system.

    ```
    virtualenv -p python3 venv
    source venv/bin/activate
    ```

5. Install any dependencies
    Using the built-in Python package manager `pip` you are able to read the
    list of dependencies from a file and install them.

    ```
    pip install -r requirements.txt
    ```

## Interacting with the Engine

### Activate the virtual environment (see above)

If you are using one, you will need to activate it each time you wish to start
the engine.

    source venv/bin/activate

### Starting the Engine
Get the game running and able to accept players.

    ./um start

### Backup Data (Not Yet Implemented)
You can either manually make a copy of the `data` folder yourself, but if you
prefer to have the scripts handle it:

    ./um backup <identifier>

If an identifier is not provided, one will be generated for you.


### Listing Backups (Not Yet Implemented)
Essentially the same as listing the files in the `backups` folder, but via an
internal command.  This may filter out only valid-looking backup files.


### Restoring Data (Not Yet Implemented)
You can restore data by providing a partial backups filename (must be present
in the `backups` folder) or the direct path to a file.

    ./um restore <identifier or path>

If a filename matching both a direct path and `backups` folder are found, the
direct path will win.


# Engine Documentation

## Subroutines

In the Undermountain game engine, most things fire Events which can be hooked
into by Entities (Actors, Rooms, Objects, etc.) to react with scripts.  These
scripts are written in Python3, but some support for OLC Mobprogs may exist
for a period of time until the game is fully ported over from ROT.

Most events will come in pairs, typically with a pre-event that is blockable
by the script, and a post-event that is not blockable.

### Example Subroutine

Just as an early example of a subroutine, we might attach the following
"entered" script to a goblin standing in the room.

    if random_number(0, 10) > 5:  # 50% chance of ..

        self.say("I kill you!", language="goblin")  # .. saying this message
        self.attack(target)  # .. and attacking

### Creating Subroutines

TBD

### Attaching Subroutines to Entities

TBD

### Event Types

This area will detail the types of events that can fire, when to expect them,
ability to be blocked, and example data that should be available with them.
Events that are blockable will be noted.


#### acting (blockable) -> acted

TBD


#### attacking (blockable) -> attacked

TBD


#### casting (blockable) -> cast
> param {Actor} target - The target that is casting.

> param {Ability} ability - The skill or spell being used.

TBD


#### despawning

TBD - When an Entity is going to be removed from the Game.

Note: This cannot be blocked.


#### drinking (blockable) -> drank

TBD


#### dying (blockable) -> died
> param {Actor} target - The target that is dying.

When an Actor's health is reduced to zero, or they are outright killed by
some other means, the *dying* event will fire in the Room where the
death is occurring.

If an Actor is not saved from *dying*, they will fire a *died* event in the
Room that they respawn in (often their recall).

Note: If *dying* is blocked, the Actor's "current_hp" stat must be changed
to a positive value in order for it to truly be blocked.  This may be
automatically enforced in the future.


#### eating (blockable) -> ate

TBD


#### inputting (blockable) -> inputted

TBD - Handle raw input of a player
Might be renamed to commanding, commanded?


#### killing (blockable) -> killed

TBD


#### messaging (blockable) -> messaged

TBD - Channel messages.


#### respawning (blockable) -> respawned

TBD - This is what happens when an area resets or regenerates from inactivity.


#### skilling (blockable) -> skill

See: casting -> cast


#### spawned

TBD - When Entity is created

Note: This cannot be blocked.


#### walking (blockable) -> walked
> param {Actor} target - The target that is walking or walked.

> param {Direction} direction - The direction that the target walked or
> entered from.

When an Actor is trying to walk out of a Room, this will fire in the Room that
the *walking* was initiated in.

When an Actor arrives in the Room, this will will fire in the Room that the
*walked* arrives in.

See: leaving -> left, entering -> entered


### Methods Available

In addition to the basic functionality that Python provides, there are various
helper functions that are made available to you in subroutines.

#### random_number
