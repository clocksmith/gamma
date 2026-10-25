class Solution {
  combinationSum2(candidates, target) {
    const ordered = candidates.slice().sort((left, right) => {
      if (left < right) {
        return -1;
      }
      if (left > right) {
        return 1;
      }
      return 0;
    });
    const combinations = [];
    const path = [];

    function collect(start, remaining) {
      if (remaining === 0) {
        combinations.push(path.slice());
        return;
      }
      for (let index = start; index < ordered.length; index += 1) {
        if (index > start && ordered[index] === ordered[index - 1]) {
          continue;
        }
        const value = ordered[index];
        if (value > remaining) {
          break;
        }
        path.push(value);
        collect(index + 1, remaining - value);
        path.pop();
      }
    }

    collect(0, target);
    return combinations;
  }
}
