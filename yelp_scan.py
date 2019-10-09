import boto3
from yelpapi import YelpAPI
from pprint import pprint
import time
from decimal import *
import json

def process_reponse(res):
    '''
    (Requirements: Business ID, Name, Address, Coordinates,
    Number of Reviews, Rating, Zip Code)
    '''
    
    bus_items = []
    
    for business in res['businesses']:
        item = {}
        item['restaurant_ID'] = business['id']
        item['name'] = business['name']
        item['rating'] = Decimal(str(business['rating']))
        item['num_reviews'] = business['review_count']
        
        item['longitude'] = Decimal(str(business['coordinates']['longitude']))
        item['latitude'] = Decimal(str(business['coordinates']['latitude']))
        
        item['address'] = " ".join(business['location']['display_address'])

        bus_items.append(item)
    
    return bus_items
    
def put_record(table, item, cuisine):
    # Put record in database
    item['insertedAtTimestamp'] = Decimal(str(time.time()))
    item['cuisine'] = cuisine
    table.put_item(
       Item=item
    )
    
def write_elastic_search_index(f, cuisine, ID, _id):
    # Writes elasticfusion json record
    json.dump({ "index" : { "_index": "restaurants", "_type" : "_doc", "_id" : _id } }, f)
    f.write('\n')
    json.dump({"type":"Restaurant", "cuisine":cuisine, "restaurant_ID":ID}, f)
    f.write('\n')

if __name__ == "__main__":
    API_KEY = "xklrWoHqNLUrNXkJlOYPXdK6w4V--bWFCa2o7hdazBxMJ1an4ESzfbgAI_SHH2wa1g0wQmpEha9BiY3_aPyOkbWqn2YODLSrLx3H0_ZJuH-2HI_D8Gh5xmCJZQ2ZXXYx"
    yelp_api = YelpAPI(API_KEY)
    
    elastic_out_file = open("bulk_restaurants.json", "w")
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('yelp-restaurants')
    
    cuisines = ["chinese", "indian", "italian", "mexican", "american", "japanese"]
    
    # Queries and processes all records.
    LIMIT = 50
    _id = 1
    for cuisine in cuisines:
        OFFSET = 0
        print("Cuisine: " + cuisine)
        while OFFSET < 1000:
            response = process_reponse(yelp_api.search_query(term=cuisine, location='Manhattan', limit=LIMIT, offset=OFFSET))
            
            for res in response:
                put_record(table, res, cuisine)
                write_elastic_search_index(elastic_out_file, cuisine, res['restaurant_ID'], _id)
                _id += 1
            
            OFFSET += LIMIT
            print(OFFSET)
        
        print('Completed!\n')