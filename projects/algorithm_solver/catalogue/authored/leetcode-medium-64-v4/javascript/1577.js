'use strict';

// 1577. Number of Ways Where Square of Number Is Equal to Product of Two Numbers: count matching products with duplicate-aware two-pointer scans.
// O(n * m + n log(n + 1) + m log(m + 1)) time and O(n + m) auxiliary space; inputs are read-only.
function solve(nums1, nums2) {
  const first = nums1.slice().sort((a, b) => a - b);
  const second = nums2.slice().sort((a, b) => a - b);
  function count(squares, values) {
    let total = 0;
    for (const value of squares) {
      const target = value * value;
      let left = 0;
      let right = values.length - 1;
      while (left < right) {
        const product = values[left] * values[right];
        if (product < target) left += 1;
        else if (product > target) right -= 1;
        else if (values[left] === values[right]) {
          const width = right - left + 1;
          total += width * (width - 1) / 2;
          break;
        } else {
          const low = values[left];
          const high = values[right];
          let lowCount = 0;
          let highCount = 0;
          while (left <= right && values[left] === low) {
            lowCount += 1;
            left += 1;
          }
          while (left <= right && values[right] === high) {
            highCount += 1;
            right -= 1;
          }
          total += lowCount * highCount;
        }
      }
    }
    return total;
  }
  return count(first, second) + count(second, first);
}

const numTriplets = solve;
class Solution {
  numTriplets(nums1, nums2) { return solve(nums1, nums2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numTriplets };
