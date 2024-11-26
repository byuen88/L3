import asyncio
from services.leaderboard_service import LeaderboardService
from db.db_constants import DynamoDBTables


def display_menu():
    print("\n--- Leaderboard Manager ---")
    print("1. View Leaderboard")
    print("2. Add Player")
    print("3. Remove Player")
    print("4. Update Leaderboard")
    print("5. Exit")

def get_input(prompt):
    user_input = input(prompt).strip()
    if user_input.lower() == 'q':
        print("Operation canceled. Returning to main menu...")
        return None  # Indicate that the user wants to quit
    return user_input

async def main():
    leaderboard_service = LeaderboardService()

    while True:
        display_menu()
        choice = get_input("Choose an option: ")

        if choice == '1':
            metrics = {
                '1': 'Average Damage',
                '2': 'KDA',
            }

            print("\nMetrics to sort by:")
            for key, value in metrics.items():
                print(f"{key}. {value}")

            metric_choice = get_input("Enter the metric to sort on (1-2, or 'q' to cancel): ")
            if metric_choice is None:
                continue

            metric_to_sort = ""

            if metric_choice not in metrics:
                print("Invalid choice for metric. Please try again.")
                continue
            elif metric_choice == '1':
                metric_to_sort = DynamoDBTables.StatsTable.AVERAGE_TOTAL_DAMAGE_DEALT_TO_CHAMPIONS
            elif metric_choice == '2':
                metric_to_sort = DynamoDBTables.StatsTable.KDA

            try:
                print("\n--- Leaderboard ---")
                leaderboard_service.view_leaderboard(metric_to_sort)
            except Exception as e:
                print(f"An error occurred while fetching the leaderboard: {e}")

        elif choice == '2':
            game_name = get_input("Enter the player's game name (or 'q' to cancel): ")
            if game_name is None:
                continue

            tag_line = get_input("Enter the player's tag line (or 'q' to cancel): ")
            if tag_line is None:
                continue

            try:
                print(await leaderboard_service.add_player(game_name, tag_line))
            except Exception as e:
                print(f"An error occurred while adding the player: {e}")

        elif choice == '3':
            print(leaderboard_service.get_leaderboard_players())
            game_name = get_input("Enter the player's game name (or 'q' to cancel): ")
            if game_name is None:
                continue

            tag_line = get_input("Enter the player's tag line (or 'q' to cancel): ")
            if tag_line is None:
                continue
            try:
                print(leaderboard_service.remove_player(game_name, tag_line))
            except ValueError:
                print("Invalid input. Please enter a number.")
            except Exception as e:
                print(f"An error occurred while removing a player: {e}")

        elif choice == '4':
            try:
                await leaderboard_service.combine_matches()
            except Exception as e:
                print(f"An error occurred while updating the leaderboard: {e}")

        elif choice == '5':
            print("Exiting Leaderboard Manager.")
            break

        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    asyncio.run(main())