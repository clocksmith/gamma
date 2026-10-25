class Solution {
  minimumRecolors(blocks, k) {
    let white = 0;
    let best = k;
    for (let index = 0; index < blocks.length; index += 1) {
      if (blocks[index] === "W") {
        white += 1;
      }
      if (index >= k && blocks[index - k] === "W") {
        white -= 1;
      }
      if (index + 1 >= k) {
        best = Math.min(best, white);
      }
    }
    return best;
  }
}
