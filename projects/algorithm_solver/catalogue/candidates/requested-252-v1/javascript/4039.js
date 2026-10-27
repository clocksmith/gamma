/**
 * 4039. Sum of Decoded Numbers
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/sum-of-decoded-numbers/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4039.Sum%20of%20Decoded%20Numbers/README_EN.md
 * Complexity: O(n log(max exponent)) time, O(log(max encoded value)) temporary space.
 * Valid encoded inputs below 10^15 are exact JS Numbers. Modular multiplication uses exact split products. Inputs preserved.
 */

function multiplyMod(a, b, modulus = 1000000007) {
  const low = a % 32768, high = Math.floor(a / 32768);
  return (low * b + ((high * b) % modulus) * 32768) % modulus;
}

function solve(nums) {
  const modulus=1000000007;
  function power(base,exponent) {
    let result=1;
    while(exponent>0) {
      if(exponent%2)result=multiplyMod(result,base,modulus);
      exponent=Math.floor(exponent/2);
      if(exponent)base=multiplyMod(base,base,modulus);
    }
    return result;
  }
  let answer=0;
  for(const value of nums) {
    const encoded=String(value),width=Number(encoded.at(-1)),digits=encoded.slice(0,-1);
    answer=(answer+power(Number(digits.slice(0,width)),Number(digits.slice(width))))%modulus;
  }
  return answer;
}

function sumDecoded(nums) {
  return solve(nums);
}

class Solution {
  sumDecoded(nums) {
    return solve(nums);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, sumDecoded, Solution };
}
