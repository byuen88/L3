class DynamoDBTables:
    class PlayersTable:
        TABLE_NAME = "players"
        GAME_NAME = "game_name"
        TAG_LINE = "tag_line"
        PUUID = "puuid"

    class StatsTable:
        TABLE_NAME = "stats"
        PUUID = "puuid"
        KDA = "kda"
        NUMBER_OF_GAMES = "numberOfGames"
        AVERAGE_DAMAGE_DEALT_TO_CHAMPIONS = "totalDamageDealtToChampions"
        CS_PER_MIN = "csPerMin"
        DAMAGE_RECORD = "damageDealtToChampionsRecord"
        AVERAGE_GOLD_EARNED = "goldEarned"
        AVERAGE_TIME_SPENT_DEAD = "totalTimeSpentDead"

    class ProcessingStatusTable:
        TABLE_NAME = "processing_status"
        LEADERBOARD_NAME = "leaderboard_name"
        PROCESSING = "processing"

