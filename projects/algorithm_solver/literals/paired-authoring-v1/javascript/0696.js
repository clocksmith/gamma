class Solution {
  countBinarySubstrings(s) {
    if (s.length === 0) {
      return 0;
    }

    let previous_run = 0;
    let current_run = 1;
    let count = 0;
    for (let index = 1; index < s.length; index += 1) {
      if (s[index] === s[index - 1]) {
        current_run += 1;
      } else {
        count += Math.min(previous_run, current_run);
        previous_run = current_run;
        current_run = 1;
      }
    }
    return count + Math.min(previous_run, current_run);
  }
}
