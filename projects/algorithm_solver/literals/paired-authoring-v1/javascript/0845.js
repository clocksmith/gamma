class Solution {
  longestMountain(arr) {
    let uphill = 0;
    let downhill = 0;
    let longest = 0;
    for (let index = 1; index < arr.length; index += 1) {
      const previous = arr[index - 1];
      const current = arr[index];
      if (current === previous || (downhill > 0 && current > previous)) {
        uphill = 0;
        downhill = 0;
      }
      if (current > previous) {
        uphill += 1;
      } else if (current < previous && uphill > 0) {
        downhill += 1;
      }
      if (uphill > 0 && downhill > 0) {
        longest = Math.max(longest, uphill + downhill + 1);
      }
    }
    return longest;
  }
}
