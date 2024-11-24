import boto3
from botocore.exceptions import ClientError
from models.player import Player
from decimal import Decimal

class DynamoClient:
    def __init__(self, table_name='players'):
        self.dynamodb = boto3.resource('dynamodb', region_name="ca-central-1")
        self.table = self.dynamodb.Table(table_name)
        
    def add_player(self, player: Player):
        """Add a player to DynamoDB."""
        try:
            self.table.put_item(
                Item={
                    'game_name': player.game_name,
                    'tag_line': player.tag_line,
                    'puuid': player.puuid
                }
            )
            print(f"Player {player.game_name}#{player.tag_line} added to DynamoDB.")
        except ClientError as e:
            print(e.response['Error']['Message'])
    
    def remove_player(self, game_name, tag_line):
        """Remove a player from DynamoDB."""
        try:
            self.table.delete_item(
                Key={
                    'game_name': game_name,
                    'tag_line': tag_line
                }
            )
            print(f"Player {game_name}#{tag_line} removed from DynamoDB.")
        except ClientError as e:
            print(e.response['Error']['Message'])

    def get_all_players(self):
        """Get all players from DynamoDB as a dictionary."""
        try:
            response = self.table.scan()
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
            self.table.update_item(
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