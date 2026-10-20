class Solution {
  firstUniqChar(values) {
    const counts = new Array(26).fill(0);
    for (const value of values) {
      const index = value.charCodeAt(0) - 97;
      counts[index] += 1;
    }
    for (let index = 0; index < values.length; index += 1) {
      if (counts[values.charCodeAt(index) - 97] === 1) {
        return index;
      }
    }
    return -1;
  }
}
