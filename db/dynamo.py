import boto3
from botocore.exceptions import ClientError
from models.player import Player

class DynamoClient:
    def __init__(self, table_name='players'):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
        
    def add_player(self, player: Player):
        """Add a player to DynamoDB."""
        try:
            self.table.put_item(
                Item={
                    'game_name': player.game_name,
                    'tag_line': player.tag_line
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
        """Get all players from DynamoDB."""
        try:
            response = self.table.scan()
            items = response.get('Items', [])
            players = []
            
            for item in items:
                game_name = item.get('game_name')
                tag_line = item.get('tag_line')
                player = Player(game_name=game_name, tag_line=tag_line)
                players.append(player)
            
            return players
        except ClientError as e:
            print(e.response['Error']['Message'])
            return []