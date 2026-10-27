'use strict';
// 220. Contains Duplicate III.
function floorDiv(value, width) { return Math.floor(value / width); }
function solve(nums, indexDiff, valueDiff) {
  if (valueDiff < 0) return false;
  const width = valueDiff + 1; const buckets = new Map();
  for (let index = 0; index < nums.length; index += 1) {
    const value = nums[index]; const bucket = floorDiv(value, width);
    if (buckets.has(bucket)) return true;
    if (buckets.has(bucket - 1) && value - buckets.get(bucket - 1) <= valueDiff) return true;
    if (buckets.has(bucket + 1) && buckets.get(bucket + 1) - value <= valueDiff) return true;
    buckets.set(bucket, value);
    if (index >= indexDiff) buckets.delete(floorDiv(nums[index - indexDiff], width));
  }
  return false;
}
const containsNearbyAlmostDuplicate = solve;
class Solution { containsNearbyAlmostDuplicate(nums, indexDiff, valueDiff) { return solve(nums, indexDiff, valueDiff); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, containsNearbyAlmostDuplicate };
