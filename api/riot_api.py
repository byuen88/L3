import os

import requests
from dotenv import load_dotenv

from L3.api.exceptions import RiotAPIError

load_dotenv()

class RiotAPI:
    def __init__(self):
        self.api_key = os.getenv("RIOT_API_KEY")
        self.riot_base_url = os.getenv("RIOT_BASE_URL")

    def _make_request(self, endpoint):
        """Helper method to make a GET request to Riot API."""
        url = f"{self.riot_base_url}{endpoint}?api_key={self.api_key}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as err:
            raise RiotAPIError(f"HTTP error occurred: {err}")
        except requests.exceptions.RequestException as req_err:
            raise RiotAPIError(f"Request error occurred: {req_err}")

    def get_account_by_riot_id(self, game_name, tag_line):
        endpoint = f"/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        return self._make_request(endpoint)

    def get_list_of_match_ids_by_puuid(self, puuid, start_time):
        endpoint = f"/lol/match/v5/matches/by-puuid/{puuid}/ids?startTime={start_time}"

        return self._make_request(endpoint)

    def get_match_by_match_id(self, match_id):
        endpoint = f"/lol/match/v5/matches/{match_id}"
        return self._make_request(endpoint)


