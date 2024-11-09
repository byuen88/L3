import os
import time
import asyncio
from collections import deque
import requests
from dotenv import load_dotenv
from api.exceptions import RiotAPIError

load_dotenv()

class RiotAPI:
    def __init__(self):
        self.api_key = os.getenv("RIOT_API_KEY")
        self.riot_base_url = os.getenv("RIOT_BASE_URL")
        self.request_times = deque()

    async def _rate_limit(self):
        """Enforce Riot API's rate limits."""
        now = time.time()

        # Clear requests outside the 2-minute window
        while self.request_times and now - self.request_times[0] > 120:
            self.request_times.popleft()

        # Check for 100 requests in the last 2 minutes
        if len(self.request_times) >= 100:
            # Wait until rate limit clears
            wait_time = 120 - (now - self.request_times[0])
            print(f"Rate limit reached: Waiting for {wait_time:.2f} seconds.")
            await asyncio.sleep(wait_time)

        # Track current request time
        self.request_times.append(now)


    async def _make_request(self, endpoint, params=None):
        """Helper method to make a GET request to Riot API with rate limiting."""
        await self._rate_limit()  # Enforce rate limit before making request

        if params is None:
            params = {}
        params["api_key"] = self.api_key
        url = f"{self.riot_base_url}{endpoint}"

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as err:
            raise RiotAPIError(f"HTTP error occurred: {err}")
        except requests.exceptions.RequestException as req_err:
            raise RiotAPIError(f"Request error occurred: {req_err}")

    async def get_account_by_riot_id(self, game_name, tag_line):
        endpoint = f"/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"

        return await self._make_request(endpoint)

    async def get_list_of_match_ids_by_puuid(self, puuid, start_time=None, count=None):
        endpoint = f"/lol/match/v5/matches/by-puuid/{puuid}/ids"

        params = {"startTime": start_time, "count": count}

        return await self._make_request(endpoint, params)

    async def get_match_by_match_id(self, match_id):
        endpoint = f"/lol/match/v5/matches/{match_id}"
        return await self._make_request(endpoint)


