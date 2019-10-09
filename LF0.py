import json
import boto3
import time

def lambda_handler(event, context):
    lex_client = boto3.client('lex-runtime')

    # Send response to lex
    response = lex_client.post_text(
        botName='ConciergeBot',
        botAlias='waiter',
        userId= "vk2425prod",
        inputText=event["message"]
    )

    return {
        'statusCode': 200,
        'body': json.dumps(response["message"])
    }
