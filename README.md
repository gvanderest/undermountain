# Undermountain Python MUD Engine

## Installation

1. Install Python 3
2. Download the code from this repository
    git clone git@bitbucket.org:wdmud/undermountain.git

3. Create a virtual environment
    python3 -m venv venv

## Interacting with the Engine

This will always require that you load up the virtual environment.
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
