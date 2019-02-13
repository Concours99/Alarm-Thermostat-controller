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

__version__ = "v1.0"
TRACE = False

RELAY_PIN = 10

from WGHelper import *
from WGRadioThermostat import *
from time import sleep
import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library

def alarm_callback(channel) :
    sleep(0.25) # needed to let things settle
    if RadThermGetInt("tmode", TRACE) == TMODE_HEAT : # heat mode
        # if the pin goes high
        if GPIO.input(RELAY_PIN) :
            WGTracePrint("System armed!")
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
        else :
            # if the pin is low
            WGTracePrint("System disarmed!")
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
                return # try again next time
            # turn off SAVE_ENERGY_MODE
            intret = RadThermSetInt("mode", SAVE_ENERGY_MODE_DISABLE, TRACE)
            if intret == RadTherm_int_ERROR :
                return # try again next time
            # !!! Now should be running current program !!!
    # else : Don't worry about doing anything in the non-heating season
    
GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
# Set relay pin to be an input pin
GPIO.setup(RELAY_PIN, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

GPIO.add_event_detect(RELAY_PIN, GPIO.BOTH, callback = alarm_callback,
	bouncetime = 500)
    
running = True

while (running) :
    sleep(1)
# GPIO.cleanup()  # clean up after yourself  
