"""534. Game Play Analysis III. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. activity: player_id, device_id, event_date (YYYY-MM-DD), games_played. Output: player_id, event_date, games_played_so_far."""

def solve(activity):
    result, totals = [], {}
    for row in sorted(activity, key=lambda item: (item['player_id'], item['event_date'])):
        player = row['player_id']
        totals[player] = totals.get(player, 0) + row['games_played']
        result.append({'player_id': player, 'event_date': row['event_date'],
                       'games_played_so_far': totals[player]})
    return result


class Solution:
    def gamePlayAnalysis(self, activity):
        return solve(activity)
