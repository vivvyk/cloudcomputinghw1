import json
import boto3
import json
import logging
import boto3
from botocore.exceptions import ClientError
import math
import datetime
import time
import os
import logging
import json
import re

def send_sqs_message(sqs_queue_url, msg_body):
    # Send message to queue
    sqs_client = boto3.client('sqs')
    msg = sqs_client.send_message(QueueUrl=sqs_queue_url,MessageBody=msg_body)
    return msg

def main_sqs(locationType, cuisineType, peopleType, timeType, numberType):
    # Formats message and sends
    sqs_queue_url = 'https://sqs.us-east-1.amazonaws.com/239851179186/Q1'
    msg_body = json.dumps({"location":locationType,"cuisine":cuisineType,"time":timeType,"people":peopleType,"number":numberType})
    msg = send_sqs_message(sqs_queue_url, msg_body)

def delegate(event):
    # Lex delegation
    slots = event["currentIntent"]["slots"]

    nnslots = {}
    for key in slots.keys():
        if slots[key] is not None:
            nnslots[key] = slots[key]

    return {
        "dialogAction": {
            "type": "Delegate",
            "slots": nnslots
        }
    }

def elicit_slot(event, slotToElicit, msg):
    # Elicits slot on error
    slots = event["currentIntent"]["slots"]
    intentName = event["currentIntent"]["name"]

    return {
        "dialogAction": {
            "type": "ElicitSlot",
            "message": {
              "contentType": "PlainText",
              "content": msg
            },
           "intentName": intentName,
           "slots": slots,
           "slotToElicit" : slotToElicit
        }
    }

# Checks (minor)
def check_city(city):
    if city is None:
        return False

    if city.lower() != "manhattan":
        return True

    return False

def check_cuisine(cuisine):
    if cuisine is None:
        return False

    if cuisine.lower() not in ["chinese", "indian", "italian", "japanese", "mexican", "american"]:
        return True

    return False

def check_people(people):
    if people is None:
        return False

    try:
        people_int = int(people)
    except ValueError:
        return True

    if not (0 < people_int < 1000):
        return True

    return False


def check_phone(phone):
    if phone is None:
        return False

    try:
        int(phone)
    except ValueError:
        return True

    if len(phone) != 10:
        return True

    return False

def close():
    # All slots fulfilled
    return{
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": "Fulfilled",
            "message": {"contentType": "PlainText", "content": "You're all set. Expect my suggestions shortly!"}
        }
    }

def lambda_handler(event, context):
    # TODO implement

    # On fulfillment, send to queue and close()
    if event["invocationSource"] == "FulfillmentCodeHook":
        location = event["currentIntent"]["slots"]["Location"]
        cuisine = event["currentIntent"]["slots"]["Cuisine"]
        people = event["currentIntent"]["slots"]["People"]
        time = event["currentIntent"]["slots"]["Time"]
        phone = event["currentIntent"]["slots"]["Phone"]
        main_sqs(location, cuisine, people, time, phone)
        return close()

    # Check params
    if check_city(event["currentIntent"]["slots"]["Location"]):
        return elicit_slot(event, "Location", "Sorry, we don't support this location at this time. Please try again!")

    if check_cuisine(event["currentIntent"]["slots"]["Cuisine"]):
        return elicit_slot(event, "Cuisine", " Sorry, we don't support this cuisine at this time. Please try again!")

    if check_people(event["currentIntent"]["slots"]["People"]):
        return elicit_slot(event, "People", " Sorry, we don't support this number of people at this time. Please try again!")

    if check_phone(event["currentIntent"]["slots"]["Phone"]):
        return elicit_slot(event, "Phone", " Sorry, we don't support this phone number at this time. Please try again!")

    # If no check throws, delegate
    return delegate(event)
