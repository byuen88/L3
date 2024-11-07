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
        self.combined = {}

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
        f=open('start_time', 'wb')
        pickle.dump(int(time.time()),f)
    

    def combine_matches(self):
        """get the matches of all players in leaderboard since the last update, and combine them into a single json file"""
        try:
            f=open('start_time','rb')
            start_time=pickle.load(f)
        # first ever time running the application
        except:
            start_time = ""

        puuids = self.get_puuids_in_leaderboard()
        for puuid in puuids:
            # get matches since the last update
            if not start_time:
                match_ids = self.riot_api.get_list_of_match_ids_by_puuid(puuid, count=3)                #TODO: count=3 for now to save space
            else:
                match_ids = self.riot_api.get_list_of_match_ids_by_puuid(puuid, start_time, count=3)    #TODO: count=3 for now to save space

            for match_id in match_ids:
                match = self.riot_api.get_match_by_match_id(match_id)
                # shorten the match json to only relevant participants
                match["info"]["participants"] = [
                    participant for participant in match["info"]["participants"] if participant["puuid"] in puuids
                ]
                if match_id not in self.combined:
                    self.combined[match_id] = match

        if self.combined:
            with open("combined.json", "w") as f:
                json.dump(self.combined,f)

            bucket = BucketService()
            bucket.upload_file('combined.json', 'combined.json')
        else:
            print("\nYou already have the most updated games")

        self.update()