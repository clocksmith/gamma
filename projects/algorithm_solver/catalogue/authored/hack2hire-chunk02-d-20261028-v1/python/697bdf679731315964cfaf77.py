"""Hack2Hire 697bdf679731315964cfaf77 (Hotel Booking Reminder, level 2) over an INFERRED spec; qualification unknown."""


def solve(reservations, emailTouchpoints):
    schedule = []
    for stay in reservations:
        for name, touchpoint in emailTouchpoints.items():
            anchor = stay['check_in_day'] + (stay['stay_length'] if touchpoint['anchor'] == 'check_out' else 0)
            day = anchor + touchpoint['offset']
            schedule.append([day, stay['guest_name'], name])
    schedule.sort()
    return schedule


class Solution:
    def buildEmailSchedule(self, reservations, emailTouchpoints):
        return solve(reservations, emailTouchpoints)
