import json

class GameStatistics:
    def __init__(self, stats_file='game_stats.json'):
        self.stats_file = stats_file
        self.player_stats = {}
        self.load_stats()

    def load_stats(self):
        try:
            with open(self.stats_file, 'r') as file:
                self.player_stats = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            print("Stats file not found or corrupted, starting fresh.")

    def record_game_played(self, player_name):
        if player_name not in self.player_stats:
            self.player_stats[player_name] = {'games_played': 0, 'victories': 0}
        self.player_stats[player_name]['games_played'] += 1

    def record_victory(self, player_name):
        if player_name not in self.player_stats:
            self.player_stats[player_name] = {'games_played': 1, 'victories': 0}
        self.player_stats[player_name]['victories'] += 1

    def save_stats(self):
        with open(self.stats_file, 'w') as file:
            json.dump(self.player_stats, file, indent=4)

    def get_summary(self, current_game_players):
        summary = "Game Statistics:\n"
        for player in current_game_players:
            stats = self.player_stats.get(player, {'games_played': 0, 'victories': 0})
            summary += f"Player: {player}, Games Played: {stats['games_played']}, Victories: {stats['victories']}\n"
        return summary
