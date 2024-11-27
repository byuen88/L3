import json
import boto3
from botocore.exceptions import ClientError

s3_client = boto3.client('s3')
dynamodb = boto3.client('dynamodb')


def lambda_handler(event, context):
    def set_processing_flag(value):
        """Set the processing status tables."""
        try:
            print(f"attempting to change processing flag")
            # Use PutItem to create or update the row with the partition key "main_table"
            dynamodb.put_item(
                TableName='processing_status',
                Item={
                    'leaderboard_name': {'S': 'main_table'},
                    'processing': {'BOOL': value}
                }
            )
            print(f"Set processing flag to: {value} in 'processing_status' table.")
        except ClientError as e:
            print(f"Error updating processing flag: {e}")
            
    print(f"starting up Lambda...")
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
    participant_stat_keys = ['totalDamageDealtToChampions', 'totalDamageTaken', 'totalTimeSpentDead', 'wardsPlaced', 'goldEarned']
    challenges_stat_keys = ['kda', 'soloKills', 'takedowns']
    calculated_stat_keys = ['csPerMin', 'damageDealtToChampionsRecord']
    all_stat_keys = participant_stat_keys + challenges_stat_keys + calculated_stat_keys
    
    damageRecord = 0

    # getting all raw entries    
    for key in key_list:
        for participant in data[key]["info"]["participants"]:
            # Calcuate cs per min
            timePlayed = participant.get("timePlayed", 1)
            minionsKilled = participant.get("totalMinionsKilled")
            csPerMin = minionsKilled / timePlayed * 60
            
            damageRecord = participant.get("totalDamageDealtToChampions")

            entry = {"puuid": participant.get("puuid"), "csPerMin": csPerMin, "damageDealtToChampionsRecord": damageRecord}
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
            grouped_by_puuid[puuid][key] += entry.get(key, 0)

        grouped_by_puuid[puuid]["numberOfGames"] += 1
    
    # calculate averages
    for stats in grouped_by_puuid.values():
        for key in all_stat_keys:
            if key != 'damageDealtToChampionsRecord':
                stats[key] = stats[key] / stats["numberOfGames"] if stats["numberOfGames"] > 0 else 0
            
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
                
                # For each key, get existing stats from DynamoDB, calculate and round new values
                for key in all_stat_keys:
                    existing_value = float(existing_item[key]['N']) if key in existing_item else 0
                    new_value = (existing_value * existing_number_of_games + stats[key] * stats['numberOfGames']) / total_games
                    updated_stats[key] = round(new_value, 2)
                
                # Get max damage record
                existing_damage_record = float(existing_item['damageDealtToChampionsRecord']['N']) if 'damageDealtToChampionsRecord' in existing_item else 0
                updated_stats['damageDealtToChampionsRecord'] = round(max(damageRecord, existing_damage_record), 2)
                
                updated_stats['numberOfGames'] = total_games

                # Update the item in DynamoDB
                update_expression = "SET " + ", ".join(f"{key} = :{key}" for key in updated_stats)
                expression_values = {f":{key}": {'N': str(round(value, 2))} for key, value in updated_stats.items()}

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
