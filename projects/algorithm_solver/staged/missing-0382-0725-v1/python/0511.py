"""511. Game Play Analysis I. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. activity: player_id, device_id, event_date (YYYY-MM-DD), games_played. Output: player_id, first_login."""

def solve(activity):
    first = {}
    for row in activity:
        player, day = row['player_id'], row['event_date']
        if player not in first or day < first[player]:
            first[player] = day
    return [{'player_id': player, 'first_login': first[player]} for player in sorted(first)]


class Solution:
    def gamePlayAnalysis(self, activity):
        return solve(activity)
