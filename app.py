from flask import Flask, render_template, request, redirect, url_for
from services.leaderboard_service import LeaderboardService
from api.riot_api import RiotAPI
from db.dynamo import DynamoClient
from db.db_constants import DynamoDBTables

app = Flask(__name__)

# Initialize services
db = DynamoClient()
riot_api = RiotAPI()
leaderboard_service = LeaderboardService("main_table", riot_api, db)

@app.route('/')
def index():
    metric_to_sort = request.args.get('metric', DynamoDBTables.StatsTable.KDA)
    leaderboard = leaderboard_service.view_leaderboard(metric_to_sort)
    error_message = request.args.get('error_message')
    return render_template('index.html', leaderboard=leaderboard, DynamoDBTables=DynamoDBTables, error_message=error_message)

@app.route('/add_player', methods=['POST'])
async def add_player():
    game_name = request.form['game_name']
    tag_line = request.form['tag_line']
    result = await leaderboard_service.add_player(game_name, tag_line)
    if "does not exist" in result:
        return redirect(url_for('index', error_message=result))
    return redirect(url_for('index'))

@app.route('/remove_player', methods=['POST'])
def remove_player():
    player_index = int(request.form['player_index'])
    leaderboard_service.remove_player(player_index)
    return redirect(url_for('index'))

@app.route('/update_leaderboard', methods=['POST'])
async def update_leaderboard():
    await leaderboard_service.combine_matches()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)