import boto3
from botocore.exceptions import ClientError
from models.player import Player
from decimal import Decimal
from collections import OrderedDict
from db.db_constants import DynamoDBTables
import os

class DynamoClient:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name=os.getenv("REGION_NAME"))
        self.players_table = self.dynamodb.Table(DynamoDBTables.PlayersTable.TABLE_NAME)
        self.processing_status_table = self.dynamodb.Table(DynamoDBTables.ProcessingStatusTable.TABLE_NAME)
        self.stats_table = self.dynamodb.Table(DynamoDBTables.StatsTable.TABLE_NAME)
        
    def add_player(self, player: Player):
        """Add a player to DynamoDB."""
        try:
            self.players_table.put_item(
                Item={
                    DynamoDBTables.PlayersTable.GAME_NAME: player.game_name,
                    DynamoDBTables.PlayersTable.TAG_LINE: player.tag_line,
                    DynamoDBTables.PlayersTable.PUUID: player.puuid
                }
            )
        except ClientError as e:
            print(e.response['Error']['Message'])
    
    def remove_player(self, puuid, game_name, tag_line):
        """Remove a player from DynamoDB."""
        try:
            self.players_table.delete_item(
                Key={
                    DynamoDBTables.PlayersTable.GAME_NAME: game_name,
                    DynamoDBTables.PlayersTable.TAG_LINE: tag_line
                }
            )
            self.stats_table.delete_item(
                Key={
                    DynamoDBTables.StatsTable.PUUID: puuid
                }
            )
        except ClientError as e:
            print(e.response['Error']['Message'])

    def get_all_players(self):
        """Get all players from DynamoDB as a dictionary."""
        try:
            response = self.players_table.scan()
            items = response.get('Items', [])
            players = OrderedDict()

            for item in items:
                player = Player(**item)
                players[player.puuid] = player  # Use `puuid` as the dictionary key

            return players
        except ClientError as e:
            print(e.response['Error']['Message'])
            return {}

    def update_player_damage(self, game_name, tag_line, avg_damage):
        """Update a player's information in DB."""
        try:
            self.players_table.update_item(
                Key={
                    DynamoDBTables.PlayersTable.GAME_NAME: game_name,
                    DynamoDBTables.PlayersTable.TAG_LINE: tag_line
                },
                UpdateExpression='SET avg_damage = :val1',
                ExpressionAttributeValues={
                    ':val1': Decimal(str(avg_damage))
                }
            )
        except ClientError as e:
            print(e.response['Error']['Message'])
            return []

    def get_all_player_stats_from_dynamodb(self):
        try:
            response = self.stats_table.scan()
            data = response['Items']

            while 'LastEvaluatedKey' in response:
                response = self.stats_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                data.extend(response['Items'])

            return data

        except Exception as e:
            print(f"Error retrieving data: {e}")
            return None

    def check_processing_status(self, leaderboard_name):
        """Returns processing status"""
        try:
            response = self.processing_status_table.scan()
            items = response['Items']

            for item in items:
                if item[DynamoDBTables.ProcessingStatusTable.LEADERBOARD_NAME] == leaderboard_name:
                    return items[0].get(DynamoDBTables.ProcessingStatusTable.PROCESSING, False)
            else:
                # If no matching leaderboard_name is found
                return None
        except ClientError as e:
            print(f"Error querying table: {e}")
            return None

