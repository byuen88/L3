import asyncio
from api.riot_api import RiotAPI
from db.dynamo import DynamoClient
from services.leaderboard_service import LeaderboardService
from db.db_constants import DynamoDBTables
from dotenv import load_dotenv

# Menu Options Constants
MENU_OPTIONS = {
    "1": "View Leaderboard",
    "2": "Add Player",
    "3": "Remove Player",
    "4": "Update Leaderboard",
    "5": "Exit"
}

METRICS = {
    '1': ("KDA", DynamoDBTables.StatsTable.KDA),
    '2': ("CS per min", DynamoDBTables.StatsTable.CS_PER_MIN),
    '3': ("Damage Record", DynamoDBTables.StatsTable.DAMAGE_RECORD),
    '4': ("Average Damage", DynamoDBTables.StatsTable.AVERAGE_DAMAGE_DEALT_TO_CHAMPIONS),
    '5': ("Average Gold Earned", DynamoDBTables.StatsTable.AVERAGE_GOLD_EARNED),
    '6': ("Average Time Spent Dead", DynamoDBTables.StatsTable.AVERAGE_TIME_SPENT_DEAD)
}

def display_menu() -> None:
    print("\n--- Leaderboard Manager ---")
    for key, value in MENU_OPTIONS.items():
        print(f"{key}. {value}")

def display_metrics() -> None:
    print("\nMetrics to sort by:")
    for key, (name, _) in METRICS.items():
        print(f"{key}. {name}")

def get_input(prompt: str) -> str | None:
    user_input = input(prompt).strip()
    if user_input.lower() == 'q':
        print("Operation canceled. Returning to main menu...")
        return None  # Indicate that the user wants to quit
    return user_input

async def handle_view_leaderboard(leaderboard_service: LeaderboardService, db: DynamoClient, leaderboard_name: str) -> None:
    status = db.check_processing_status(leaderboard_name)
    if status is None:
        return
    elif status:
        print("Leaderboard update in process")
        return
    display_metrics()
    metric_choice = get_input("Enter the metric to sort on (1-6, or 'q' to cancel): ")
    if metric_choice is None or metric_choice not in METRICS:
        print("Invalid choice or operation canceled. Returning to main menu.")
        return

    metric_to_sort = METRICS[metric_choice][1]

    try:
        print("\n--- Leaderboard ---")
        leaderboard_service.view_leaderboard(metric_to_sort)
    except Exception as e:
        print(f"An error occurred while fetching the leaderboard: {e}")

async def handle_add_player(leaderboard_service: LeaderboardService) -> None:
    game_name = get_input("Enter the player's game name (or 'q' to cancel): ")
    if game_name is None:
        return

    tag_line = get_input("Enter the player's tag line (or 'q' to cancel): ")
    if tag_line is None:
        return

    try:
        print(await leaderboard_service.add_player(game_name, tag_line))
    except Exception as e:
        print(f"An error occurred while adding the player: {e}")

async def handle_remove_player(leaderboard_service: LeaderboardService) -> None:
    print(leaderboard_service.get_leaderboard_players())
    index = get_input("Enter the player's number (or 'q' to cancel): ")
    if index is None:
        return

    try:
        print(leaderboard_service.remove_player(int(index)))
    except ValueError:
        print("Invalid input. Please enter a number.")
    except Exception as e:
        print(f"An error occurred while removing a player: {e}")

async def handle_update_leaderboard(leaderboard_service: LeaderboardService) -> None:
    try:
        await leaderboard_service.combine_matches()
    except Exception as e:
        print(f"An error occurred while updating the leaderboard: {e}")

async def main() -> None:
    load_dotenv()
    db = DynamoClient()
    riot_api = RiotAPI()
    leaderboard_name = "main_table"
    leaderboard_service = LeaderboardService(leaderboard_name, riot_api, db)

    while True:
        display_menu()
        choice = get_input("Choose an option: ")

        if choice == "1":
            await handle_view_leaderboard(leaderboard_service, db, leaderboard_name)
        elif choice == "2":
            await handle_add_player(leaderboard_service)
        elif choice == "3":
            await handle_remove_player(leaderboard_service)
        elif choice == "4":
            await handle_update_leaderboard(leaderboard_service)
        elif choice == "5":
            print("Exiting Leaderboard Manager.")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    asyncio.run(main())
