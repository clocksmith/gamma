'use strict';

// 2847. Smallest Number With Given Digit Product: factor into large digits and place the selected digits in increasing order.
// O(log(n + 1)) time and output space on the stated integer domain; inputs are read-only.
function solve(n) {
  if (typeof n !== 'bigint' && !Number.isSafeInteger(n)) throw new RangeError('n must be an exact integer');
  let remaining = BigInt(n);
  if (remaining < 1n) throw new RangeError('n must be positive');
  if (remaining === 1n) return '1';
  const digits = [];
  for (let digit = 9n; digit >= 2n; digit -= 1n) {
    while (remaining % digit === 0n) {
      digits.push(digit.toString());
      remaining /= digit;
    }
  }
  if (remaining !== 1n) return '-1';
  return digits.reverse().join('');
}

const smallestNumber = solve;
class Solution {
  smallestNumber(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestNumber };
