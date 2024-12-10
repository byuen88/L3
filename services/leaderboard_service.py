
from models.player import Player
from services.bucket_services import BucketService
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
        self.update_lock = asyncio.Lock()  # Lock for single-process control
        self.cooldown = 120  # Cooldown period in seconds
        self.leaderboard_name = leaderboard_name

    def is_leaderboard_empty(self):
        self.leaderboard = self.db.get_all_players()
        return not self.leaderboard

    def view_leaderboard(self, metric_to_sort):
        """Query database for calculated statistics and display based on specified order"""
        data = self.db.get_all_player_stats_from_dynamodb()

        if not data or len(data) == 0:
            print("No statistics to show")
            return []

        sort_idx = self._get_sort_index(metric_to_sort)
        if sort_idx == -1:
            print("Sorting on incorrect metric")
            return []
        
        sorted_data = self._sort_data(data, sort_idx)

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

        # ============================= Display leaderboard in CLI =============================
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
        leaderboard = []
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
                # ============================= build and return leaderabord for front-end =============================
                leaderboard.append({
                    "puuid": player.puuid,
                    "game_name": player.game_name,
                    "tag_line": player.tag_line,
                    "kda": kda,
                    "cs_per_min": cs,
                    "damage_record": damage_record,
                    "avg_damage": avg_dmg,
                    "avg_gold": avg_gold,
                    "avg_time_dead": avg_dead
                })

        return leaderboard

    def _get_sort_index(self, metric_to_sort):
        """Get the index to sort the data by the specified metric"""
        sort_indices = {
            DynamoDBTables.StatsTable.KDA: 1,
            DynamoDBTables.StatsTable.CS_PER_MIN: 2,
            DynamoDBTables.StatsTable.DAMAGE_RECORD: 3,
            DynamoDBTables.StatsTable.AVERAGE_DAMAGE_DEALT_TO_CHAMPIONS: 4,
            DynamoDBTables.StatsTable.AVERAGE_GOLD_EARNED: 5,
            DynamoDBTables.StatsTable.AVERAGE_TIME_SPENT_DEAD: 6,
        }
        return sort_indices.get(metric_to_sort, -1)

    def _sort_data(self, data, sort_idx):
        """Sort the data based on the specified index"""
        return sorted(
            [(item["puuid"],
              item[DynamoDBTables.StatsTable.KDA],
              item[DynamoDBTables.StatsTable.CS_PER_MIN],
              item[DynamoDBTables.StatsTable.DAMAGE_RECORD], 
              item[DynamoDBTables.StatsTable.AVERAGE_DAMAGE_DEALT_TO_CHAMPIONS],
              item[DynamoDBTables.StatsTable.AVERAGE_GOLD_EARNED],
              item[DynamoDBTables.StatsTable.AVERAGE_TIME_SPENT_DEAD])
             for item in data],
            key=lambda x: x[sort_idx],  # Sort by the metric value
            reverse=True
        )

    def get_leaderboard_players(self):
        """Query the database for all players in the leaderboard."""
        self.leaderboard = self.db.get_all_players()
        if not self.leaderboard:
            print("Leaderboard is currently empty.")
            return None

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
            game_name = response.get("gameName")
            tag_line = response.get("tagLine")
            if not puuid or not game_name or not tag_line:
                return "Player does not exist."
        except:
            return "Player does not exist."

        player = Player(game_name=game_name, tag_line=tag_line, puuid=puuid)

        # Add to cache
        self.leaderboard[player.puuid] = player

        # Add to DB
        self.db.add_player(player)

        await self.combine_matches(puuid)

        return f"Player {game_name}#{tag_line} added to leaderboard."

    def remove_player(self, index):
        """Remove a player from the leaderboard."""
        self.leaderboard = self.db.get_all_players()
        if not self.leaderboard:
            return "Leaderboard is currently empty."

        for idx, player in enumerate(self.leaderboard.values(), start=1):
            if idx == index:
                # Remove from DB
                self.db.remove_player(player.puuid, player.game_name, player.tag_line)
                # Remove from cache
                self.leaderboard.pop(player.puuid)
                return f"Player {player.game_name}#{player.tag_line} removed from the leaderboard."

        return f"No player found in the leaderboard."

    def remove_player_by_puuid(self, puuid):
        """Remove a player from the leaderboard by puuid."""
        self.leaderboard = self.db.get_all_players()
        if not self.leaderboard:
            return "Leaderboard is currently empty."

        player = self.leaderboard.get(puuid)
        if player:
            # Remove from DB
            self.db.remove_player(player.puuid, player.game_name, player.tag_line)
            # Remove from cache
            self.leaderboard.pop(player.puuid)
            return f"Player {player.game_name}#{player.tag_line} removed from the leaderboard."

        return f"No player found in the leaderboard."

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

    async def combine_matches(self, new_puuid=None):
        """get matches of all players in leaderboard since the last update, combine them into a single json file, and upload file to S3 bucket"""
        combined = {}
        new_matches_found = False
        combined_json_path = self.get_file_path(self.combined_json)
        puuids = [new_puuid] + list(self.leaderboard.keys()) if new_puuid else list(self.leaderboard.keys())
        last_update_time = self.get_last_update_time()

        try:
            for puuid in puuids:
                # For new players (if puuid given), fetch all matches (no start_time)
                current_start_time = "" if puuid == new_puuid else last_update_time

                match_ids = await self.riot_api.get_list_of_match_ids_by_puuid(puuid, start_time=current_start_time)

                for match_id in match_ids:
                    if match_id in combined:
                        continue

                    match = await self.riot_api.get_match_by_match_id(match_id)
                    # Filter participants to include only leaderboard players
                    match["info"]["participants"] = [
                        participant for participant in match["info"]["participants"]
                        if participant["puuid"] in self.leaderboard
                    ]
                    combined[match_id] = match
                    new_matches_found = True 

            if new_matches_found:
                with open(combined_json_path, "w") as f:
                    json.dump(combined, f)
                # upload json to S3
                BucketService().upload_file(combined_json_path, self.combined_json)
            else:
                print("\nAll games are up-to-date.")

        except Exception as e:
            print(f"\nAn error occurred while processing matches: {e}")
            traceback.print_exc()

        self.save_last_update_time()