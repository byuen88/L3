from api.riot_api import RiotAPI
from models.player import Player
from services.bucket_services import BucketService
import json
import pickle
import time

class LeaderboardService:
    def __init__(self):
        self.riot_api = RiotAPI()
        self.leaderboard = []
        self.combined_json = "combined.json"
        self.latest_update_time = "start_time"

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
        player = Player(game_name=game_name, tag_line=tag_line)
        self.leaderboard.append(player)
        return f"Player {game_name}#{tag_line} added to leaderboard."

    def remove_player(self, game_name, tag_line):
        """Remove a player from the leaderboard."""
        for player in self.leaderboard:
            if player.game_name == game_name and player.tag_line == tag_line:
                self.leaderboard.remove(player)
                return f"Player {game_name}#{tag_line} removed from leaderboard."
        return f"No player found with name {game_name}#{tag_line}."

    def update_leaderboard(self, start_time, count):
        """Update the leaderboard. Display results to terminal. (for the time being)"""
        print("\nUpdating leaderboard...")
        for player in self.leaderboard:
            puuid = self.riot_api.get_account_by_riot_id(player.game_name, player.tag_line).get("puuid")

            match_ids = self.riot_api.get_list_of_match_ids_by_puuid(puuid, start_time, count)

            num_matches = len(match_ids)
            total_damage = 0

            for match_id in match_ids:
                match = self.riot_api.get_match_by_match_id(match_id)
                total_damage += int(match.get("info").get("participants")[0].get("totalDamageDealt"))

            print("Average Damage in past", num_matches, "games: ", total_damage/ num_matches)

    def get_puuids_in_leaderboard(self):
        """return a list of puuids in the leaderboard"""
        puuids = []
        for player in self.leaderboard:
            puuid = self.riot_api.get_account_by_riot_id(player.game_name, player.tag_line).get("puuid")
            puuids.append(puuid)
        return puuids

    def update(self):
        """update to the current epoch time"""
        with open(self.latest_update_time, 'wb') as f:
            pickle.dump(int(time.time()), f)

    def combine_matches(self):
        """get matches of all players in leaderboard since the last update, combine them into a single json file, and upload file to S3 bucket"""
        combined = {}

        try:
            with open(self.latest_update_time,'rb') as f:
                start_time=pickle.load(f)
        except:
            start_time = ""

        puuids = self.get_puuids_in_leaderboard()
        for puuid in puuids:
            # get matches since the last update
            match_ids = self.riot_api.get_list_of_match_ids_by_puuid(puuid, start_time, 3)              # TODO: count=3 for now to save space
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

        self.update()
        with open(self.latest_update_time,'rb') as f:
            start_time=pickle.load(f)