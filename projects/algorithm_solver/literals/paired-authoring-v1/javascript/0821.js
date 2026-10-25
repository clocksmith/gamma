class Solution {
  shortestToChar(s, c) {
    const distances = new Array(s.length).fill(0);
    let previous = -s.length;
    for (let index = 0; index < s.length; index += 1) {
      if (s[index] === c) {
        previous = index;
      }
      distances[index] = index - previous;
    }
    let following = 2 * s.length;
    for (let index = s.length - 1; index >= 0; index -= 1) {
      if (s[index] === c) {
        following = index;
      }
      distances[index] = Math.min(distances[index], following - index);
    }
    return distances;
  }
}
