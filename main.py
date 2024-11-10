from flask import Flask, request
from threading import Thread
from services.leaderboard_service import LeaderboardService

# Initialize Flask application
app = Flask(__name__)

# Define route for receiving POST data from Lambda
@app.route('/receive_data', methods=['POST'])
def receive_data():
    data = request.json  # Expecting JSON data from Lambda
    print("\nReceived data:", data)
    # Optionally, update or process leaderboard with received data
    # leaderboard_service.update_leaderboard()  # Modify this if needed for data processing
    return "Data received", 200

# Function to run the Flask server in a separate thread
def run_server():
    app.run(host='0.0.0.0', port=5000)


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
    # Start the Flask server in a background thread
    server_thread = Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

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