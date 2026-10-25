class Solution {
  subsets(nums) {
    const subsets = [];
    const path = [];

    function collect(start) {
      subsets.push(path.slice());
      for (let index = start; index < nums.length; index += 1) {
        path.push(nums[index]);
        collect(index + 1);
        path.pop();
      }
    }

    collect(0);
    return subsets;
  }
}
