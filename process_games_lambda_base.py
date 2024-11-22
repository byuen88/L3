import json
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal

s3_client = boto3.client('s3')
dynamodb = boto3.client('dynamodb')


def lambda_handler(event, context):
    def set_processing_flag(value):
        """Set the processing flag for all items in the DynamoDB table."""
        try:
            # Scan the table to get all rows
            scan_response = dynamodb.scan(TableName='stats')
            
            # Update the `processing` flag for each item
            for item in scan_response['Items']:
                puuid = item['puuid']['S']
                dynamodb.update_item(
                    TableName='stats',
                    Key={'puuid': {'S': puuid}},
                    UpdateExpression="SET processing = :processing",
                    ExpressionAttributeValues={':processing': {'BOOL': value}}
                )
            print("set processing flag to:" + str(value))
        except ClientError as e:
            print(f"Error updating processing flag: {e}")

    set_processing_flag(True)

    srcBucket = event['Records'][0]['s3']['bucket']['name']
    srcKey = event['Records'][0]['s3']['object']['key']
    bucket_content = s3_client.get_object(Bucket=srcBucket, Key=srcKey)
    
    json_file = bucket_content['Body'].read().decode("utf-8")
    
    data = json.loads(json_file)
    
    # pull all the player puuid from db -> dictionary
    # iterate over json keys (matches), if we find a match with past puuid, update that row
    # else calculate average for newcomer and insert a new row for them
    
    # iterate over the json keys 
    # find person in db, grab avg there and recalc then put back in
    
    key_list = []
    processed_matches = []
    grouped_by_puuid = {}
    
    for key, body in data.items():
        key_list.append(key)
    
    # participant_stat_keys ignores puuid
    participant_stat_keys = ['totalDamageDealtToChampions', 'totalDamageTaken', 'totalTimeSpentDead', 'wardsPlaced']
    challenges_stat_keys = ['kda', 'multikills', 'soloKills', 'takedowns']
    all_stat_keys = participant_stat_keys + challenges_stat_keys
        
    # getting all raw entries    
    for key in key_list:
        for participant in data[key]["info"]["participants"]:
            entry = {"puuid": participant.get("puuid")}
            entry.update({key: participant.get(key, 0) for key in participant_stat_keys})
            entry.update({key: participant["challenges"].get(key, 0) for key in challenges_stat_keys})
        processed_matches.append(entry)
    
    # grouping entries by puuid and getting total along with # of games 
    for entry in processed_matches:
        puuid = entry['puuid']
        if puuid not in grouped_by_puuid:
            grouped_by_puuid[puuid] = {key: 0 for key in all_stat_keys}
            grouped_by_puuid[puuid]["numberOfGames"] = 0
            
        for key in all_stat_keys:
            grouped_by_puuid[puuid][key] += entry[key]

        grouped_by_puuid[puuid]["numberOfGames"] += 1
    
    # calculate averages
    for stats in grouped_by_puuid.values():
        for key in all_stat_keys:
            stats[key] /= stats["numberOfGames"]
            
    # new function that does it all 
    for puuid, stats in grouped_by_puuid.items():
        try:
            # Fetch the existing data from DynamoDB for the current puuid
            response = dynamodb.get_item(
                TableName='stats',
                Key={'puuid': {'S': puuid}}
            )
            
            # Check if the player exists in the database
            if 'Item' in response:
                existing_item = response['Item']
                existing_number_of_games = int(existing_item['numberOfGames']['N']) if 'numberOfGames' in existing_item else 0
                total_games = existing_number_of_games + stats['numberOfGames']
                updated_stats = {}
                
                # For each key, get existing stats from DynamoDB and calculate new values
                for key in all_stat_keys:
                    existing_value = Decimal(existing_item[key]['N']) if key in existing_item else 0
                    new_value = (existing_value * existing_number_of_games + stats[key] * stats['numberOfGames']) / total_games
                    updated_stats[key] = new_value
                
                updated_stats['numberOfGames'] = total_games

                # Update the item in DynamoDB
                update_expression = "SET " + ", ".join(f"{key} = :{key}" for key in updated_stats)
                expression_values = {f":{key}": {'N': str(value)} for key, value in updated_stats.items()}

                dynamodb.update_item(
                    TableName='stats',  
                    Key={'puuid': {'S': puuid}}, 
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_values,
                    ReturnValues="UPDATED_NEW"
                )
            else:
                # If the player does not exist, create new items for them
                item = {key: {'N': str(value)} for key, value in stats.items()}
                item['puuid'] = {'S': puuid}
                item['numberOfGames'] = {'N': str(stats['numberOfGames'])}
                
                # Insert the new player record into DynamoDB
                dynamodb.put_item(TableName='stats', Item=item)
                
        except ClientError as e:
            print(f"Error processing player {puuid}: {e}")

    set_processing_flag(False)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Player stats updated in DynamoDB!')
    }
