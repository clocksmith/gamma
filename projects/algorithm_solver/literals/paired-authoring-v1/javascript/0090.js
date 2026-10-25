class Solution {
  subsetsWithDup(nums) {
    const ordered = nums.slice().sort((left, right) => {
      if (left < right) {
        return -1;
      }
      if (left > right) {
        return 1;
      }
      return 0;
    });
    const subsets = [];
    const path = [];

    function collect(start) {
      subsets.push(path.slice());
      for (let index = start; index < ordered.length; index += 1) {
        if (index > start && ordered[index] === ordered[index - 1]) {
          continue;
        }
        path.push(ordered[index]);
        collect(index + 1);
        path.pop();
      }
    }

    collect(0);
    return subsets;
  }
}
