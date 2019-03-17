################################################################################
#
# alarm-tstat.py - Control Radio Thermostat when a switch (i.e., alarm relay) is
#   armed/disarmed
#
# Copyright (C) 2019, Wayne Geiser.  All Rights Reserved.
# email: geiserw@gmail.com
#
# You have no rights to any of this code without expressed permission.
#
################################################################################

__version__ = "v1.01"
TRACE = False

RELAY_PIN = 10

from WGHelper import *
from WGRadioThermostat import *
import time
import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library

def alarm_callback(channel) :
    global previous
    global armed
    # see if we're bouncing
    current = time.time()
    if (current - previous) < 7.0 :
        WGTracePrint("Bouncing?  Seconds since last call = " + str(current - previous))
        previous = current
        return
    
    time.sleep(0.25) # needed to let things settle
    if RadThermGetInt("tmode", TRACE) == TMODE_HEAT : # heat mode
        # if the pin goes high
        if GPIO.input(RELAY_PIN) :
            WGTracePrint("System armed! Seconds since last call = " + str(current - previous))
            # set the thermostat back
            setback_temp = RadThermGetTodaysLowestSetting(TRACE)
            if (setback_temp != RadTherm_float_ERROR) :
                WGTracePrint("Setting target temp to " + str(setback_temp))
                # set the temporary temperature to the value we found, above
                floatret = RadThermSetFloat("t_heat", setback_temp, TRACE)
                if floatret == RadTherm_float_ERROR :
                    return
                # set the t-stat to hold
                intret = RadThermSetInt("hold", HOLD_ENABLED, TRACE)
                if intret == RadTherm_int_ERROR :
                    return
                # turn the night light off
                intret = RadThermSetInt("intensity", NIGHTLIGHT_OFF, TRACE)
                if intret == RadTherm_int_ERROR :
                    return
                armed = True
        else : # the pin is low
            if armed :
                WGTracePrint("System disarmed! Seconds since last call = " + str(current - previous))
                # turn the night light on
                intret = RadThermSetInt("intensity", NIGHTLIGHT_ON, TRACE)
                if intret == RadTherm_int_ERROR :
                    return
                # disable hold
                intret = RadThermSetInt("hold", HOLD_DISABLED, TRACE)
                if intret == RadTherm_int_ERROR :
                    return
                # set the tstat to SAVE_ENERGY_MODE
                intret = RadThermSetInt("mode", SAVE_ENERGY_MODE_ENABLE, TRACE)
                if intret == RadTherm_int_ERROR :
                    return
                # turn off SAVE_ENERGY_MODE
                intret = RadThermSetInt("mode", SAVE_ENERGY_MODE_DISABLE, TRACE)
                if intret == RadTherm_int_ERROR :
                    return
                # !!! Now should be running current program !!!
                armed = False
            else : # already disarmed
                WGTracePrint("System already disarmed, ignoring! Seconds since last call = " + str(current - previous))
        previous = current
    else : # Don't worry about doing anything in the non-heating season
        WGTracePrint("Non-heating season, ignoring! Seconds since last call = " + str(current - previous))
        previous = current
    
GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
# Set relay pin to be an input pin
GPIO.setup(RELAY_PIN, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

GPIO.add_event_detect(RELAY_PIN, GPIO.BOTH, callback = alarm_callback,
	bouncetime = 500)
    
running = True
previous = time.time()
armed = False

WGTracePrint("Alarm/Tstat controller started.  Version: " + __version__)
while (running) :
    time.sleep(1)
# GPIO.cleanup()  # clean up after yourself  
