import boto3
import json
from decimal import Decimal

# Custom JSON encoder
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

def get_all_player_stats_from_dynamodb():
    dynamodb = boto3.resource('dynamodb', region_name='ca-central-1')  
    table = dynamodb.Table('stats')

    try:
        response = table.scan()
        data = response['Items']
        
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            data.extend(response['Items'])

        return data

    except Exception as e:
        print(f"Error retrieving data: {e}")
        return None