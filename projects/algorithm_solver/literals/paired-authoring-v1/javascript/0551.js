class Solution {
  checkRecord(s) {
    let absences = 0;
    let late_run = 0;
    for (const character of s) {
      if (character === "A") {
        absences += 1;
      }
      if (character === "L") {
        late_run += 1;
      } else {
        late_run = 0;
      }
      if (absences >= 2 || late_run >= 3) {
        return false;
      }
    }
    return true;
  }
}
