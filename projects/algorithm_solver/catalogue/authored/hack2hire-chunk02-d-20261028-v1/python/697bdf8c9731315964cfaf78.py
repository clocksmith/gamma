"""Hack2Hire 697bdf8c9731315964cfaf78 (Hotel Booking Reminder, level 3) over an INFERRED spec; qualification unknown."""


def solve(reservations, emailTouchpoints):
    schedule = []
    for stay in reservations:
        for name, touchpoint in emailTouchpoints.items():
            rooms = touchpoint.get('room_types')
            if rooms is not None and stay['room_type'] not in rooms:
                continue
            anchor = stay['check_in_day'] + (stay['stay_length'] if touchpoint['anchor'] == 'check_out' else 0)
            day = anchor + touchpoint['offset']
            schedule.append([day, stay['guest_name'], name])
    schedule.sort()
    return schedule


class Solution:
    def buildEmailSchedule(self, reservations, emailTouchpoints):
        return solve(reservations, emailTouchpoints)
