function countSequences(counts) {
  let total = 0;
  for (let letter = 0; letter < 26; letter += 1) {
    if (counts[letter] > 0) {
      counts[letter] -= 1;
      total += 1 + countSequences(counts);
      counts[letter] += 1;
    }
  }
  return total;
}


class Solution {
  numTilePossibilities(tiles) {
    const counts = Array(26).fill(0);
    for (const letter of tiles) {
      counts[letter.charCodeAt(0) - 65] += 1;
    }
    return countSequences(counts);
  }
}
