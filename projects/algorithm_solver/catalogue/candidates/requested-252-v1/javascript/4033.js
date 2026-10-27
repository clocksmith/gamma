/**
 * 4033. Valid K-Unique Subarrays I
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/valid-k-unique-subarrays-i/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4033.Valid%20K-Unique%20Subarrays%20I/README_EN.md
 * Complexity: O(q log q + (n+q) sqrt(n)) time, O(n+q+max(nums)) space.
 * Exact Mo frequency accounting; no probabilistic parity hashes. Maximum-size runtime is not measured. Inputs preserved.
 */

function solve(nums, k, queries) {
  const width = Math.max(1, Math.floor(Math.sqrt(nums.length)));
  const order = queries.map((_, i) => i).sort((a,b) => {
    const x = Math.floor(queries[a][0]/width), y = Math.floor(queries[b][0]/width);
    return x-y || ((x%2===0) ? queries[a][1]-queries[b][1] : queries[b][1]-queries[a][1]);
  });
  let maximum = 0;
  for (const x of nums) maximum = Math.max(maximum,x);
  const frequency = new Int32Array(maximum+1), answer = Array(queries.length);
  let left=0, right=-1, distinct=0, odd=0;
  function change(index,delta) {
    const x=nums[index], old=frequency[x], next=old+delta;
    odd += (next&1)-(old&1);
    distinct += Number(next>0)-Number(old>0);
    frequency[x]=next;
  }
  for (const q of order) {
    const [a,b]=queries[q];
    while(left>a) change(--left,1);
    while(right<b) change(++right,1);
    while(left<a) change(left++,-1);
    while(right>b) change(right--,-1);
    answer[q]=distinct===k && odd===0;
  }
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
