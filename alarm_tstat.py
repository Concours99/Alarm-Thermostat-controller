""" alarm_tstat: Python app to alter RadioThermostat settings on alarm arm/disarm. """
################################################################################
#
# alarm_tstat.py - Control Radio Thermostat when a switch (i.e., alarm relay) is
#   armed/disarmed
#
# Copyright (C) 2019, Wayne Geiser.  All Rights Reserved.
# email: geiserw@gmail.com
#
# You have no rights to any of this code without expressed permission.
#
################################################################################
from time import sleep
from time import time
import RPi.GPIO as GPIO # pylint: disable=E0401
from wg_helper import wg_trace_print
from wg_radio_thermostat import HOLD_DISABLED
from wg_radio_thermostat import HOLD_ENABLED
from wg_radio_thermostat import NIGHTLIGHT_OFF
from wg_radio_thermostat import NIGHTLIGHT_ON
from wg_radio_thermostat import RADTHERM_FLOAT_ERROR
from wg_radio_thermostat import RADTHERM_INT_ERROR
from wg_radio_thermostat import radtherm_get_int
from wg_radio_thermostat import radtherm_get_todays_lowest_setting
from wg_radio_thermostat import radtherm_set_float
from wg_radio_thermostat import radtherm_set_int
from wg_radio_thermostat import SAVE_ENERGY_MODE_DISABLE
from wg_radio_thermostat import SAVE_ENERGY_MODE_ENABLE
from wg_radio_thermostat import TMODE_HEAT

__version__ = "v2.0"
TRACE = False

RELAY_PIN = 10
DEBOUNCE_SECONDS = 7.0
NUM_CALLBACKS_SINCE_HANDLED = 0


def alarm_callback(channel): # pylint: disable=W0613
    """ Callback for GPIO pin changing from high to low or vice bersa. """
    global NUM_CALLBACKS_SINCE_HANDLED # pylint: disable=W0603
    NUM_CALLBACKS_SINCE_HANDLED = NUM_CALLBACKS_SINCE_HANDLED + 1


def setback_tstat():
    """ Set the thermostat to the lowest temp setting on today's prog. """
    setback_temp = radtherm_get_todays_lowest_setting(TRACE)
    if setback_temp != RADTHERM_FLOAT_ERROR:
        wg_trace_print("Setting target temp to " + str(setback_temp))
        # set the temporary temperature to the value we found, above
        floatret = radtherm_set_float("t_heat", setback_temp)
        if floatret == RADTHERM_FLOAT_ERROR:
            wg_trace_print("Error setting t_heat")
            return
        # set the t-stat to hold
        intret = radtherm_set_int("hold", HOLD_ENABLED)
        if intret == RADTHERM_INT_ERROR:
            wg_trace_print("Error setting hold")
            return
        # turn the night light off
        intret = radtherm_set_int("intensity", NIGHTLIGHT_OFF)
        if intret == RADTHERM_INT_ERROR:
            wg_trace_print("Error setting intensity")
            return


def run_tstat():
    """ Run the current thermostat prog. """
    # turn the night light on
    intret = radtherm_set_int("intensity", NIGHTLIGHT_ON)
    if intret == RADTHERM_INT_ERROR:
        wg_trace_print("Error setting intensity")
        return
    # disable hold
    intret = radtherm_set_int("hold", HOLD_DISABLED)
    if intret == RADTHERM_INT_ERROR:
        wg_trace_print("Error setting hold")
        return
    # set the tstat to SAVE_ENERGY_MODE
    intret = radtherm_set_int("mode", SAVE_ENERGY_MODE_ENABLE)
    if intret == RADTHERM_INT_ERROR:
        wg_trace_print("Error enabling save energy mode")
        return
    # turn off SAVE_ENERGY_MODE
    intret = radtherm_set_int("mode", SAVE_ENERGY_MODE_DISABLE)
    if intret == RADTHERM_INT_ERROR:
        wg_trace_print("Error disabling save energy mode")
        return
    # !!! Now should be running current program !!!


def main():
    """ alarm_tstat main code. """
    global NUM_CALLBACKS_SINCE_HANDLED # pylint: disable=W0603

    GPIO.setwarnings(False) # Ignore warning for now
    GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
    # Set relay pin to be an input pin
    GPIO.setup(RELAY_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    GPIO.add_event_detect(RELAY_PIN, GPIO.BOTH, callback=alarm_callback,
                          bouncetime=500)

    armed = False
    running = True
    previous = time()

    wg_trace_print("Alarm/Tstat controller started.  Version: " + __version__)
    while running:
        sleep(1)
        current = time()
        if (current - previous) >= DEBOUNCE_SECONDS:
            if NUM_CALLBACKS_SINCE_HANDLED > 1:  # we've had several events wait
                NUM_CALLBACKS_SINCE_HANDLED = 0  # wait until things have calmed
                                                 # down
            else:
                # if the pin goes high
                if GPIO.input(RELAY_PIN) and not armed:
                    if radtherm_get_int("tmode", TRACE) == TMODE_HEAT: # heat mode
                        wg_trace_print("System armed! Seconds since last call = " +
                                       str(current - previous))
                        # set the thermostat back
                        setback_tstat()
                        armed = True
                elif not GPIO.input(RELAY_PIN) and armed:
                    if radtherm_get_int("tmode", TRACE) == TMODE_HEAT: # heat mode
                        wg_trace_print("System disarmed! Seconds since last call = " +
                                       str(current - previous))
                        # run current program
                        run_tstat()
                        armed = False
        previous = current

    GPIO.cleanup()  # clean up after yourself

main()
