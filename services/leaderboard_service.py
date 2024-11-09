from api.riot_api import RiotAPI
from models.player import Player
from services.bucket_services import BucketService
from db.dynamo import DynamoClient
import json
import pickle
import time

class LeaderboardService:
    def __init__(self):
        self.riot_api = RiotAPI()
        self.db = DynamoClient()
        self.leaderboard = self.db.get_all_players()
        self.combined_json = "combined.json"
        self.latest_update_time = "last_update_time"
        self.player_add_delete = False

    def get_leaderboard_players(self):
        """Query the database for all players in the leaderboard."""
        if not self.leaderboard:
            return "Leaderboard is currently empty."

        leaderboard_str = "Current Leaderboard:\n"
        for idx, player in enumerate(self.leaderboard, start=1):
            leaderboard_str += f"{idx}. {player.game_name}#{player.tag_line}\n"
        return leaderboard_str

    def add_player(self, game_name, tag_line):
        """Add a player to the leaderboard."""
        tag_line = tag_line.upper()

        # check for duplicate player
        for player in self.leaderboard:
            if player.game_name == game_name and player.tag_line == tag_line:
                return f"Player {game_name}#{tag_line} is already on the leaderboard."

        puuid = self.riot_api.get_account_by_riot_id(game_name, tag_line).get("puuid")
        player = Player(game_name=game_name, tag_line=tag_line, puuid=puuid)

        # Add to cache
        self.leaderboard.append(player)
        
        # Add to DB
        self.db.add_player(player)
        self.player_add_delete = True
        return f"Player {game_name}#{tag_line} added to leaderboard."

    def remove_player(self, game_name, tag_line):
        """Remove a player from the leaderboard."""
        tag_line = tag_line.upper()
        
        # Remvoe from DB
        self.db.remove_player(game_name, tag_line)
        
        # Remove from cache
        for player in self.leaderboard:
            if player.game_name == game_name and player.tag_line == tag_line:
                self.leaderboard.remove(player)
                return f"Player {game_name}#{tag_line} removed from leaderboard DB."
            
        self.player_add_delete = True
        return f"No player found with name {game_name}#{tag_line} in DB."

    def update_damage(self, match_ids, player: Player):
        """Update total damage dealth over X matches."""
        num_matches = len(match_ids)
        total_damage = 0

        for match_id in match_ids:
            match = self.riot_api.get_match_by_match_id(match_id)
            total_damage += int(match.get("info").get("participants")[0].get("totalDamageDealt"))
        
        avg_damage = total_damage / num_matches
        
        # self.db.update_player_damage(player.game_name, player.tag_line, avg_damage)

        print("Average Damage in past", num_matches, "games: ", avg_damage)
        
    def update_leaderboard(self, start_time, count):
        """Update the leaderboard. Display results to terminal. (for the time being)"""
        print("\nUpdating leaderboard...")
    
        for player in self.leaderboard:
            match_ids = self.riot_api.get_list_of_match_ids_by_puuid(player.puuid, start_time, count)

            self.update_damage(match_ids, player)

    def get_puuids_in_leaderboard(self):
        """return a list of puuids in the leaderboard"""
        puuids = []
        for player in self.leaderboard:
            puuid = self.riot_api.get_account_by_riot_id(player.game_name, player.tag_line).get("puuid")
            puuids.append(puuid)
        return puuids

    def save_last_update_time(self):
        """save the current epoch time as the last update time"""
        with open(self.latest_update_time, 'wb') as f:
            pickle.dump(int(time.time()), f)

    def get_last_update_time(self):
        """get the last updated epoch time"""
        try:
            with open(self.latest_update_time,'rb') as f:
                last_update_time=pickle.load(f)
        except:
            last_update_time = ""
        return last_update_time

    def combine_matches(self):
        """get matches of all players in leaderboard since the last update, combine them into a single json file, and upload file to S3 bucket"""
        combined = {}
        # check if there are any additions or deletions of player
        if self.player_add_delete:
            last_update_time = ""
            self.player_add_delete = False
        else:
            last_update_time = self.get_last_update_time()

        puuids = self.get_puuids_in_leaderboard()
        for puuid in puuids:
            # get matches since the last update
            match_ids = self.riot_api.get_list_of_match_ids_by_puuid(puuid, start_time=last_update_time, count=3)      # TODO: count=3 for now to save space
            for match_id in match_ids:
                match = self.riot_api.get_match_by_match_id(match_id)
                # shorten the json to only relevant participants info
                match["info"]["participants"] = [
                    participant for participant in match["info"]["participants"] if participant["puuid"] in puuids
                ]
                if match_id not in combined:
                    combined[match_id] = match
        if combined:
            with open(self.combined_json, "w") as f:
                json.dump(combined,f)
            # upload json to S3
            BucketService().upload_file(self.combined_json, self.combined_json)
        else:
            print("\nAll games are up-to-date.")

        self.save_last_update_time()