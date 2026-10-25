class Solution {
  findCenter(edges) {
    const [first, second] = edges[0];
    const [otherFirst, otherSecond] = edges[1];
    if (first === otherFirst || first === otherSecond) {
      return first;
    }
    return second;
  }
}
