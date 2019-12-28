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
from gpiozero import Button
from wg_helper import wg_trace_print
from wg_helper import wg_error_print
from wg_radio_thermostat import HOLD_DISABLED
from wg_radio_thermostat import HOLD_ENABLED
from wg_radio_thermostat import NIGHTLIGHT_OFF
from wg_radio_thermostat import NIGHTLIGHT_ON
from wg_radio_thermostat import RADTHERM_FLOAT_ERROR
from wg_radio_thermostat import RADTHERM_INT_ERROR
from wg_radio_thermostat import radtherm_get_todays_lowest_setting
from wg_radio_thermostat import radtherm_set_float
from wg_radio_thermostat import radtherm_set_int
from wg_radio_thermostat import SAVE_ENERGY_MODE_DISABLE
from wg_radio_thermostat import SAVE_ENERGY_MODE_ENABLE
from wg_twilio import sendtext

__version__ = "v3.1"
TRACE = False
TEST_MODE = False

NO_RELAY_PIN_BCM = 15
NC_RELAY_PIN_BCM = 17
DEBOUNCE_SECONDS = 5.0

NUM_RETRIES = 5 # Number of times to retry a failed call


def setback_tstat(button):
    """ Set the thermostat to the lowest temp setting on today's prog. """

    wg_trace_print("Normally open switch held for " + str(button.active_time) + " seconds", TRACE)
    if TEST_MODE:
        return
    i = 0
    setback_temp = RADTHERM_FLOAT_ERROR
    while i < NUM_RETRIES and setback_temp == RADTHERM_FLOAT_ERROR:
        setback_temp = radtherm_get_todays_lowest_setting(TRACE)
        if setback_temp != RADTHERM_FLOAT_ERROR:
            wg_trace_print("Setting target temp to " + str(setback_temp), TRACE)
            # set the temporary temperature to the value we found, above
            floatret = radtherm_set_float("t_heat", setback_temp, TRACE)
            if floatret == RADTHERM_FLOAT_ERROR:
                wg_error_print("setback_tstat", "Error setting t_heat")
                return
            # set the t-stat to hold
            intret = radtherm_set_int("hold", HOLD_ENABLED, TRACE)
            if intret == RADTHERM_INT_ERROR:
                wg_error_print("setback_tstat", "Error setting hold")
                return
            # turn the night light off
            intret = radtherm_set_int("intensity", NIGHTLIGHT_OFF, TRACE)
            if intret == RADTHERM_INT_ERROR:
                wg_error_print("setback_tstat", "Error setting intensity")
                return
            wg_trace_print("System armed", True)
        else:
            sleep(DEBOUNCE_SECONDS)
            i = i + 1
    if setback_temp == RADTHERM_FLOAT_ERROR:
        # Send me a text message to tell me it didn't work
        sendtext("Unable to set thermostat back.  You'll have to do it via smartphone app.  Sorry.")


def run_tstat(button):
    """ Run the current thermostat prog. """

    wg_trace_print("Normally closed switch held for " + str(button.active_time) + " seconds", TRACE)
    if TEST_MODE:
        return
    # wait to see if we get anymore button presses in the next DEBOUNCE_SECONDS seconds
    # disable hold
    intret = radtherm_set_int("hold", HOLD_DISABLED, TRACE)
    if intret == RADTHERM_INT_ERROR:
        wg_error_print("run_tstat", "Error setting hold")
        return
    # set the tstat to SAVE_ENERGY_MODE
    intret = radtherm_set_int("mode", SAVE_ENERGY_MODE_ENABLE, TRACE)
    if intret == RADTHERM_INT_ERROR:
        wg_error_print("run_tstat", "Error enabling save energy mode")
        return
    # turn off SAVE_ENERGY_MODE
    intret = radtherm_set_int("mode", SAVE_ENERGY_MODE_DISABLE, TRACE)
    if intret == RADTHERM_INT_ERROR:
        wg_error_print("run_tstat", "Error disabling save energy mode")
        return
    # !!! Now should be running current program !!!
    # turn the night light on
    intret = radtherm_set_int("intensity", NIGHTLIGHT_ON, TRACE)
    if intret == RADTHERM_INT_ERROR:
        wg_error_print("run_tstat", "Error setting intensity")
        return
    wg_trace_print("System disarmed", True)


def main():
    """ alarm_tstat main code. """

    wg_trace_print("Alarm/Tstat controller started.  Version: " + __version__, True)
    armed_switch = Button(NO_RELAY_PIN_BCM, hold_time=DEBOUNCE_SECONDS)
    disarmed_switch = Button(NC_RELAY_PIN_BCM, hold_time=DEBOUNCE_SECONDS)
    armed_switch.when_held = setback_tstat
    disarmed_switch.when_held = run_tstat

    # Make sure we start out disarmed and the tstat is running it's program
    running = True
    run_tstat(disarmed_switch)

    while running:
        sleep(1)

main()
