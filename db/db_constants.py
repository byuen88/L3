class DynamoDBTables:
    class PlayerTable:
        TABLE_NAME = "players"
        GAME_NAME = "game_name"
        TAG_LINE = "tag_line"
        PUUID = "puuid"

    class StatsTable:
        TABLE_NAME = "stats"
        PUUID = "puuid"
        KDA = "kda"
        NUMBER_OF_GAMES = "numberOfGames"
        TOTAL_AVERAGE_DAMAGE_DEALT_TO_CHAMPIONS = "totalAverageDamageDealtToChampions"

