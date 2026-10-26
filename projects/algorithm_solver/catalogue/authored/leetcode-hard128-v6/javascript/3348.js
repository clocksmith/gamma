'use strict';

// 3348. Smallest Divisible Digit Product II.
// Cover required prime exponents while choosing the rightmost feasible increment and lexicographically least suffix; O(9*L+log t) time and O(L) space. Inputs are preserved.

function solve(num, t) {
  const factors = [[0,0,0,0],[0,0,0,0],[1,0,0,0],[0,1,0,0],[2,0,0,0],[0,0,1,0],[1,1,0,0],[0,0,0,1],[3,0,0,0],[0,2,0,0]];
  const required = [0, 0, 0, 0], primes = [2n, 3n, 5n, 7n];
  let product = BigInt(t);
  for (let index = 0; index < 4; index += 1) {
    while (product % primes[index] === 0n) { required[index] += 1; product /= primes[index]; }
  }
  if (product !== 1n) return '-1';
  function consume(state, digit) { return state.map((value, index) => Math.max(0, value - factors[digit][index])); }
  function needed(state) {
    let [twos, threes, fives, sevens] = state;
    const answer = fives + sevens + Math.floor(twos / 3) + Math.floor(threes / 2);
    twos %= 3; threes %= 2;
    return answer + Math.ceil(twos / 2) + threes - (twos === 1 && threes === 1 ? 1 : 0);
  }
  function fill(state, length) {
    const result = [];
    for (let remaining = length - 1; remaining >= 0; remaining -= 1) {
      for (let digit = 1; digit <= 9; digit += 1) {
        const following = consume(state, digit);
        if (needed(following) <= remaining) { result.push(String(digit)); state = following; break; }
      }
    }
    return result.join('');
  }
  const prefixes = [required.slice()];
  let firstZero = num.length;
  for (let index = 0; index < num.length; index += 1) {
    if (num[index] === '0') { firstZero = index; break; }
    prefixes.push(consume(prefixes[prefixes.length - 1], Number(num[index])));
  }
  if (firstZero === num.length && needed(prefixes[prefixes.length - 1]) === 0) return num;
  for (let index = Math.min(firstZero, num.length - 1); index >= 0; index -= 1) {
    const remaining = num.length - index - 1;
    for (let digit = Number(num[index]) + 1; digit <= 9; digit += 1) {
      const state = consume(prefixes[index], digit);
      if (needed(state) <= remaining) return num.slice(0, index) + String(digit) + fill(state, remaining);
    }
  }
  return fill(required, Math.max(num.length + 1, needed(required)));
}

const smallestNumber = solve;
class Solution {
  smallestNumber(num, t) { return solve(num, t); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestNumber };
