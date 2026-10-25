class Solution {
  maxSumTwoNoOverlap(nums, firstLen, secondLen) {
    const prefix = [0];
    for (const value of nums) prefix.push(prefix[prefix.length - 1] + value);

    function firstBeforeSecond(firstLength, secondLength) {
      let bestFirst = prefix[firstLength];
      let bestTotal = prefix[firstLength + secondLength];
      for (let end = firstLength + secondLength; end <= nums.length; end += 1) {
        const split = end - secondLength;
        bestFirst = Math.max(bestFirst, prefix[split] - prefix[split - firstLength]);
        bestTotal = Math.max(bestTotal, bestFirst + prefix[end] - prefix[split]);
      }
      return bestTotal;
    }

    return Math.max(firstBeforeSecond(firstLen, secondLen),
      firstBeforeSecond(secondLen, firstLen));
  }
}
