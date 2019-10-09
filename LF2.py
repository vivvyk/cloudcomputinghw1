import json
import boto3
import time
import elasticsearch
import certifi
import random

def lambda_handler(event, context):

    # Pull mesage from queue
    queue_client = boto3.client('sqs')
    queue_response = queue_client.receive_message(
        QueueUrl='https://sqs.us-east-1.amazonaws.com/239851179186/Q1'
    )

    if "Messages" not in queue_response.keys():
        return {
            'statusCode': 400,
             # 'body': text_message
             'body': "No message in Queue"
        }

    # Delete message from queue and extract information
    queue_message = queue_response["Messages"][0]
    receipt = queue_message["ReceiptHandle"]
    message = json.loads(queue_message["Body"])

    queue_client.delete_message(
        QueueUrl='https://sqs.us-east-1.amazonaws.com/239851179186/Q1',
        ReceiptHandle=receipt
    )

    # Message info
    location = message["location"].lower()
    cuisine = message["cuisine"].lower()
    time = message["time"]
    people = message["people"]
    phone = message["number"]

    # ElasticSearch lookup and random selection
    es = elasticsearch.Elasticsearch("https://search-restaurants-iup6gzge45fgfeuz4vkpiktqq4.us-east-1.es.amazonaws.com", use_ssl=True, ca_certs=certifi.where())
    res = es.search(index="restaurants", body={"query": {"match": {"cuisine":cuisine}}}, size=1000)
    restaurant_items = random.sample(res['hits']['hits'], 3)

    restaurant_ids = [d['_source']['restaurant_ID'] for d in restaurant_items]

    # Look up restaurants in Dynamodb
    db_client = boto3.client('dynamodb')

    restaurant_rows = []
    for _id in restaurant_ids:
        db_response = db_client.get_item(
            TableName='yelp-restaurants',
            Key={
                "restaurant_ID": {"S": _id}
            },
        )

        restaurant_rows.append(db_response['Item'])

    # Construct text message
    text_message = "Hi! I have some {} restaurant suggestions for {} people at {}!\n\n".format(cuisine, people, time)

    for i, restaurant in enumerate(restaurant_rows):
        rest_rev = "{}. {} located at {}, which is rated {} stars with {} reviews.\n\n".format(i+1, restaurant['name']['S'],
                                                                        restaurant['address']['S'], restaurant['rating']['N'], restaurant['num_reviews']['N'])
        text_message += rest_rev


    # Send text message
    sns_client = boto3.client('sns')
    sns_client.publish(
        PhoneNumber="+1" + phone,
        Message=text_message,
        Subject='Dining Recommendations'
    )

    return {
        'statusCode': 200,
         'body': text_message
    }
