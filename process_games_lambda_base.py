import json
import boto3
import datetime
from botocore.exceptions import ClientError

s3_client = boto3.client('s3')
dynamodb = boto3.client('dynamodb')


def lambda_handler(event, context):
    srcBucket = event['Records'][0]['s3']['bucket']['name']
    srcKey = event['Records'][0]['s3']['object']['key']
    bucket_content = s3_client.get_object(Bucket=srcBucket, Key=srcKey)
    #print("Params: srcBucket: " + srcBucket + " srcKey: " + srcKey + "\n");
    #print("this is the contents: ")
    #print(bucket_content)
    
    json_file = bucket_content['Body'].read().decode("utf-8")
    
    #print("this is the type:" + "\n")
    #print(type(json_file))
    #print("this is the body:" + "\n")
    #print(json_file)
    
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
        
    # getting all raw entries    
    for key in key_list:
        print("Key: " + key)
        for participant in data[key]["info"]["participants"]:
            entry = {
                "puuid": participant.get("puuid"),
                "kda": participant["challenges"].get("kda"),
                "totalDamageDealtToChampions": participant.get("totalDamageDealtToChampions")
            }
        processed_matches.append(entry)
        
    #print(processed_matches)
    
    # grouping entries by puuid and getting total along with # of games 
    for entry in processed_matches:
        print("entry: " + entry['puuid'] + " " + str(entry['kda']) + " " + str(entry['totalDamageDealtToChampions']) + "\n")
        # new entry 
        if entry['puuid'] not in grouped_by_puuid:
            grouped_by_puuid[entry['puuid']] = {"kda": 0, "totalDamageDealtToChampions": 0, "numberOfGames": 0}
        
        grouped_by_puuid[entry['puuid']]["kda"] += (entry['kda'])
        grouped_by_puuid[entry['puuid']]["totalDamageDealtToChampions"] += (entry['totalDamageDealtToChampions'])
        grouped_by_puuid[entry['puuid']]["numberOfGames"] += 1
            
        
    #print(grouped_by_puuid)
    
    # calculate averages
    for puuid, stats in grouped_by_puuid.items():
        stats["kda"] /= stats["numberOfGames"]
        stats["totalDamageDealtToChampions"] /= stats["numberOfGames"]
        
    #print(grouped_by_puuid)
            
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
                
                # Get existing stats from DynamoDB
                existing_kda = float(existing_item['kda']['N']) if 'kda' in existing_item else 0
                existing_total_damage = float(existing_item['totalDamageDealtToChampions']['N']) if 'totalDamageDealtToChampions' in existing_item else 0
                existing_number_of_games = int(existing_item['numberOfGames']['N']) if 'numberOfGames' in existing_item else 0
                
                # Recalculate new values
                total_games = existing_number_of_games + stats['numberOfGames']
                new_kda = (existing_kda * existing_number_of_games + stats['kda'] * stats['numberOfGames']) / total_games
                new_total_damage = (existing_total_damage * existing_number_of_games + stats['totalDamageDealtToChampions'] * stats['numberOfGames']) / total_games
                
                # Update the item in DynamoDB
                update_response = dynamodb.update_item(
                    TableName='stats',  
                    Key={'puuid': {'S': puuid}}, 
                    UpdateExpression="SET kda = :kda, totalDamageDealtToChampions = :totalDamageDealtToChampions, numberOfGames = :numberOfGames",
                    ExpressionAttributeValues={
                        ':kda': {'N': str(new_kda)},
                        ':totalDamageDealtToChampions': {'N': str(new_total_damage)},
                        ':numberOfGames': {'N': str(total_games)}
                    },
                    ReturnValues="UPDATED_NEW"
                )
                #print(f"Updated player {puuid} with new stats: kda={new_kda}, totalDamageDealt={new_total_damage}, numberOfGames={total_games}")
            
            else:
                # If the player does not exist, insert them
                new_kda = stats['kda']
                new_total_damage = stats['totalDamageDealtToChampions']
                total_games = stats['numberOfGames']
                
                # Insert the new player record into DynamoDB
                insert_response = dynamodb.put_item(
                    TableName='stats',
                    Item={
                        'puuid': {'S': puuid},
                        'kda': {'N': str(new_kda)},
                        'totalDamageDealtToChampions': {'N': str(new_total_damage)},
                        'numberOfGames': {'N': str(total_games)}
                    }
                )
                # print(f"Inserted new player {puuid} with stats: kda={new_kda}, totalDamageDealt={new_total_damage}, numberOfGames={total_games}")
                
        except ClientError as e:
            print(f"Error processing player {puuid}: {e}")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Player stats updated in DynamoDB!')
    }
