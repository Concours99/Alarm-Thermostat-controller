# Alarm-Thermostat controller
#
# Copyright @ 2019, Wayne Geiser.  All Rights Reserved.
#
# Contact the author via email: geiserw@gmail.com

This python application sets a Radio Thermostat WiFi thermostat back when pin
#10 on the Raspberry PI goes high and returns it to the currently running
program when the same pin goes low.

I have this connected to a relay in my alarm system box.  When the alarm system
is armed, the relay closes and the Raspberry pi pin goes high.  When the alarm
system is disarmed, the relay opens and the Raspberry pi pin goes low.

One issue that I needed to code around:

	When the alarm is tripped, the relay flashes off and on (the same as the
	red light on the alarm keypad).

Obviously, I didn't want the Raspberry pi to be continually altering the
thermostat settings while this was happening, so you can see in the code where
I simply count trips to the callback routine and then make sure that things
aren't changing before I call the routines to actually do the work.

You will need to insert your own thermostat name in the TSTAT_IP variable to
customize this to your environment.
