class Solution:
    def checkRecord(self, s: str) -> bool:
        absences = 0
        late_run = 0
        for character in s:
            if character == "A":
                absences += 1
            if character == "L":
                late_run += 1
            else:
                late_run = 0
            if absences >= 2 or late_run >= 3:
                return False
        return True
