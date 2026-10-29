// 327 — Count of Range Sum. Original implementation; authored candidate, not independently qualified.
function solve(nums, lower, upper) {
  const prefix = [0];
  for (const value of nums) prefix.push(prefix[prefix.length - 1] + value);
  const scratch = Array(prefix.length);
  function count(lo, hi) {
    if (hi - lo <= 1) return 0;
    const mid = Math.floor((lo + hi) / 2);
    let answer = count(lo, mid) + count(mid, hi), first = mid, last = mid;
    for (let i = lo; i < mid; i++) {
      while (first < hi && prefix[first] - prefix[i] < lower) first++;
      while (last < hi && prefix[last] - prefix[i] <= upper) last++;
      answer += last - first;
    }
    let i = lo, j = mid;
    for (let k = lo; k < hi; k++) scratch[k] = i < mid && (j === hi || prefix[i] <= prefix[j]) ? prefix[i++] : prefix[j++];
    for (let k = lo; k < hi; k++) prefix[k] = scratch[k];
    return answer;
  }
  return count(0, prefix.length);
}

module.exports = { solve, countRangeSum: solve };
