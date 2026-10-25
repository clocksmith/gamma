class Solution {
  diStringMatch(s) {
    let lowest = 0;
    let highest = s.length;
    const result = [];
    for (const character of s) {
      if (character === "I") {
        result.push(lowest);
        lowest += 1;
      } else {
        result.push(highest);
        highest -= 1;
      }
    }
    result.push(lowest);
    return result;
  }
}
