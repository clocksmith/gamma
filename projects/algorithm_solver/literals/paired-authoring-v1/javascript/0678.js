class Solution {
  checkValidString(s) {
    let minimum = 0;
    let maximum = 0;
    for (const character of s) {
      if (character === "(") {
        minimum += 1;
        maximum += 1;
      } else if (character === ")") {
        minimum = Math.max(0, minimum - 1);
        maximum -= 1;
      } else {
        minimum = Math.max(0, minimum - 1);
        maximum += 1;
      }
      if (maximum < 0) {
        return false;
      }
    }
    return minimum === 0;
  }
}
