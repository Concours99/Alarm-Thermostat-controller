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
# Requirements:
#   paho-mqtt library
#
###########################################################################
from time import sleep
from wg_helper import wg_trace_print
from wg_helper import wg_error_print
from wg_helper import wg_init_log
import paho.mqtt.publish as publish
from SecretStuff import SECRET_HA_URL
from SecretStuff import SECRET_MQTT_USER
from SecretStuff import SECRET_MQTT_PASS

__version__ = "v5.0"
APP_NAME = "Alarm T-stat Control"
TRACE = False
TEST_MODE = False

if TEST_MODE :
    class Button():
        active_time = 0
else :
    from gpiozero import Button
    

g_Just_Started = True

NO_RELAY_PIN_BCM = 15
NC_RELAY_PIN_BCM = 17
DEBOUNCE_SECONDS = 5.0

ALARM_STATE_TOPIC = "homeassistant/alarm/state"

def setback_tstat(button):
    """ Set the thermostat to the lowest temp setting on today's prog. """
    global g_Just_Started
     
    if not TEST_MODE : # no button to quuery
        wg_trace_print("Normally open switch held for " +
                       str(button.active_time) + " seconds", TRACE)
    wg_trace_print("System armed", True)
    publish.single(ALARM_STATE_TOPIC,
                   "ON",
                   retain=True,
                   hostname=SECRET_HA_URL,
                   auth={'username': SECRET_MQTT_USER, 
                         'password': SECRET_MQTT_PASS})
    g_Just_Started = False # next time through will be because of a change 
                           # to the alarm

def run_tstat(button):
    """ Run the current thermostat prog. """
    global g_Just_Started

    if not TEST_MODE : # no button to query
        wg_trace_print("Normally closed switch held for " +
                       str(button.active_time) + " seconds", TRACE)
    wg_trace_print("System disarmed", True)
    publish.single(ALARM_STATE_TOPIC,
                   "OFF",
                   retain=True,
                   hostname=SECRET_HA_URL,
                   auth={'username': SECRET_MQTT_USER,
                         'password': SECRET_MQTT_PASS})                   
    g_Just_Started = False # next time through will be because of a change 
                           # to the alarm

def main():
    """ alarm_tstat main code. """
    
    wg_init_log("err.txt")
    wg_trace_print("Alarm/Tstat controller started.  Version: " + __version__, True)
    if not TEST_MODE :
        armed_switch = Button(NO_RELAY_PIN_BCM, hold_time=DEBOUNCE_SECONDS)
        disarmed_switch = Button(NC_RELAY_PIN_BCM, hold_time=DEBOUNCE_SECONDS, pull_up=True)
        armed_switch.when_held = setback_tstat
        disarmed_switch.when_held = run_tstat

    running = True

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
