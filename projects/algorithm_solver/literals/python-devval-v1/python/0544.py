def solve(team_count):
    round_teams = [str(number) for number in range(1, team_count + 1)]
    while len(round_teams) > 1:
        round_teams = ["(" + round_teams[index] + "," + round_teams[-index - 1] + ")"
                       for index in range(len(round_teams) // 2)]
    return round_teams[0]
