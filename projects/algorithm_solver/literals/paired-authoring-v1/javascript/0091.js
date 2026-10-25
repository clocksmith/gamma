class Solution {
  numDecodings(s) {
    if (s.length === 0) {
      return 0;
    }
    let twoBack = 1;
    let oneBack = s[0] === "0" ? 0 : 1;
    for (let index = 1; index < s.length; index += 1) {
      let current = s[index] === "0" ? 0 : oneBack;
      if (s[index - 1] === "1" || (
        s[index - 1] === "2" && s[index] <= "6"
      )) {
        current += twoBack;
      }
      // Shift only after both valid token lengths read their prefix counts.
      twoBack = oneBack;
      oneBack = current;
    }
    return oneBack;
  }
}
