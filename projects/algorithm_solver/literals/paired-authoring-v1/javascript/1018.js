class Solution {
  prefixesDivBy5(nums) {
    const answer = [];
    let remainder = 0;
    for (const bit of nums) {
      remainder = (remainder * 2 + bit) % 5;
      answer.push(remainder === 0);
    }
    return answer;
  }
}
