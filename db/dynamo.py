import boto3
from botocore.exceptions import ClientError
from models.player import Player
from decimal import Decimal
from boto3.dynamodb.conditions import Key

class DynamoClient:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name="ca-central-1")
        self.players_table = self.dynamodb.Table('players')
        self.processing_status_table = self.dynamodb.Table('processing_status')
        self.stats_table = self.dynamodb.Table('stats')
        
    def add_player(self, player: Player):
        """Add a player to DynamoDB."""
        try:
            self.players_table.put_item(
                Item={
                    'game_name': player.game_name,
                    'tag_line': player.tag_line,
                    'puuid': player.puuid
                }
            )
        except ClientError as e:
            print(e.response['Error']['Message'])
    
    def remove_player(self, puuid, game_name, tag_line):
        """Remove a player from DynamoDB."""
        try:
            self.players_table.delete_item(
                Key={
                    'game_name': game_name,
                    'tag_line': tag_line
                }
            )
            self.stats_table.delete_item(
                Key={
                    'puuid': puuid
                }
            )
        except ClientError as e:
            print(e.response['Error']['Message'])

    def get_all_players(self):
        """Get all players from DynamoDB as a dictionary."""
        try:
            response = self.players_table.scan()
            items = response.get('Items', [])
            players = {}

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
                    'game_name': game_name,
                    'tag_line': tag_line
                },
                UpdateExpression='SET avg_damage = :val1',
                ExpressionAttributeValues={
                    ':val1': Decimal(str(avg_damage))
                }
            )
        except ClientError as e:
            print(e.response['Error']['Message'])
            return []

    def check_processing_status(self, leaderboard_name):
        """Returns processing status"""
        try:
            response = self.processing_status_table.scan()
            items = response['Items']

            for item in items:
                if item['leaderboard_name'] == leaderboard_name:
                    return items[0].get('processing', False)
            else:
                # If no matching leaderboard_name is found
                return None
        except ClientError as e:
            print(f"Error querying table: {e}")
            return None

