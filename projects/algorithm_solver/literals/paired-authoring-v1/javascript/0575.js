class Solution {
  distributeCandies(candyType) {
    const kinds = new Set(candyType);
    return Math.min(kinds.size, Math.floor(candyType.length / 2));
  }
}
