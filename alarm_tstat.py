#!/usr/bin/python3
""" alarm_tstat: Python app to alter RadioThermostat settings on alarm arm/disarm. """
###########################################################################
#
# alarm_tstat.py - Control Radio Thermostat when a switch (i.e., alarm
# relay) is armed/disarmed
#
# Copyright (C) 2019-2023, Wayne Geiser.  All Rights Reserved.
# email: geiserw@gmail.com
#
# You have no rights to any of this code without expressed permission.
#
###########################################################################
from time import sleep
from gpiozero import Button
from wg_helper import wg_trace_print
from wg_helper import wg_error_print
from wg_helper import wg_init_log
from wg_radio_thermostat import HOLD_DISABLED
from wg_radio_thermostat import HOLD_ENABLED
from wg_radio_thermostat import TMODE_HEAT
from wg_radio_thermostat import NIGHTLIGHT_OFF
from wg_radio_thermostat import NIGHTLIGHT_ON
from wg_radio_thermostat import RADTHERM_FLOAT_ERROR
from wg_radio_thermostat import RADTHERM_INT_ERROR
from wg_radio_thermostat import radtherm_get_todays_lowest_setting
from wg_radio_thermostat import radtherm_set_float
from wg_radio_thermostat import radtherm_set_int
from wg_radio_thermostat import radtherm_get_int
from wg_radio_thermostat import radtherm_status
from wg_radio_thermostat import SAVE_ENERGY_MODE_DISABLE
from wg_radio_thermostat import SAVE_ENERGY_MODE_ENABLE
from wg_messagesender import sendtext

__version__ = "v3.5"
APP_NAME = "Alarm T-stat Control"
TRACE = False
TEST_MODE = False

g_Just_Started = True

CELL_PHONE = "9784072619"

NO_RELAY_PIN_BCM = 15
NC_RELAY_PIN_BCM = 17
DEBOUNCE_SECONDS = 5.0

NUM_RETRIES = 10 # Number of times to retry a failed call


def setback_tstat(button):
    """ Set the thermostat to the lowest temp setting on today's prog. """

    wg_trace_print("Normally open switch held for " +
                   str(button.active_time) + " seconds", TRACE)
    tstat_status = radtherm_status()
    if 'error' in tstat_status:
        wg_error_print("setback_tstat",
                       "Error getting thermostat status.  Skipping...")
        return  # try again the next time
    tmode = tstat_status['tmode']   # thermostat mode (heat?)
    if tstat_status['hold'] == HOLD_ENABLED:
        return # don't mess with the settings, someone wants them this way
    if tmode != TMODE_HEAT:
        return # don't mess with the settings, we're not heating
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
            i = i + 1
            t = DEBOUNCE_SECONDS * i
            wg_trace_print("Error getting today's lowest setting, trying again in " +
                           str(t) + " seconds", True)
            sleep(t) # delay a little longer each time in hopes it'll work
            
    if setback_temp == RADTHERM_FLOAT_ERROR:
        # Send me a text message to tell me it didn't work
        sendtext(CELL_PHONE, APP_NAME,
                 "Unable to set thermostat back.  You'll have to do it via smartphone app.  Sorry.")


def run_tstat(button):
    """ Run the current thermostat prog. """
    global g_Just_Started

    wg_trace_print("Normally closed switch held for " +
                   str(button.active_time) + " seconds", TRACE)
    tstat_status = radtherm_status()
    if 'error' in tstat_status:
        wg_error_print("run_tstat",
                       "Error getting thermostat status.  Skipping...")
        return  # try again the next time
    tmode = tstat_status['tmode']   # thermostat mode (heat?)
    if tmode != TMODE_HEAT:
        wg_trace_print("We're not in heating mode.  Don't do anything.", TRACE)
        return # don't mess with the settings, we're not heating
    if TEST_MODE:
        wg_trace_print("Test mode.  Don't do anything.", TRACE)
        return
    if (tstat_status['hold'] == HOLD_ENABLED) and g_Just_Started:
        # if hold & we just started up, don't mess with the settings
        g_Just_Started = False # next time through will be because of a change to the alarm
        wg_trace_print("Hold enabled and we just started, not changing t-stat settings", TRACE)
        return
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

    wg_init_log("err.txt")
    wg_trace_print("Alarm/Tstat controller started.  Version: " + __version__, True)
    armed_switch = Button(NO_RELAY_PIN_BCM, hold_time=DEBOUNCE_SECONDS)
    disarmed_switch = Button(NC_RELAY_PIN_BCM, hold_time=DEBOUNCE_SECONDS, pull_up=True)
    armed_switch.when_held = setback_tstat
    disarmed_switch.when_held = run_tstat

    # Make sure we start out disarmed and the tstat is running it's program
    running = True
    run_tstat(disarmed_switch)

    while running:
        sleep(1)

main()
