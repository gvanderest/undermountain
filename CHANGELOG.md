# CHANGELOG

## VERSION 0.2.0 (fight-club) - 2017-06-12T22:53:48

* Basics of a Combat system
* Added basic "kill" command which is spammable to do damage to a target
* Added basic health regeneration every 5 seconds (out of combat)
* Added basic death logic and announcement to game
* Basic experience gain per kill (see kill command above) and levelling
* Toying with "cinematic" feature experiment, you can test this by dying
* Loaded areas/rooms from Waterdeep ROT datafiles into JSON format
* Minimapping on room descriptions (will be configurable)
* Full map via "map" command
* Ability to flee from combat
* Swear filtering protection (will be configurable)
* Basic design of organization membership
* Exception handling on command input
* Some basic enter/exit subroutines (see Tchazzar at recall)
* Ablity to recall back to start (will be improved later)
* Public channels for discussion (ooc, cgossip, say, hero, bitch, ask, answer, etc.)
* Listing "who" is online and setting of title


## VERSION 0.1.0 (genesis) - 2017-04-01T17:44:49

* Module system for grouping services/features
* Managers for modules that handle areas of the game
* Injector system for modules to allow access to to collections/logic services
* Event system for handling things like "walking" and "walked", with ability to block certain events
* Creation of a subroutine system to attach to all game Entities
