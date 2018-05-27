# Undermountain Python MUD Engine

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

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
    brew install python3 virtualenv  # on mac
    virtualenv -p python3 venv
    source venv/bin/activate
    ```

5. Install any dependencies
    Using the built-in Python package manager `pip` you are able to read the
    list of dependencies from a file and install them.

    ```
    pip install -r requirements.txt
    ```

6. Restore from the example backup
    Run the undermountain restore script to load the example backup file.

    ```
    ./um restore example
    ```

## Interacting with the Engine

### Activate the virtual environment (see above)

If you are using one, you will need to activate it each time you wish to start
the engine.

    source venv/bin/activate

### Starting the Engine
Get the game running and able to accept players.

    ./um start

### Backup Data
You can either manually make a copy of the `data` folder yourself, but if you
prefer to have the scripts handle it:

    ./um backup <identifier>

If an identifier is not provided, one will be generated for you.


### Listing Backups (Not Yet Implemented)
Essentially the same as listing the files in the `backups` folder, but via an
internal command.  This may filter out only valid-looking backup files.


### Restoring Data
You can restore data by providing a partial backups filename (must be present
in the `backups` folder) or the direct path to a file.

    ./um restore <identifier or path>

If a filename matching both a direct path and `backups` folder are found, the
direct path will win.


## Developing the Engine

In addition to the basic installation steps, you'll want to also add

```shell
pip install -r dev-requirements.txt
```

And set up the pre-commit hooks for git.

```shell
pre-commit install
```

# Engine Concepts

### Modules

### Injectors

#### Collections

### Managers

### Clients

* Settings File
* Clients
* Modules
    * Events
