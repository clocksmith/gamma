"""Hack2Hire 6782d18f3cd890ccd3798fc5 (Find All 5-Minute Intervals) over an INFERRED spec; qualification unknown."""


DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
WEEK = 7 * 24 * 60


def parse(text):
    day, clock, half = text.split(' ')
    hour, minute = clock.split(':')
    h = int(hour) % 12
    if half == 'PM':
        h += 12
    return DAYS.index(day) * 1440 + h * 60 + int(minute)


def render(t):
    t %= WEEK
    day, rest = t // 1440, t % 1440
    h, minute = rest // 60, rest % 60
    shown = h % 12
    if shown == 0:
        shown = 12
    return DAYS[day] + ' ' + str(shown) + ':' + ('0' if minute < 10 else '') + str(minute) + (' AM' if h < 12 else ' PM')


def solve(start, end):
    a, b = parse(start), parse(end)
    if b < a:
        b += WEEK
    t = (a + 4) // 5 * 5
    result = []
    while t <= b:
        result.append(render(t))
        t += 5
    return result


class Solution:
    def fiveMinuteIntervals(self, start, end):
        return solve(start, end)
