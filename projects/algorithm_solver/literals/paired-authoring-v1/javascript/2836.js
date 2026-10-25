class Solution {
  getMaxFunctionValue(receiver, k) {
    const jumps = [receiver.slice()];
    const sums = [receiver.slice()];
    let block = 2;
    while (block <= k) {
      const previousJumps = jumps[jumps.length - 1];
      const previousSums = sums[sums.length - 1];
      const followingJumps = [];
      const followingSums = [];
      for (let node = 0; node < receiver.length; node += 1) {
        const middle = previousJumps[node];
        followingJumps.push(previousJumps[middle]);
        followingSums.push(previousSums[node] + previousSums[middle]);
      }
      jumps.push(followingJumps);
      sums.push(followingSums);
      block *= 2;
    }
    let best = 0;
    for (let start = 0; start < receiver.length; start += 1) {
      let node = start;
      let total = start;
      let remaining = k;
      let level = 0;
      while (remaining > 0) {
        if (remaining % 2 === 1) {
          total += sums[level][node];
          node = jumps[level][node];
        }
        remaining = Math.floor(remaining / 2);
        level += 1;
      }
      best = Math.max(best, total);
    }
    return best;
  }
}
