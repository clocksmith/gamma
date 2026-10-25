class Solution {
  maxUncrossedLines(nums1, nums2) {
    const row = new Array(nums2.length + 1).fill(0);
    for (const left of nums1) {
      let diagonal = 0;
      for (let index = 1; index <= nums2.length; index += 1) {
        const previous = row[index];
        if (left === nums2[index - 1]) row[index] = diagonal + 1;
        else row[index] = Math.max(row[index], row[index - 1]);
        diagonal = previous;
      }
    }
    return row[row.length - 1];
  }
}
