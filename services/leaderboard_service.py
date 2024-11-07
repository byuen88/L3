from api.riot_api import RiotAPI
from models.player import Player

class LeaderboardService:
    def __init__(self):
        self.riot_api = RiotAPI()
        self.leaderboard = []

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
        puuid = self.riot_api.get_account_by_riot_id(game_name, tag_line).get("puuid")
        player = Player(game_name=game_name, tag_line=tag_line, puuid=puuid)
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
            match_ids = self.riot_api.get_list_of_match_ids_by_puuid(player.puuid, start_time, count)

            num_matches = len(match_ids)
            total_damage = 0

            for match_id in match_ids:
                match = self.riot_api.get_match_by_match_id(match_id)
                total_damage += int(match.get("info").get("participants")[0].get("totalDamageDealt"))

            print(player.game_name, "#", player.tag_line, "'s average Damage in the past", num_matches, "games: ", total_damage/ num_matches)

