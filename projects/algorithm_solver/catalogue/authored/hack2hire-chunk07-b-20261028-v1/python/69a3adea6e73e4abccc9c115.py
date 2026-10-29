"""Hack2Hire 69a3adea6e73e4abccc9c115 (Monster Team Battle, level 2) over an INFERRED spec; qualification unknown."""

LEVEL = 2


def solve(teamA, teamB):
    teams = (teamA, teamB)
    health = ([m['health'] for m in teamA], [m['health'] for m in teamB])
    front = [0, 0]
    log = []

    def attack(side):
        other = 1 - side
        attacker, defender = teams[side][front[side]], teams[other][front[other]]
        damage = attacker['attack'] if LEVEL == 1 else max(1, attacker['attack'] - defender['defense'])
        left = health[other][front[other]] - damage
        health[other][front[other]] = left
        log.append('%s attacks %s for %d damage, %s has %d health left' % (attacker['name'], defender['name'], damage, defender['name'], max(0, left)))
        if left <= 0:
            log.append(defender['name'] + ' is defeated')
            front[other] += 1
            return True
        return False

    turn = 0
    while front[0] < len(teamA) and front[1] < len(teamB):
        if LEVEL == 3:
            first = 0 if teamA[front[0]]['speed'] >= teamB[front[1]]['speed'] else 1
            if not attack(first):
                attack(1 - first)
        else:
            attack(turn)
            turn = 1 - turn
    log.append('Team A wins' if front[0] < len(teamA) else 'Team B wins')
    return log


class Solution:
    def battleLog(self, teamA, teamB):
        return solve(teamA, teamB)
