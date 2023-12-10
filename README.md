# Turntabler
_how the turns have tabled_
## Prewords
This repository provides source code to use an Arduino Uno, a 28BYJ-48 Stepper Motor and a ULN2803 driver board to power an IKEA SNUDDA turntable. 
3D-Printable 'adapters' can be found on printables, i used [this one](https://www.printables.com/model/499102-ikea-snudda-motorized-turntable-with-arduino).

## Repository
The repository contains source code for both the desktop app and the arduino stepper driver. 
```
    |- /config-app/             <-- contains the desktop app, written in python
    |- /arduino-stepper/        <-- contains the stepper source, written in arduino
```

## Arduino Stepper Driver
The Stepper driver can operate in a pan-tilt mode, where it runs a configurable amount of steps forwards, afterwards the same amount of steps backwards.
It can run in continous-mode in both directions. 

Additionally, the Stepper Driver can:
- Adjust the steppers speed (lower number - less delay - more speed)
- Store its settings for tilting/paning in the EEPROM to run headless

To achieve a non-blocking motor driver, i integrated a stepper driver based on a main loop polling algorithm. With the default stepper.h library, the communication hung up several times. 

### Arduino API
Connect to the arduino via Serial, baudrate 115200. 
Commands:
| Command | Comment | Arguments |
| ------- | ------- | --------- |
| r       | Start (continously running)| _None_ |
| s       | Stop    | _None_ |
| c       | Direction |  1 = clockwise, 2 = counterclockwise |
| t       | pan/tilt mode | 1-65536 (steps to pan/tilt) |
| v       | speed | 1-100 (lower = higher speed) |
| b       | burn settings to eeprom | _None_ |
| e       | erase settings from eeprom | _None_ |

To send a command, put it in a console and send it with a ending newline ``\nl``. Commands with arguments must be sent commandArgument without any space in between (ie. ``c1`` => direction, clockwise)


## config-app
For convenience, the apps frontend is partly german. The whole source code and variable naming is in english, translation can be done easily. 
![Config App Screenshot](/assets/config-app.png)

To connect to the arduino board, select the corresponding comport (refresh if app was running before arduino is connected) and Open the port by clicken the 'Open port' button. 

To enable the infinite pan/tilt mode, enter the number of steps that should be paned and start with 'Los'.
After enabling tilt, it is possible to change the speed and to burn the image to the eeprom. 

To enable infinite run, select if the turntable runs clockwise/counter-clockwise via the checkbox (not populated per default != counter-clockwise per default) and press 'Starten'. 

To stop any action, press the 'Stoppen' button. 

Burn Settings stores the current mode and speed to the eeprom, the arduino board will load those settings and start after connecting to power. 
To disable that behavior, Erase the Settings by pressing the corresponding button. 

In the bottom all transmitted and received messages from/to the arduino are logged. 

## Backlog
1. Implement a 'bouce'-delay (delay turning of the direction after reaching end position in pan/tilt mode)