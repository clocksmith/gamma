class Solution {
  splitArray(nums) {
    if (nums.length < 7) {
      return false;
    }

    const prefix = [0];
    for (const value of nums) {
      prefix.push(prefix[prefix.length - 1] + value);
    }
    for (let middle = 3; middle < nums.length - 3; middle += 1) {
      const sums = new Set();
      for (let left = 1; left < middle - 1; left += 1) {
        const first = prefix[left];
        const second = prefix[middle] - prefix[left + 1];
        if (first === second) {
          sums.add(first);
        }
      }
      for (let right = middle + 2; right < nums.length - 1; right += 1) {
        const third = prefix[right] - prefix[middle + 1];
        const fourth = prefix[nums.length] - prefix[right + 1];
        if (third === fourth && sums.has(third)) {
          return true;
        }
      }
    }
    return false;
  }
}
