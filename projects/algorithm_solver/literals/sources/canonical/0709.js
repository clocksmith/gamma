class Solution {
  toLowerCase(values) {
    const upper = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    const lower = 'abcdefghijklmnopqrstuvwxyz';
    const result = [];
    for (const value of values) {
      const index = upper.indexOf(value);
      result.push(index >= 0 ? lower[index] : value);
    }
    return result.join('');
  }
}
