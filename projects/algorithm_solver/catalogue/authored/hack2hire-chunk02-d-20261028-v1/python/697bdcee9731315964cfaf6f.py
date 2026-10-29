"""Hack2Hire 697bdcee9731315964cfaf6f (Hotel Booking Reminder, level 1) over an INFERRED spec; qualification unknown."""


def solve(reservations, emailTouchpoints):
    schedule = []
    for stay in reservations:
        for name, touchpoint in emailTouchpoints.items():
            day = stay['check_in_day'] + touchpoint
            schedule.append([day, stay['guest_name'], name])
    schedule.sort()
    return schedule


class Solution:
    def buildEmailSchedule(self, reservations, emailTouchpoints):
        return solve(reservations, emailTouchpoints)
