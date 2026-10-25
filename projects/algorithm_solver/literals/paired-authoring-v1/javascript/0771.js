class Solution {
  numJewelsInStones(jewels, stones) {
    const kinds = new Set(jewels);
    let count = 0;
    for (const stone of stones) {
      if (kinds.has(stone)) {
        count += 1;
      }
    }
    return count;
  }
}
