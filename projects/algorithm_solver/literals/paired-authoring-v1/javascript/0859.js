class Solution {
  buddyStrings(s, goal) {
    if (s.length !== goal.length) {
      return false;
    }
    if (s === goal) {
      return new Set(s).size < s.length;
    }

    const mismatches = [];
    for (let index = 0; index < s.length; index += 1) {
      if (s[index] !== goal[index]) {
        mismatches.push(index);
        if (mismatches.length > 2) {
          return false;
        }
      }
    }
    if (mismatches.length !== 2) {
      return false;
    }
    const [first, second] = mismatches;
    return s[first] === goal[second] && s[second] === goal[first];
  }
}
