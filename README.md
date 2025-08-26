# Alarm-Thermostat controller

#
# Copyright @ 2019-2023, Wayne Geiser.  All Rights Reserved.

#
# Contact the author via email: geiserw@gmail.com

This python application sends mqtt messages to a broker when pin #15 (BCM
numbering) on the Raspberry PI (named AlarmPi) goes high and returns it to the
currently running program when the pin #17 (also BCM numbering) goes high.

I have this connected to a relay board in my alarm system box.  The relay board
has three contacts ... a common, a normally open and a normally closed contact.
When the alarm system is armed, the relay closes and the normally open contact
is connected to the common / the normally closed contact is disconnected from
the common.  When the alarm system is disarmed, the normally closed contact is
conneced to the common and the normally open contact is disconnected from it.
The Raspberry pi pin #15 is conntected to the normally open contact and pin #17
is connected to the normally closed contact.

When the alarm is triggered, the relay will flip off and on.  I use the gpiozero
library to sense when the pins are held down for a number of seconds.  This
prevents the AlarmPi from constantly trying to change the thermostat when the
alarm is tripped.

Things you will need to cusomize:

1. all the things imported from SecretStuff:
	The URL of the mqtt broker
	The mqtt authorized user / password
