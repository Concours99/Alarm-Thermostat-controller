# pylint: disable=e0401

#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (C) 2023, Wayne Geiser (geiserw@gmail.com).  All Rights Reserved
#
# Helper functiona and definitions to send emails and text messages
#
# Note, sending either a text message or an email message requires a MailTrap account
# (SMS messages are sent as email to the carrier gateway)
"""Interface to a email and text (SMS)"""
import mailtrap as mt

# CARRIERDOMAIN = "mailmymobile.net" # This stopped working for Consumer Cellular, noticed 2023-Nov
CARRIERDOMAIN = "txt.att.net"
FROMEMAILADDR = "pythonapps@geiserweb.com"
FROMEMAILNAME = "WG Python app"
MAILTRAPTOKEN = "9865f60bf9b7987b7bbf3d8f2d4c35a7"

####################################################################
#
# Send an email message
#
def sendemail(toaddress, app, message):
    # create mail object
    mail = mt.Mail(
        sender=mt.Address(email=FROMEMAILADDR, name=FROMEMAILNAME),
        to=[mt.Address(email=toaddress)],
        subject="Notification from " + app,
        text=message)

    # create client and send
    client = mt.MailtrapClient(token=MAILTRAPTOKEN)
    client.send(mail)

####################################################################
#
# Send a text message
#
def sendtext(phonenumber, app, message):
    emailaddress = phonenumber + '@' + CARRIERDOMAIN
    sendemail(emailaddress, app, message)
