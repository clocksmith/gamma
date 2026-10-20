class Solution {
  checkRecord(values) {
    let count = 0;
    let length = 0;
    for (const value of values) {
      if (value === 'A' && ++count >= 2) return false;
      if (value === 'L') {
        if (++length >= 3) return false;
      } else {
        length = 0;
      }
    }
    return true;
  }
}
