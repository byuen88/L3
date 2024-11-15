from api.riot_api import RiotAPI
from models.player import Player
from services.bucket_services import BucketService
from db.dynamo import DynamoClient
import asyncio
import json
import pickle
import time
import os

class LeaderboardService:
    def __init__(self):
        self.riot_api = RiotAPI()
        self.db = DynamoClient()
        self.leaderboard = self.db.get_all_players()
        self.ec2_volume = "/app/data/"
        self.combined_json = "combined.json"
        self.latest_update_time = "last_update_time"
        self.player_add_delete = False
        self.update_lock = asyncio.Lock()  # Lock for single-process control
        self.cooldown = 120  # Cooldown period in seconds

    def get_leaderboard_players(self):
        """Query the database for all players in the leaderboard."""
        if not self.leaderboard:
            return "Leaderboard is currently empty."

        leaderboard_str = "Current Leaderboard:\n"
        for idx, player in enumerate(self.leaderboard, start=1):
            leaderboard_str += f"{idx}. {player.game_name}#{player.tag_line}\n"
        return leaderboard_str

    def get_puuids_in_leaderboard(self):
        """return a list of puuids in the leaderboard"""
        puuids = []
        for player in self.leaderboard:
            puuids.append(player.puuid)
        return puuids

    async def add_player(self, game_name, tag_line):
        """Add a player to the leaderboard."""
        tag_line = tag_line.upper()

        # check for duplicate player
        for player in self.leaderboard:
            if player.game_name == game_name and player.tag_line == tag_line:
                return f"Player {game_name}#{tag_line} is already on the leaderboard."

        try:
            response = await self.riot_api.get_account_by_riot_id(game_name, tag_line)
            puuid = response.get("puuid")
            if not puuid:
                return "Player does not exist."
        except:
            return "Player does not exist."

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
        
        # Remove from DB
        self.db.remove_player(game_name, tag_line)
        
        # Remove from cache
        for player in self.leaderboard:
            if player.game_name == game_name and player.tag_line == tag_line:
                self.leaderboard.remove(player)
                return f"Player {game_name}#{tag_line} removed from leaderboard DB."

        self.player_add_delete = True
        return f"No player found with name {game_name}#{tag_line} in DB."

    async def update_leaderboard(self, start_time, count):
        """Update leaderboard stats if the cooldown has passed."""
        current_time = time.time()
        if current_time - self.get_last_update_time() < self.cooldown:
            print("Cooldown active. Skipping redundant update.")
            return

        async with self.update_lock:  # Ensure only one update at a time
            print("Updating leaderboard...")
            for player in self.leaderboard:
                await self.update_player_stats(player, start_time, count)
            self.save_last_update_time()

    async def update_player_stats(self, player, start_time, count):
        """Fetch and update stats for a player."""
        # Fetch recent match IDs
        match_ids = await self.riot_api.get_list_of_match_ids_by_puuid(player.puuid, start_time, count)
        await self.update_damage(match_ids, player)

    async def update_damage(self, match_ids, player: Player):
        """Update total damage dealt over X matches."""
        num_matches = len(match_ids)
        total_damage = 0

        for match_id in match_ids:
            match = await self.riot_api.get_match_by_match_id(match_id)
            damage = int(match["info"]["participants"][0].get("totalDamageDealt", 0))
            total_damage += damage
        
        avg_damage = total_damage / num_matches
        
        # self.db.update_player_damage(player.game_name, player.tag_line, avg_damage)

        print("Average Damage in past", num_matches, "games: ", avg_damage)

    def get_file_path(self, filename):
        """get the file_path depending if the application is ran locally or inside Docker"""
        if os.path.exists(self.ec2_volume):
            # Inside Docker, use the mounted directory path
            base_path = self.ec2_volume
        else:
            # Running locally, use current directory
            base_path = "."
        return os.path.join(base_path, filename) 

    def save_last_update_time(self):
        """save the current epoch time as the last update time"""
        latest_update_time = self.get_file_path(self.latest_update_time)
        with open(latest_update_time, 'wb') as f:
            pickle.dump(int(time.time()), f)

    def get_last_update_time(self):
        """get the last updated epoch time"""
        try:
            latest_update_time = self.get_file_path(self.latest_update_time)
            with open(latest_update_time,'rb') as f:
                last_update_time=pickle.load(f)
        except:
            last_update_time = ""
        return last_update_time

    async def combine_matches(self):
        """get matches of all players in leaderboard since the last update, combine them into a single json file, and upload file to S3 bucket"""
        combined = {}
        # check if there are any additions or deletions of player
        if self.player_add_delete:
            last_update_time = ""
            self.player_add_delete = False
        else:
            last_update_time = self.get_last_update_time()

        puuids = self.get_puuids_in_leaderboard()
        try:
            for puuid in puuids:
                # get matches since the last update
                match_ids = await self.riot_api.get_list_of_match_ids_by_puuid(puuid, start_time=last_update_time,
                                                                               count=3)  # TODO: count=3 for now to save space
                for match_id in match_ids:
                    match = await self.riot_api.get_match_by_match_id(match_id)
                    # shorten the json to only relevant participants info
                    match["info"]["participants"] = [
                        participant for participant in match["info"]["participants"] if participant["puuid"] in puuids
                    ]
                    if match_id not in combined:
                        combined[match_id] = match
            if combined:
                combined_json = self.get_file_path(self.combined_json)
                with open(combined_json, "w") as f:
                    json.dump(combined, f)
                # upload json to S3
                BucketService().upload_file(combined_json, self.combined_json)
            else:
                print("\nAll games are up-to-date.")
        except:
            print("\nAN error occurred")


        self.save_last_update_time()