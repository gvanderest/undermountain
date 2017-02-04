# Undermountain Python MUD Engine

A modular MUD platform for flexibly creating worlds, written in Python.

## Features

### Completed
* Telnet Server

### In Progress
* Account System
* Channel Communication System
* Module System for Extensibility
* Flat-File Database Collections for Areas, Rooms, Actors, Objects, etc.
* Organizations (Clans, Factions, etc.)
* Scripting Engine for Areas, Rooms, Actors, Objects, etc.
* Combat in PVE and PVP forms
* Maps and Mapping
* Import from ROT - Waterdeep Specific at this time
* Equipment Slot and Weaponry
* Races
* Classes
* Genders
* Skills and Spells
* Character Creation
* Rerolling
* In-Depth Equipment Stat System
* Vehicles and Mounts
* Pets
* Levelling
* Shops

### Future Features
* Food and Drink with Effects
* Pills and Potions with Effects
* Staves and Wands and Scrolls with Effects
* Henchmen
* Multi-Classing Support
* Specialization Support
* WebSocket Server
* Seasonal Reset Systems
* Leaderboards for Time-Trials, Arena Victories, Player-Killing, etc.
* Random (Endless?) Dungeon Generators
* Player Housing
* Tradeskills
* Crafting System
* Raiding / Claiming / Encounter systems
* Instancing of Areas for Groups
* PVP Battlegrounds and Arenas
* Forum and Discussion System
* Global Effects and Buffs
* Support Ticket Submission System
* API Integrations
* Random (Bandit?) Encounters
* Pet Battles
* Minigame Support
* DDOS Protection
* Immortal Punishment and Control Systems
* Justice System
* Questing System
* Achievement System and Brackets
* Building Tools
* Auctioning and Marketplace System
* Forget System
* Friends System
* Grouping System
* Heal- and Damage-Over-Time Effects
* Global Roleplay Integrations
* Organization Builder Commands
* Clan Commands
* Mortal Administrator System
* Mail System
* Banking
* Garrison-Like Quests
* Detect Enemies-like Skills for Minimap
* Tutorial Area for "Adventurer" type of class
* Tracking of failed login attempts


## Installation
1. Install Python3

    See: https://www.python.org/downloads/

    At this time, Python 2.7.X may still work, but with our target being
    Python3, there may be conflicts that will not be resolved unless they
    affect the newest versions of the Python3 interpreter.

2. Download the code from this repository
        git clone git@bitbucket.org:wdmud/undermountain.git

3. Create a virtual environment (recommended)
    If you wish to create a sandbox that prevents the Undermountain engine
    from being affected by the rest of the system, it can be created via
    the virtual environment system.

        python3 -m venv venv
        source venv/bin/activate

5. Install any dependencies
    Using the built-in Python package manager `pip` you are able to read the
    list of dependencies from a file and install them.

        pip install -r requirements.txt

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
