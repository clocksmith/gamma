class Solution {
  partitionLabels(s) {
    const last = new Array(26).fill(-1);
    for (let index = 0; index < s.length; index += 1) {
      last[s.charCodeAt(index) - 97] = index;
    }
    const result = [];
    let start = 0;
    let end = 0;
    for (let index = 0; index < s.length; index += 1) {
      end = Math.max(end, last[s.charCodeAt(index) - 97]);
      if (index === end) {
        result.push(index - start + 1);
        start = index + 1;
      }
    }
    return result;
  }
}
