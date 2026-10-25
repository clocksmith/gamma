class Solution {
  findErrorNums(nums) {
    const counts = new Array(nums.length + 1).fill(0);
    for (const value of nums) {
      counts[value] += 1;
    }
    let duplicate = 0;
    let missing = 0;
    for (let value = 1; value < counts.length; value += 1) {
      if (counts[value] === 2) {
        duplicate = value;
      } else if (counts[value] === 0) {
        missing = value;
      }
    }
    return [duplicate, missing];
  }
}
