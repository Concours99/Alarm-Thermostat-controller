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
from wg_helper import wg_trace_print
from wg_helper import wg_error_print
from wg_helper import wg_init_log
from wg_ecobee import HOLD_ENABLED
from wg_ecobee import HOLD_DISABLED
from wg_ecobee import TMODE_HEAT
from wg_ecobee import TSTAT_ERROR
from wg_ecobee import ecobee_get_status
from wg_ecobee import authorize_app_with_ecobee
from wg_ecobee import ecobee_get_todays_lowest_setting
from wg_ecobee import ecobee_set_hold_temp
from wg_ecobee import ecobee_resume_program
from wg_ecobee import ecobee_send_alert
from wg_messagesender import sendtext

__version__ = "v4.1"
APP_NAME = "Alarm T-stat Control"
TRACE = False
TEST_MODE = False

if TEST_MODE :
    class Button():
        active_time = 0
else :
    from gpiozero import Button
    

g_Just_Started = True

CELL_PHONE = "9784072619"

NO_RELAY_PIN_BCM = 15
NC_RELAY_PIN_BCM = 17
DEBOUNCE_SECONDS = 5.0

NUM_RETRIES = 10 # Number of times to retry a failed call


def setback_tstat(button):
    """ Set the thermostat to the lowest temp setting on today's prog. """
    global g_Just_Started

    if not TEST_MODE : # no button to quuery
        wg_trace_print("Normally open switch held for " +
                       str(button.active_time) + " seconds", TRACE)
    tstat_status = ecobee_get_status(TRACE)
    if 'error' in tstat_status:
        wg_error_print("setback_tstat",
                       "Error getting thermostat status.  Skipping...")
        return  # try again the next time
    tmode = tstat_status['tmode']   # thermostat mode (heat?)
    if tstat_status['hold'] == HOLD_ENABLED:
        wg_trace_print("Hold enabled.  Don't do anything", TRACE)
        return # don't mess with the settings, someone wants them this way
    if tmode != TMODE_HEAT:
        wg_trace_print("We're not in heating mode.  Don't do anything.", TRACE)
        return # don't mess with the settings, we're not heating
    i = 0
    setback_temp = TSTAT_ERROR
    while i < NUM_RETRIES and setback_temp == TSTAT_ERROR:
        setback_temp = ecobee_get_todays_lowest_setting(TRACE)        
        if setback_temp != TSTAT_ERROR:
            wg_trace_print("Setting target temp to " + str(setback_temp), TRACE)
            # set the temporary temperature to the value we found, above
            ret = ecobee_set_hold_temp(setback_temp, TRACE)
            if ret == TSTAT_ERROR:
                wg_error_print("setback_tstat", "Error setting t_heat")
                return
            # turn the night light off
            # ret = ecobee_set_intensity(NIGHTLIGHT_OFF, TRACE)
            # if ret == TSTAT_ERROR:
            #     wg_error_print("setback_tstat", "Error setting intensity")
            #    return
            wg_trace_print("System armed", True)
        else:
            i = i + 1
            t = DEBOUNCE_SECONDS * i
            wg_trace_print("Error getting today's lowest setting, trying again in " +
                           str(t) + " seconds", True)
            sleep(t) # delay a little longer each time in hopes it'll work
    g_Just_Started = False
    if setback_temp == TSTAT_ERROR:
        # Send me a text message to tell me it didn't work
        sendtext(CELL_PHONE, APP_NAME,
                 "Unable to set thermostat back.  You'll have to do it via smartphone app.  Sorry.")

def run_tstat(button):
    """ Run the current thermostat prog. """
    global g_Just_Started

    if not TEST_MODE : # no button to query
        wg_trace_print("Normally closed switch held for " +
                       str(button.active_time) + " seconds", TRACE)
    tstat_status = ecobee_get_status(TRACE)
    if 'error' in tstat_status:
        wg_error_print("run_tstat",
                       "Error getting thermostat status.  Skipping...")
        return  # try again the next time
    tmode = tstat_status['tmode']   # thermostat mode (heat?)
    if tmode != TMODE_HEAT:
        wg_trace_print("We're not in heating mode.  Don't do anything.", TRACE)
        return # don't mess with the settings, we're not heating
    if (tstat_status['hold'] == HOLD_ENABLED) and g_Just_Started:
        # if hold & we just started up, don't mess with the settings
        wg_trace_print("Hold enabled and we just started, not changing t-stat settings", TRACE)
        return
    # disable hold
    ret = ecobee_resume_program(TRACE)
    if ret == TSTAT_ERROR:
        wg_error_print("run_tstat", "Error disabling hold")
        return
    # !!! Now should be running current program !!!
    # turn the night light on
    # ret = ecobee_set_intensity(NIGHTLIGHT_ON, TRACE)
    # if ret == TSTAT_ERROR:
    #     wg_error_print("run_tstat", "Error setting intensity")
    #     return
    wg_trace_print("System disarmed", True)
    g_Just_Started = False # next time through will be because of a change to the alarm


def main():
    """ alarm_tstat main code. """

    authorize_app_with_ecobee(TRACE) # We only need to do this at startup because we reboot once a day
    wg_init_log("err.txt")
    wg_trace_print("Alarm/Tstat controller started.  Version: " + __version__, True)
    if not TEST_MODE :
        armed_switch = Button(NO_RELAY_PIN_BCM, hold_time=DEBOUNCE_SECONDS)
        disarmed_switch = Button(NC_RELAY_PIN_BCM, hold_time=DEBOUNCE_SECONDS, pull_up=True)
        armed_switch.when_held = setback_tstat
        disarmed_switch.when_held = run_tstat

    # Make sure we start out disarmed and the tstat is running it's program
    running = True
    if TEST_MODE :
        b = Button()
        run_tstat(b)
    else :
        run_tstat(disarmed_switch)

    if TEST_MODE :
        print("1 alarm armed - 2 alarm disarmed")
    while running:
        if TEST_MODE:
            num = int(input())
            if num == 1 :
                setback_tstat(0)
            elif  num == 2 :
                run_tstat(0)
            else :
                wg_error_print("main", "Bad input: expecting either 1 to setback or 2 to resume")
        else :
            sleep(1)

main()
