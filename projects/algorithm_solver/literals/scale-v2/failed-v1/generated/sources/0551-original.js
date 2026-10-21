function isAttendanceEligible(text) {
  let absenceCount = 0;
  let lateRunLength = 0;
  for (const character of text) {
    if (character === 'A') {
      absenceCount += 1;
      if (absenceCount >= 2) {
        return false;
      }
    }
    if (character === 'L') {
      lateRunLength += 1;
      if (lateRunLength >= 3) {
        return false;
      }
    } else {
      lateRunLength = 0;
    }
  }
  return true;
}
class Solution {
  checkRecord(s) {
    return isAttendanceEligible(s);
  }
}
