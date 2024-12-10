class RiotAPIError(Exception):
    """Custom exception for errors related to the Riot API."""
    pass

class InvalidResponseError(RiotAPIError):
    """Exception raised for invalid responses from the Riot API."""
    def __init__(self, message="Invalid response received from the API."):
        self.message = message
        super().__init__(self.message)

class NotFoundError(RiotAPIError):
    """Exception raised when a requested resource is not found."""
    def __init__(self, resource, identifier):
        self.message = f"{resource} with identifier '{identifier}' not found."
        super().__init__(self.message)

class RateLimitExceededError(RiotAPIError):
    """Exception raised when the API rate limit is exceeded."""
    def __init__(self, reset_time):
        self.message = f"Rate limit exceeded. Try again in {reset_time} seconds."
        super().__init__(self.message)

class APIKeyError(RiotAPIError):
    """Exception raised for issues related to the API key."""
    def __init__(self, message="Invalid or missing API key."):
        self.message = message
        super().__init__(self.message)