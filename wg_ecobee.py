# pylint: disable=w0613

"""Routines to query and control Radio Thermostat WiFi thermostat"""
#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (C) 2018-2023, Wayne Geiser (geiserw@gmail.com).  All Rights Reserved
#
# Helper functiona and definitions to interface with an Ecobee thermostat
import os
import datetime
import json
import requests
import traceback
from time import sleep
from urllib3 import PoolManager
from wg_helper import wg_error_print
from wg_helper import wg_trace_print
from wg_helper import wg_trace_pprint

WG_ECOBEE_THERMOSTAT_VERSION = "1.0"

# One (and only one) of these should be True.  It sets up the correct keys
APP_ALARMPI   = True
APP_WEATHERPI = False

# Ecobee stuff
if APP_ALARMPI :
    ECOBEE_KEY = "syzVJMlDoZLh6HoLaSE0LF1JZTLInd24"
if APP_WEATHERPI :
    ECOBEE_KEY = "ZfuqdNHcDemn9Y88h39eoZUOLXYOcDIF"
ECOBEE_URL = 'https://api.ecobee.com/1/thermostat'

# Turn this on if you want checking code to be run
DEBUGGING = False

# fmode = fan mode
FAN_AUTO = 0
FAN_CIRC = 1
FAN_ON = 2
# tmode = thermostat mode
TMODE_OFF = 0
TMODE_HEAT = 1
TMODE_COOL = 2
TMODE_AUTO = 3
# hold = target temperature hold
HOLD_DISABLED = 0
HOLD_ENABLED = 1

TSTAT_ERROR = -999
TSTAT_SUCCESS = 999

NUM_TRIES = 5

###############################################################################
#
# The application needs to be authorized the the ecobee.
# This authorization will time out and must be renewed.
#

# various values that need to be remembered to get (and refresh) app authorization
if APP_ALARMPI :
    authcode = "t49XGtAP4ZWOI8FLaWD3m-5f"
if APP_WEATHERPI :
   authcode = "hz9rgMxp48pWXr-Y83TGoXpG"

tok_file_name = "token_storage.txt"

def ecobee_get_saved_tokens(trace) :
    """Get the saved access and refresh tokens"""
    # Obtain access token and refresh token
    # Read the tokens from a temporary storage file
    # The file should contain an accesstoken on the first line and a refresh token on the
    # second line
    acctoken = ' '
    reftoken = ' '
    if os.path.isfile(tok_file_name) :
        # we have stored tokens
        tok_file = open(tok_file_name, "r")
        acctoken = tok_file.readline().replace('\n', '')
        reftoken = tok_file.readline().replace('\n', '')
    return acctoken, reftoken
    
def authorize_app_with_ecobee(trace) :
    """Authorize the application"""
    try :
        acctoken, reftoken = ecobee_get_saved_tokens(trace)
        if reftoken == " " :
            # First time through, we don't have a refresh token yet
            url = ('https://api.ecobee.com/token?grant_type=ecobeePin&code=' + authcode +
                   '&client_id=' + ECOBEE_KEY)
            pman = PoolManager()
            ret = pman.request_encode_url('POST', url)
            retval = json.loads(ret.data.decode('utf-8'))
            wg_trace_pprint(json.dumps(retval, indent=4), trace)
            if retval.get('error_description') != None  :
                wg_error_print("authorize_app_with_ecobee",
                               "Error with access_token call")
                wg_error_print("authorize_app_with_ecobee",
                               retval.get('error_description'))
                return TSTAT_ERROR
            acctoken = retval['access_token']
            reftoken = retval['refresh_token']       
        else :
            # We have a refresh token, refresh the authorization
            url = "https://api.ecobee.com/token"
            data = {
                'grant_type': 'refresh_token',
                'code': reftoken,
                'client_id': ECOBEE_KEY
            }
            retval = requests.post(url, data=data).json()
            if retval.get('error_description') != None  :
                wg_error_print("authorize_app_with_ecobee",
                               "Error with refresh_token call")
                wg_error_print("authorize_app_with_ecobee",
                               retval.get('error_description'))
                return TSTAT_ERROR
            acctoken = retval['access_token']
            reftoken = retval['refresh_token']
        # Write the two tokens to the temporary storage file
        tok_file = open(tok_file_name, "w")
        tok_file.write(acctoken)
        tok_file.write('\n')
        tok_file.write(reftoken)
        tok_file.write('\n')
        return TSTAT_SUCCESS
    except Exception as e:
        wg_error_print("authorize_app_with_ecobee", str(e))
        print(traceback.format_tb(e.__traceback__))
        return TSTAT_ERROR
        
def get_tstat_data(trace, count) :
    """ Get current thermostat runtimes"""
    try: 
        if count <= NUM_TRIES :
            acctoken, reftoken = ecobee_get_saved_tokens(trace)
            headers = {
                'Content-Type'  : 'text/json',
                'Authorization' : 'Bearer ' + acctoken
            }
            data = {
                "format" : "json",
                "body"   : ('{' +
                                '"selection" : {' +
                                    '"selectionType"   : "registered",' + 
                                    '"selectionMatch"  : "",' +
                                    '"includeRuntime"  : true,' +
                                    '"includeSettings" : true,' +
                                    '"includeProgram"  : true,' +
                                    '"includeEvents"   : true'
                                '}' +
                             '}')
            }
            retval = requests.request('GET', ECOBEE_URL, params=data, headers=headers).json()
            if retval.get('status').get('code') == 0 :
                return retval
            elif retval.get('status').get('code') == 14 : # token expired refresh
                wg_trace_print("Ecobee tokens are expired.  Refreshing them.", True)
                authorize_app_with_ecobee(trace)
                return get_tstat_data(trace, count + 1)
            else :
                wg_trace_print("Uunable to get tstat data, trying again in 5 seconds.", trace)
                wg_trace_pprint(json.dumps(retval, indent=4), True)
            sleep(5)
        return retval # all we can do is pass along the error
    except Exception as e:
        wg_error_print("get_tstat_data", str(e))
        print(traceback.format_tb(e.__traceback__))
        retval = {'status' : {'code' : 999}}
        return retval
  
def ecobee_get_status(trace) :
    """Get the status of the thermostat"""
    retval = {} # This will have all the values we will return

    tstat_status = get_tstat_data(trace, 1)
    wg_trace_pprint(json.dumps(tstat_status, indent=4), trace)
    if not tstat_status.get('status').get('code') == 0 :
        # error.  Try to get out gracefully
        retval['error'] = "get_tstat_data failed!"
        wg_trace_pprint(json.dumps(tstat_status, indent=4), True)
        return retval

    tstat = tstat_status.get('thermostatList')[0]
    
    # tmode - Current thermostat mode setting
    status_str = tstat.get('settings').get('hvacMode')
    if status_str == "auto" :
        retval['tmode'] = TMODE_AUTO
    elif (status_str == "auxHeatOnly") or (status_str == "heat") :
        retval['tmode'] = TMODE_HEAT
    elif status_str == "cool" :
        retval['tmode'] = TMODE_COOL
    elif status_str == "off" :
         retval['tmode'] = TMODE_OFF
    else :
        retval['error'] = 'Unknown State value: ' + status_str
        
    # temp - Current displayed temperature
    status_str = tstat.get('runtime').get('actualTemperature')
    retval['temp'] = int(status_str) / 10
    
    # humid - Current displayed humidity
    status_str = tstat.get('runtime').get('actualHumidity')
    retval['humid'] = int(status_str)

    # t_heat - Current temperature desired
    status_str = tstat.get('runtime').get('desiredHeat')
    retval['t_heat'] = int(status_str)

    # fmode - fan mode (auto, on, null)
    status_str = tstat.get('runtime').get('desiredFanMode')
    if status_str == "on" :
        retval['fmode'] = FAN_ON
    else :
        retval['fmode'] = FAN_AUTO
    
    
    # hold - in hold state
    retval['hold'] = HOLD_DISABLED
    tstat_events = tstat.get('events')
    for event in tstat_events :
        if event.get('type') == 'hold' :
            if event.get('running') :
                retval['hold'] = HOLD_ENABLED
                break
    
    wg_trace_pprint(json.dumps(retval, indent=4), trace)
    
    return retval

def ecobee_get_todays_highest_setting(trace) :
    """Get the setting for when we are here"""
    retval = TSTAT_ERROR
    tstat_status = get_tstat_data(trace, 1)
    wg_trace_pprint(json.dumps(tstat_status, indent=4), trace)
    
    # Current thermostat mode setting
    climates = tstat_status.get('thermostatList')[0].get('program').get('climates')
    for climate in climates :
        if climate.get('name') == "Home" :
            retval = int(climate.get('heatTemp'))
    return retval

def ecobee_get_todays_lowest_setting(trace) :
    """Get the setting for when we are away"""
    retval = TSTAT_ERROR
    tstat_status = get_tstat_data(trace, 1)
    wg_trace_pprint(json.dumps(tstat_status, indent=4), trace)
    
    # Current thermostat mode setting
    climates = tstat_status.get('thermostatList')[0].get('program').get('climates')
    for climate in climates :
        if climate.get('name') == "Away" :
            retval = int(climate.get('heatTemp'))
    return retval

def ecobee_control_fan(mode, trace) :
    """Set thermostat hold and temp"""
    acctoken, reftoken = ecobee_get_saved_tokens(trace)
    headers = {
        'Content-Type'  : 'application/json;charset=UTF-8',
        'Authorization' : 'Bearer ' + acctoken
    }
    if mode == FAN_ON :
        data = {
                "format" : "json",
                "body"   : ('{' +
                    '"selection" : {' +
                        '"selectionType"  : "registered",' +
                        '"selectionMatch" : ""' +
                    '},' +
                    '"functions" : [{' +
                        '"type"   : "setHold",' +
                        '"params" : {' +
                            '"fan"    : "on"' +
                        '}' +
                    '}]' +
                '}')
        }
        wg_trace_pprint(json.dumps(data, indent=4), trace)
        retval = requests.request('POST', ECOBEE_URL, params=data, headers=headers).json()
        wg_trace_pprint(json.dumps(retval, indent=4), trace)
        if DEBUGGING :
            # Check to make sure it actually did items
            stat = ecobee_get_status(trace)
        if retval.get('status').get('code') == 0 :
            return TSTAT_SUCCESS
        else:
            return TSTAT_ERROR
    else :
        # set back to auto by resuming the hold state
        return ecobee_resume_program(trace)

def ecobee_set_hold_temp(setback_temp, trace) :
    """Set thermostat hold and temp"""
    wg_trace_print("setback_temp is " + str(setback_temp), trace)
    acctoken, reftoken = ecobee_get_saved_tokens(trace)
    headers = {
        'Content-Type'  : 'application/json;charset=UTF-8',
        'Authorization' : 'Bearer ' + acctoken
    }
    data = {
            "format" : "json",
            "body"   : ('{' +
                '"selection" : {' +
                    '"selectionType"  : "registered",' +
                    '"selectionMatch" : ""' +
                '},' +
                '"functions" : [{' +
                    '"type"   : "setHold",' +
                    '"params" : {' +
                        '"holdtype"    : "indefinite",' +
                        '"heatHoldTemp" : ' + str(int(setback_temp)) + ',' +
                        '"coolHoldTemp" : ' + str(int(setback_temp)) +
                    '}' +
                '}]' +
            '}')
    }
    wg_trace_pprint(json.dumps(data, indent=4), trace)
    retval = requests.request('POST', ECOBEE_URL, params=data, headers=headers).json()
    wg_trace_pprint(json.dumps(retval, indent=4), trace)
    if DEBUGGING :
        # Check to make sure it actually did items
        stat = ecobee_get_status(trace)
        if not stat['hold'] == HOLD_ENABLED :
            wg_error_print("ecobee_set_hold_temp", "Hold did not get set!")
    if retval.get('status').get('code') == 0 :
        return TSTAT_SUCCESS
    else:
        return TSTAT_ERROR

def ecobee_send_alert(msg, trace) :
    """Send an alert message to the tstat"""
    
    #
    # This doesn't just write a message to the screen.
    # It sends an alert that must be acknowledged, either in the app or on the tstat screen
    #
    
    acctoken, reftoken = ecobee_get_saved_tokens(trace)
    headers = {
        'Content-Type'  : 'application/json;charset=UTF-8',
        'Authorization' : 'Bearer ' + acctoken
    }
    headers = {
        'Content-Type'  : 'application/json;charset=UTF-8',
        'Authorization' : 'Bearer ' + acctoken
    }
    data = {
            "format" : "json",
            "body"   : ('{' +
                '"selection" : {' +
                    '"selectionType"  : "registered",' +
                    '"selectionMatch" : ""' +
                '},' +
                '"functions" : [{' +
                    '"type" : "sendMessage",' +
                    '"params" : {' +
                        '"text" : "' + msg + '"'
                    '}' +
                '}]' +
            '}')
    }
    retval = requests.request('POST', ECOBEE_URL, params=data, headers=headers).json()
    wg_trace_pprint(json.dumps(retval, indent=4), trace)
    if retval.get('status').get('code') == 0 :
        return TSTAT_SUCCESS
    else:
        return TSTAT_ERROR

def ecobee_resume_program(trace) :
    """Run the tstat's program"""
    #
    # Note that this code fails if there isn't a hold
    #
    acctoken, reftoken = ecobee_get_saved_tokens(trace)
    headers = {
        'Content-Type'  : 'application/json;charset=UTF-8',
        'Authorization' : 'Bearer ' + acctoken
    }
    data = {
            "format" : "json",
            "body"   : ('{' +
                '"selection" : {' +
                    '"selectionType"  : "registered",' +
                    '"selectionMatch" : ""' +
                '},' +
                '"functions" : [{' +
                    '"type" : "resumeProgram",' +
                    '"params" : {' +
                        '"resumeAll" : true' +
                    '}' +
                '}]' +
            '}')
    }
    wg_trace_pprint(json.dumps(data, indent=4), trace)
    retval = requests.request('POST', ECOBEE_URL, params=data, headers=headers).json()
    wg_trace_pprint(json.dumps(retval, indent=4), trace)
    if retval.get('status').get('code') == 0 :
        return TSTAT_SUCCESS
    else:
        return TSTAT_ERROR

