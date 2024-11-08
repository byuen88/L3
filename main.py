from services.leaderboard_service import LeaderboardService


def display_menu():
    print("\n--- Leaderboard Manager ---")
    print("1. View Leaderboard")
    print("2. Add Player")
    print("3. Remove Player")
    print("4. Update Leaderboard")
    print("5. Combine")
    print("6. Exit")

def main():
    leaderboard_service = LeaderboardService()
    # leaderboard_service.add_player("Krono", "urmom")

    while True:
        display_menu()
        choice = input("Choose an option: ").strip()

        if choice == '1':
            print(leaderboard_service.get_leaderboard_players())

        elif choice == '2':
            game_name = input("Enter the player's game name: ").strip()
            tag_line = input("Enter the player's tag line: ").strip()
            print(leaderboard_service.add_player(game_name, tag_line))

        elif choice == '3':
            print(leaderboard_service.get_leaderboard_players())
            try:
                game_name = input("Enter the player's game name: ").strip()
                tag_line = input("Enter the player's tag line: ").strip()
                print(leaderboard_service.remove_player(game_name, tag_line))
            except ValueError:
                print("Invalid input. Please enter a number.")

        elif choice == '4':
            start_time = input("Enter start time: ").strip()
            count = input("Enter number of matches: ").strip()
            leaderboard_service.update_leaderboard(start_time, count)

        elif choice == '5':
            leaderboard_service.combine_matches()

        elif choice == '6':
            print("Exiting Leaderboard Manager.")
            break

        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()