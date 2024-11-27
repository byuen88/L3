
from models.player import Player
from services.bucket_services import BucketService
from db.db_query import get_all_player_stats_from_dynamodb
from db.db_constants import DynamoDBTables
import asyncio
import json
import pickle
import time
import os
import traceback

class LeaderboardService:
    def __init__(self, leaderboard_name, riot_api, db):
        self.riot_api = riot_api
        self.db = db
        self.leaderboard = self.db.get_all_players()
        self.ec2_volume = "/app/data/"
        self.combined_json = "combined.json"
        self.latest_update_time = "last_update_time"
        self.player_add_delete = False
        self.update_lock = asyncio.Lock()  # Lock for single-process control
        self.cooldown = 120  # Cooldown period in seconds
        self.leaderboard_name = leaderboard_name

    def view_leaderboard(self, metric_to_sort):
        """Query database for calculated statistics and display based on specified order"""
        data = get_all_player_stats_from_dynamodb()

        if not data or len(data) == 0:
            print("No statistics to show")
            return

        sort_idx = -1
        if (metric_to_sort == DynamoDBTables.StatsTable.KDA):
            sort_idx = 1
        elif (metric_to_sort == DynamoDBTables.StatsTable.CS_PER_MIN):
            sort_idx = 2
        elif (metric_to_sort == DynamoDBTables.StatsTable.DAMAGE_RECORD):
            sort_idx = 3
        elif (metric_to_sort == DynamoDBTables.StatsTable.AVERAGE_DAMAGE_DEALT_TO_CHAMPIONS):
            sort_idx = 4
        elif (metric_to_sort == DynamoDBTables.StatsTable.AVERAGE_GOLD_EARNED):
            sort_idx = 5   
        elif (metric_to_sort == DynamoDBTables.StatsTable.AVERAGE_TIME_SPENT_DEAD):
            sort_idx = 6   

        if (sort_idx == -1):
            print("Sorting on incorrect metric")
            return

        sorted_data = sorted(
            [(
                item["puuid"],
                item[DynamoDBTables.StatsTable.KDA],
                item[DynamoDBTables.StatsTable.CS_PER_MIN],
                item[DynamoDBTables.StatsTable.DAMAGE_RECORD],
                item[DynamoDBTables.StatsTable.AVERAGE_DAMAGE_DEALT_TO_CHAMPIONS],
                item[DynamoDBTables.StatsTable.AVERAGE_GOLD_EARNED],
                item[DynamoDBTables.StatsTable.AVERAGE_TIME_SPENT_DEAD],
              ) for item in data],
            key=lambda x: x[sort_idx],  # Sort by the metric value
            reverse=True
        )

        # Find the longest player name for consistent formatting
        longest_name_length = max(
            len(f"{self.leaderboard.get(item[0]).game_name}#{self.leaderboard.get(item[0]).tag_line}")
            for item in sorted_data if self.leaderboard.get(item[0])
        )

        count = 1
        # Column widths for consistent formatting
        long_width = 17
        medium_width = 10
        short_width = 5

        # Display leaderboard header
        print(
            f"{'Player':<{longest_name_length + 4}} | "
            f"{'KDA':<{short_width}} | "
            f"{'CS/min':<{medium_width}} | "
            f"{'Damage Record':<{long_width}} | "
            f"{'AVG Damage':<{medium_width}} | "
            f"{'AVG Gold':<{medium_width}} | "
            f"{'AVG Time Dead (s)':<{long_width}} | "
        )
        print("-" * (longest_name_length + 4 + short_width + medium_width + long_width + medium_width + medium_width + long_width + 20))

        # Display leaderboard rows
        for puuid, kda, cs, damage_record, avg_dmg, avg_gold, avg_dead in sorted_data:
            player = self.leaderboard.get(puuid)

            if player:  # Ensure player exists
                name = f"{player.game_name}#{player.tag_line}"
                if count < 10:
                    print(
                        f"{count}) {name:<{longest_name_length + 1}} | "
                        f"{round(kda, 2):<{short_width}} | "
                        f"{round(cs, 2):<{medium_width}} | "
                        f"{round(damage_record, 0):<{long_width}} | "
                        f"{round(avg_dmg, 0):<{medium_width}} | "
                        f"{round(avg_gold, 0):<{medium_width}} | "
                        f"{round(avg_dead, 0):<{long_width}} | "
                    )
                else:
                    print(
                        f"{count}) {name:<{longest_name_length}} | "
                        f"{round(kda, 2):<{short_width}} | "
                        f"{round(cs, 2):<{medium_width}} | "
                        f"{round(damage_record, 0):<{long_width}} | "
                        f"{round(avg_dmg, 0):<{medium_width}} | "
                        f"{round(avg_gold, 0):<{medium_width}} | "
                        f"{round(avg_dead, 0):<{long_width}} | "
                    )
                count += 1

    def get_leaderboard_players(self):
        """Query the database for all players in the leaderboard."""
        if not self.leaderboard:
            return "Leaderboard is currently empty."

        leaderboard_str = "Current Leaderboard:\n"
        for idx, player in enumerate(self.leaderboard.values(), start=1):
            leaderboard_str += f"{idx}. {player.game_name}#{player.tag_line}\n"
        return leaderboard_str

    async def add_player(self, game_name, tag_line):
        """Add a player to the leaderboard."""
        self.leaderboard = self.db.get_all_players()
        tag_line = tag_line.upper()

        # check for duplicate player
        for player in self.leaderboard.values():
            if player.game_name.upper() == game_name.upper() and player.tag_line == tag_line:
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
        self.leaderboard[player.puuid] = player

        # Add to DB
        self.db.add_player(player)
        self.player_add_delete = True

        await self.combine_matches()

        return f"Player {game_name}#{tag_line} added to leaderboard."

    def remove_player(self, game_name, tag_line):
        """Remove a player from the leaderboard."""
        self.leaderboard = self.db.get_all_players()
        tag_line = tag_line.upper()

        for player in self.leaderboard.values():
            if player.game_name.upper() == game_name.upper() and player.tag_line == tag_line:
                # Remove from DB
                self.db.remove_player(player.puuid, game_name, tag_line)
                # Remove from cache
                self.leaderboard.pop(player.puuid)
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

        puuids = list(self.leaderboard.keys())
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
        except Exception as e:
            print(f"\nAn error occurred while processing matches: {e}")
            traceback.print_exc()

        self.save_last_update_time()
        