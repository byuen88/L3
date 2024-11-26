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
        #TODO CHANGE COLUMN NAME AFTER RYAN'S CHANGES
        AVERAGE_TOTAL_DAMAGE_DEALT_TO_CHAMPIONS = "totalDamageDealtToChampions"
