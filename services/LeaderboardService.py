from L3.api.riot_api import RiotAPI

class LeaderboardService:
    def __init__(self):
        self.riot_api = RiotAPI()

    def get_leaderboard_players(self):
        """Query the database for all players in the leaderboard."""

    def add_player_to_leaderboard(self, gameN_name, tag_line):
        """Add a player to the leaderboard."""

    def update_leaderboard(self):
        """Update the leaderboard. Display results to terminal. (for the time being)"""