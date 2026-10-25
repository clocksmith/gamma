class Solution {
  numTilePossibilities(tiles) {
    const counts = new Array(26).fill(0);
    for (const letter of tiles) {
      counts[letter.charCodeAt(0) - 65] += 1;
    }
    let ways = [1];
    for (const count of counts) {
      if (count === 0) continue;
      const following = new Array(ways.length + count).fill(0);
      for (let length = 0; length < ways.length; length += 1) {
        let combinations = 1;
        for (let used = 0; used <= count; used += 1) {
          if (used > 0) combinations = combinations * (length + used) / used;
          following[length + used] += ways[length] * combinations;
        }
      }
      ways = following;
    }
    return ways.reduce((total, value) => total + value, 0) - 1;
  }
}
