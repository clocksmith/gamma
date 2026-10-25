class Solution {
  minOperations(nums) {
    let parity = 0;
    let operations = 0;
    for (const value of nums) {
      const effective = parity === 0 ? value : 1 - value;
      if (effective === 0) {
        operations += 1;
        parity = 1 - parity;
      }
    }
    return operations;
  }
}
