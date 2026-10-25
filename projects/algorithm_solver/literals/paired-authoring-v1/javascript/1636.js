class Solution {
  frequencySort(nums) {
    const frequencies = new Map();
    for (const value of nums) {
      frequencies.set(value, (frequencies.get(value) || 0) + 1);
    }
    return nums.slice().sort((first, second) => {
      const difference = frequencies.get(first) - frequencies.get(second);
      return difference !== 0 ? difference : second - first;
    });
  }
}
