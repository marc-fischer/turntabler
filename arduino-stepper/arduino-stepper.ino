// #include "Stepper.h"
#include <EEPROM.h>

int steps_per_turn = 2048;
int speed = 3;
int direction = 1; // 1 = clockwise, -1 = counter-clockwise
int turns = 0;
int turns_counter = 0;
int loops = 0;        // 0 = stop after emptying the turns conter, 1 = loop, meaning turn around and step back if turns are 0, 2 = run forever
int bounce_delay = 0; // configurable bounce delay on a direction change of the tilt mode

#define EEPROM_ADDR_SPEED 0
#define EEPROM_ADDR_TURNS EEPROM_ADDR_SPEED + 10
#define EEPROM_ADDR_LOOPS EEPROM_ADDR_TURNS + 10
#define EEPROM_ADDR_DIRECTION EEPROM_ADDR_LOOPS + 10
#define EEPROM_ADDR_BURNED EEPROM_ADDR_DIRECTION + 10
#define EEPROM_ADDR_BOUNCE_DELAY EEPROM_ADDR_BURNED + 10

int stepperPin[4] = {A0, A2, A1, A3};
// int stepDelay = 10;

// Stepper myStepper = Stepper(steps_per_turn, A0, A2, A1, A3); // do not use, blocks the serial communication and whole system hangs

// #define STATUS_MESSAGE // uncomment to add a status message every 1s

double next_send = 0;
double next_step = 0;

void burn_settings_to_eeprom(void)
{
  // save loops, direction and turns to the EEPROM to autostart if configured
  EEPROM.write(EEPROM_ADDR_SPEED, speed);
  EEPROM.write(EEPROM_ADDR_TURNS, turns);
  EEPROM.write(EEPROM_ADDR_LOOPS, loops);
  EEPROM.write(EEPROM_ADDR_DIRECTION, direction);
  EEPROM.write(EEPROM_ADDR_BOUNCE_DELAY, bounce_delay);
  EEPROM.write(EEPROM_ADDR_BURNED, true);
}

void format_eeprom(void)
{
  EEPROM.write(EEPROM_ADDR_SPEED, 0);
  EEPROM.write(EEPROM_ADDR_TURNS, 0);
  EEPROM.write(EEPROM_ADDR_LOOPS, 0);
  EEPROM.write(EEPROM_ADDR_DIRECTION, 0);
  EEPROM.write(EEPROM_ADDR_BOUNCE_DELAY, 0);
  EEPROM.write(EEPROM_ADDR_BURNED, false);
}

void read_settings_from_eeprom(void)
{
  if (EEPROM.read(EEPROM_ADDR_BURNED) == true)
  {
    Serial.println("Settings in EEPROM found, starting over");
    speed = EEPROM.read(EEPROM_ADDR_SPEED);
    turns = EEPROM.read(EEPROM_ADDR_TURNS);
    loops = EEPROM.read(EEPROM_ADDR_LOOPS);
    direction = EEPROM.read(EEPROM_ADDR_DIRECTION);
    bounce_delay = EEPROM.read(EEPROM_ADDR_BOUNCE_DELAY);
    send_status_message();
  }
  else
  {
    Serial.println("EEPROM not configured to autostart. Send Config and burn EEPROM to autostart");
  }
}

void send_status_message(void)
{
  Serial.println("-----  Current State  -----");
  Serial.print("Speed: ");
  Serial.println(speed);
  Serial.print("Direction: ");
  Serial.println(direction);
  Serial.print("Bounce Delay: ");
  Serial.println(bounce_delay);
  Serial.print("Turns: ");
  Serial.println(turns);
  Serial.print("Turns Counter: ");
  Serial.println(turns_counter);
  Serial.print("Loops: ");
  Serial.println(loops);
}

void stepper_init(void)
{
  // myStepper.setSpeed(speed);
  pinMode(stepperPin[0], OUTPUT);
  pinMode(stepperPin[1], OUTPUT);
  pinMode(stepperPin[2], OUTPUT);
  pinMode(stepperPin[3], OUTPUT);
  Serial.println("Init Stepper");
}

int step_pattern_step = 0;
void step(void)
{
  switch (step_pattern_step)
  {
  case 0:
    digitalWrite(stepperPin[0], HIGH);
    digitalWrite(stepperPin[1], LOW);
    digitalWrite(stepperPin[2], HIGH);
    digitalWrite(stepperPin[3], LOW);
    break;
  case 1:
    digitalWrite(stepperPin[0], LOW);
    digitalWrite(stepperPin[1], HIGH);
    digitalWrite(stepperPin[2], HIGH);
    digitalWrite(stepperPin[3], LOW);
    break;
  case 2:
    digitalWrite(stepperPin[0], LOW);
    digitalWrite(stepperPin[1], HIGH);
    digitalWrite(stepperPin[2], LOW);
    digitalWrite(stepperPin[3], HIGH);
    break;
  case 3:
    digitalWrite(stepperPin[0], HIGH);
    digitalWrite(stepperPin[1], LOW);
    digitalWrite(stepperPin[2], LOW);
    digitalWrite(stepperPin[3], HIGH);
    break;
  }
  step_pattern_step = step_pattern_step + 1 * direction; // +1 on clockwise, -1 on counter-clockwise
  if (step_pattern_step > 3)
  {
    step_pattern_step = 0;
  }
  if (step_pattern_step < 0)
  {
    step_pattern_step = 3;
  }
}

void stepper_stop(void)
{
  digitalWrite(stepperPin[0], HIGH);
  digitalWrite(stepperPin[1], HIGH);
  digitalWrite(stepperPin[2], HIGH);
  digitalWrite(stepperPin[3], HIGH);
  step_pattern_step = 0;
}

int steps_per_turn_counter = 0;
int bounce_delay_counter = 0;

void stepper_task(void)
{
  // Serial.println("Stepper Task");
  if (bounce_delay_counter <= 0)
  {
    if (turns_counter > 0)
    {

      if (steps_per_turn_counter > 0)
      {
        step();
        steps_per_turn_counter--;
      }
      if (steps_per_turn_counter % steps_per_turn == 0)
      {
        turns_counter--;
      }
    }
    if (turns_counter <= 0)
    {

      if (loops == 1)
      {                        // loop (tilt) mode
        turns_counter = turns; // reset turns to the tilt steps
        steps_per_turn_counter = turns_counter * steps_per_turn;
        stepper_stop();
        if (direction == 1)
        { // invert direction
          direction = -1;
        }
        else
        {
          direction = 1;
        }
        bounce_delay_counter = bounce_delay;
      }
      if (loops == 2)
      { // run forever mode
        turns_counter = 2;
        steps_per_turn_counter = turns_counter * steps_per_turn;
      }
      if (loops == 0)
      {
        stepper_stop();
        steps_per_turn_counter = 0;
      }
    }
  }
  else

  {
    //Serial.print("Operation Delayed for: ");
    //Serial.print(bounce_delay_counter);
    //Serial.println("s");
    bounce_delay_counter--;
  }
}

void setup()
{
  // Start serial communication at 9600 bps
  Serial.begin(115200);
  stepper_init();
  read_settings_from_eeprom();
}

void loop()
{
  // Check if data is available to read from serial
  if (Serial.available() > 0)
  {
    // Read the incoming data
    String incomingData = Serial.readString();

    // Print the received data to the serial monitor
    Serial.print("Received: ");
    Serial.println(incomingData);

    // parse the input, split to command and payload
    String command = incomingData.substring(0, 1);
    int payload = 0;

    if (incomingData.length() > 1)
    {
      String pl = incomingData.substring(1);
      payload = pl.toInt();
    }

    if (command.equalsIgnoreCase("r"))
    {
      Serial.println("Start command received");
      turns_counter = 2;
      loops = 2;
    }
    else if (command.equalsIgnoreCase("s"))
    {
      Serial.println("Stop command received");
      turns_counter = 0;
      loops = 0;
    }
    else if (command.equalsIgnoreCase("c"))
    {
      Serial.println("Direction command received");
      if (payload == 0)
      {
        Serial.println("Direction: Counter-Clockwise");
        direction = -1;
      }
      if (payload == 1)
      {
        Serial.println("Direction: Clockwise");
        direction = 1;
      }
    }
    else if (command.equalsIgnoreCase("t"))
    {
      Serial.println("Steps command received");
      Serial.print("Steps: ");
      Serial.println(payload);
      turns = payload;
      turns_counter = payload;
      loops = 1;
    }
    else if (command.equalsIgnoreCase("v"))
    {
      Serial.println("Speed command received");
      Serial.print("Speed setting: ");
      Serial.println(payload);
      speed = payload;
      // stepper_init();
    }
    else if (command.equalsIgnoreCase("b"))
    {
      Serial.println("Burning settings to eeprom, enable autostart");
      burn_settings_to_eeprom();
    }
    else if (command.equalsIgnoreCase("e"))
    {
      Serial.println("Erasing EEPROM, disable autostart");
      format_eeprom();
    }
    else if (command.equalsIgnoreCase("d"))
    {
      Serial.println("Update Bounce Delay");
      Serial.print("Delay: ");
      Serial.print(payload);
      Serial.println("s");
      bounce_delay = payload * 10 / speed;
      // stepper_init();
    }
    // Send the response back to the computer
  }

#ifdef STATUS_MESSAGE
  if (millis() > next_send)
  {
    send_status_message();
    next_send = millis() + 1000;
  }
#endif

  if (millis() > next_step)
  {
    stepper_task();
    next_step = millis() + speed;
  }
}
