"""512. Game Play Analysis II. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. activity: player_id, device_id, event_date (YYYY-MM-DD), games_played. Output: player_id, device_id."""

def solve(activity):
    first = {}
    for row in activity:
        player = row['player_id']
        if player not in first or row['event_date'] < first[player]['event_date']:
            first[player] = row
    return [{'player_id': player, 'device_id': first[player]['device_id']} for player in sorted(first)]


class Solution:
    def gamePlayAnalysis(self, activity):
        return solve(activity)
