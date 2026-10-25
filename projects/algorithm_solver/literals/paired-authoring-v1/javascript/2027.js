class Solution {
  minimumMoves(s) {
    let index = 0;
    let moves = 0;
    while (index < s.length) {
      if (s[index] === "X") {
        moves += 1;
        index += 3;
      } else {
        index += 1;
      }
    }
    return moves;
  }
}
